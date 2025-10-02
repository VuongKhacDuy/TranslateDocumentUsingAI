# Parallel Translation Engine for multi-API processing
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Callable
from queue import Queue
import logging

from src.infrastructure.multi_api_manager import MultiAPIManager, APIConfig
from src.domain.translator import Translator

@dataclass
class PageTask:
    page_index: int
    page_texts: List[str]
    target_lang: str
    
@dataclass
class TranslationResult:
    page_index: int
    translated_texts: List[str]
    api_used: str
    success: bool
    error_message: Optional[str] = None

class ParallelTranslationEngine:
    def __init__(self, model_type: str = "gemini", progress_callback: Optional[Callable] = None):
        self.api_manager = MultiAPIManager()
        self.model_type = model_type
        self.provider_filter = self.api_manager.get_provider_from_model_type(model_type)
        self.translators: Dict[str, Translator] = {}
        self.progress_callback = progress_callback
        self.total_tasks = 0
        self.completed_tasks = 0
        self._init_translators()
    
    def _init_translators(self):
        """Initialize translator instances for each API of the selected provider"""
        # Only use APIs from the selected provider
        filtered_apis = self.api_manager.get_active_apis(self.provider_filter)
        
        if self.progress_callback and self.provider_filter:
            self.progress_callback(f"🔧 Using {self.provider_filter.value} APIs only ({len(filtered_apis)} found)")
        
        for api_config in filtered_apis:
            # Create a unique identifier for each API instance
            api_id = f"{api_config.provider.value}_{api_config.api_key[:8]}"
            
            # Create translator with specific API config
            translator = Translator()
            translator.client = self._create_client(api_config)
            translator.model_name = api_config.model_name
            translator.api_delay = 60 / api_config.max_requests_per_minute  # Convert RPM to delay
            
            self.translators[api_id] = translator
    
    def _create_client(self, api_config: APIConfig):
        """Create OpenAI-compatible client for different providers"""
        from openai import OpenAI
        
        if api_config.provider.name == "CLAUDE":
            # For Claude, you might need a different client or wrapper
            # This is a simplified example
            return OpenAI(
                api_key=api_config.api_key,
                base_url=api_config.base_url
            )
        else:
            return OpenAI(
                api_key=api_config.api_key,
                base_url=api_config.base_url
            )
    
    def calculate_optimal_threading(self, total_pages: int) -> Tuple[int, Dict[str, int]]:
        """Calculate optimal number of threads and distribution"""
        active_apis = self.api_manager.get_active_apis(self.provider_filter)
        if not active_apis:
            return 1, {}
        
        # Maximum threads = number of APIs (one thread per API)
        max_threads = len(active_apis)
        
        # If we have fewer pages than APIs, use fewer threads
        optimal_threads = min(total_pages, max_threads)
        
        # Calculate page distribution across APIs
        api_distribution = self.api_manager.get_api_distribution(total_pages, self.provider_filter)
        
        return optimal_threads, api_distribution
    
    def translate_pages_parallel(self, pages_texts: List[List[str]], target_lang: str) -> List[List[str]]:
        """Translate multiple pages in parallel using multiple APIs"""
        if not pages_texts:
            return []
        
        self.total_tasks = len(pages_texts)
        self.completed_tasks = 0
        
        # Calculate optimal threading strategy
        num_threads, api_distribution = self.calculate_optimal_threading(len(pages_texts))
        
        if self.progress_callback:
            self.progress_callback(f"Starting parallel translation with {num_threads} threads across {len(self.translators)} APIs")
        
        # Create page tasks
        tasks = [
            PageTask(i, page_texts, target_lang) 
            for i, page_texts in enumerate(pages_texts)
        ]
        
        # Distribute tasks across available APIs
        task_queues = self._distribute_tasks(tasks, api_distribution)
        
        # Execute parallel translation
        results = self._execute_parallel_translation(task_queues, num_threads)
        
        # Sort results by page index to maintain order
        results.sort(key=lambda x: x.page_index)
        
        # Extract translated texts, handle failures
        translated_pages = []
        for result in results:
            if result.success:
                translated_pages.append(result.translated_texts)
            else:
                # Return original texts if translation failed
                original_page = pages_texts[result.page_index]
                translated_pages.append(original_page)
                if self.progress_callback:
                    self.progress_callback(f"⚠️ Page {result.page_index + 1} translation failed: {result.error_message}")
        
        return translated_pages
    
    def _distribute_tasks(self, tasks: List[PageTask], api_distribution: Dict[APIConfig, int]) -> Dict[str, Queue]:
        """Distribute tasks across API queues based on capacity"""
        task_queues = {}
        
        # Initialize queues for each translator
        for api_id in self.translators.keys():
            task_queues[api_id] = Queue()
        
        # Distribute tasks based on API distribution
        task_index = 0
        for api_config, page_count in api_distribution.items():
            api_id = f"{api_config.provider.value}_{api_config.api_key[:8]}"
            
            # Add tasks to this API's queue
            for _ in range(page_count):
                if task_index < len(tasks):
                    task_queues[api_id].put(tasks[task_index])
                    task_index += 1
        
        # Distribute any remaining tasks round-robin
        api_ids = list(self.translators.keys())
        api_idx = 0
        while task_index < len(tasks):
            api_id = api_ids[api_idx % len(api_ids)]
            task_queues[api_id].put(tasks[task_index])
            task_index += 1
            api_idx += 1
        
        return task_queues
    
    def _execute_parallel_translation(self, task_queues: Dict[str, Queue], num_threads: int) -> List[TranslationResult]:
        """Execute translation tasks in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit worker tasks
            future_to_api = {}
            
            for api_id, task_queue in task_queues.items():
                if not task_queue.empty():
                    future = executor.submit(self._worker_thread, api_id, task_queue)
                    future_to_api[future] = api_id
            
            # Collect results as they complete
            for future in as_completed(future_to_api):
                api_id = future_to_api[future]
                try:
                    worker_results = future.result()
                    results.extend(worker_results)
                except Exception as e:
                    if self.progress_callback:
                        self.progress_callback(f"❌ Worker thread for {api_id} failed: {str(e)}")
        
        return results
    
    def _worker_thread(self, api_id: str, task_queue: Queue) -> List[TranslationResult]:
        """Worker thread that processes tasks from queue using specific API"""
        results = []
        translator = self.translators[api_id]
        
        while not task_queue.empty():
            try:
                task = task_queue.get_nowait()
                
                if self.progress_callback:
                    self.progress_callback(f"🔄 Translating page {task.page_index + 1} with {api_id}")
                
                # Translate page texts
                try:
                    translated_texts = translator.translate_batch(task.page_texts, task.target_lang)
                    
                    result = TranslationResult(
                        page_index=task.page_index,
                        translated_texts=translated_texts,
                        api_used=api_id,
                        success=True
                    )
                    
                    self.completed_tasks += 1
                    
                    if self.progress_callback:
                        progress = (self.completed_tasks / self.total_tasks) * 100
                        self.progress_callback(f"✅ Page {task.page_index + 1} completed ({progress:.1f}%)")
                
                except Exception as e:
                    result = TranslationResult(
                        page_index=task.page_index,
                        translated_texts=[],
                        api_used=api_id,
                        success=False,
                        error_message=str(e)
                    )
                    
                    # Disable this API if it's consistently failing
                    provider = api_id.split('_')[0]
                    api_key = api_id.split('_')[1]
                    # Note: We could implement failure tracking here
                
                results.append(result)
                
            except Exception as e:
                # Queue empty or other error
                break
        
        return results
    
    def get_status_summary(self) -> Dict:
        """Get current status summary"""
        return {
            "total_apis": len(self.translators),
            "active_apis": len([t for t in self.translators.values()]),
            "total_capacity": self.api_manager.get_total_capacity(),
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "progress_percent": (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0
        }