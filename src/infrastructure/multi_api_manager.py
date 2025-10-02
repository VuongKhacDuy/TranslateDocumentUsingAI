# Multi-API Configuration for parallel translation
import os
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class APIProvider(Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"

@dataclass
class APIConfig:
    provider: APIProvider
    api_key: str
    base_url: str
    model_name: str
    max_requests_per_minute: int = 10
    is_active: bool = True
    
    def __hash__(self):
        return hash((self.provider, self.api_key, self.base_url, self.model_name))
    
    def __eq__(self, other):
        if not isinstance(other, APIConfig):
            return False
        return (self.provider, self.api_key, self.base_url, self.model_name) == (other.provider, other.api_key, other.base_url, other.model_name)

class MultiAPIManager:
    def __init__(self):
        self.api_configs: List[APIConfig] = []
        self._load_configurations()
        
    def _load_env(self):
        """Load environment variables"""
        from dotenv import load_dotenv
        load_dotenv()
    
    def _load_configurations(self):
        """Load API configurations from environment variables"""
        # Load .env file first
        self._load_env()
        
        # Gemini configurations
        gemini_keys = self._get_multiple_keys("GEMINI_API_KEY")
        for key in gemini_keys:
            if key:
                self.api_configs.append(APIConfig(
                    provider=APIProvider.GEMINI,
                    api_key=key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    model_name="gemini-2.5-flash-preview-05-20",
                    max_requests_per_minute=15,
                    is_active=True
                ))
        
        # OpenAI configurations  
        openai_keys = self._get_multiple_keys("OPENAI_API_KEY")
        for key in openai_keys:
            if key and key != "your_openai_key_here":
                self.api_configs.append(APIConfig(
                    provider=APIProvider.OPENAI,
                    api_key=key,
                    base_url="https://api.openai.com/v1/",
                    model_name="gpt-3.5-turbo",
                    max_requests_per_minute=20,
                    is_active=True
                ))
        
        # Claude configurations (via OpenRouter or direct)
        claude_keys = self._get_multiple_keys("CLAUDE_API_KEY")
        for key in claude_keys:
            if key and key != "your_claude_key_here":
                self.api_configs.append(APIConfig(
                    provider=APIProvider.CLAUDE,
                    api_key=key,
                    base_url="https://api.anthropic.com/v1/",
                    model_name="claude-3-haiku-20240307",
                    max_requests_per_minute=10,
                    is_active=True
                ))
        
        # DeepSeek configurations
        deepseek_keys = self._get_multiple_keys("DEEPSEEK_API_KEY")
        for key in deepseek_keys:
            if key and key != "your_deepseek_key_here":
                self.api_configs.append(APIConfig(
                    provider=APIProvider.DEEPSEEK,
                    api_key=key,
                    base_url="https://api.deepseek.com/v1/",
                    model_name="deepseek-chat",
                    max_requests_per_minute=12,
                    is_active=True
                ))
    
    def _get_multiple_keys(self, base_key: str) -> List[str]:
        """Get multiple API keys with suffixes _1, _2, etc."""
        keys = []
        
        # Check base key first
        base_value = os.getenv(base_key)
        if base_value:
            keys.append(base_value)
        
        # Check numbered variants
        for i in range(1, 6):  # Support up to 5 keys per provider
            key_name = f"{base_key}_{i}"
            key_value = os.getenv(key_name)
            if key_value:
                keys.append(key_value)
        
        return keys
    
    def get_active_apis(self, provider_filter: Optional[APIProvider] = None) -> List[APIConfig]:
        """Get active API configurations, optionally filtered by provider"""
        active_configs = [config for config in self.api_configs if config.is_active]
        
        if provider_filter:
            active_configs = [config for config in active_configs if config.provider == provider_filter]
        
        return active_configs
    
    def get_total_capacity(self, provider_filter: Optional[APIProvider] = None) -> int:
        """Calculate total requests per minute across APIs"""
        return sum(config.max_requests_per_minute for config in self.get_active_apis(provider_filter))
    
    def get_api_count(self, provider_filter: Optional[APIProvider] = None) -> int:
        """Get number of active APIs"""
        return len(self.get_active_apis(provider_filter))
    
    def disable_api(self, provider: APIProvider, api_key: str):
        """Disable a specific API (e.g., if it fails)"""
        for config in self.api_configs:
            if config.provider == provider and config.api_key == api_key:
                config.is_active = False
                break
    
    def get_api_distribution(self, total_pages: int, provider_filter: Optional[APIProvider] = None) -> Dict[APIConfig, int]:
        """Calculate how many pages each API should handle"""
        active_apis = self.get_active_apis(provider_filter)
        if not active_apis:
            return {}
        
        # Calculate distribution based on API capacity
        total_capacity = self.get_total_capacity(provider_filter)
        distribution = {}
        
        remaining_pages = total_pages
        for i, api in enumerate(active_apis):
            if i == len(active_apis) - 1:  # Last API gets remaining pages
                distribution[api] = remaining_pages
            else:
                # Distribute based on capacity ratio
                ratio = api.max_requests_per_minute / total_capacity
                pages_for_api = int(total_pages * ratio)
                distribution[api] = pages_for_api
                remaining_pages -= pages_for_api
        
        return distribution
    
    def get_provider_from_model_type(self, model_type: str) -> Optional[APIProvider]:
        """Map model_type to APIProvider"""
        mapping = {
            "gemini": APIProvider.GEMINI,
            "gpt": APIProvider.OPENAI,
            "openai": APIProvider.OPENAI,
            "claude": APIProvider.CLAUDE,
            "deepseek": APIProvider.DEEPSEEK
        }
        return mapping.get(model_type.lower())