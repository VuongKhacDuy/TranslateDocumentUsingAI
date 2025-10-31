# Dynamic API Configuration Management
import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from src.infrastructure.multi_api_manager import APIProvider, APIConfig

class DynamicAPIManager:
    def __init__(self):
        self.config_file = Path("api_configs.json")
        self.session_apis = "dynamic_apis"
        self._load_saved_configs()
    
    def _load_saved_configs(self):
        """Load saved API configurations from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_configs = json.load(f)
                    # Fix any configuration issues
                    for config in saved_configs:
                        if 'base_url' in config:
                            config['base_url'] = config['base_url'].strip()
                        if 'model_name' in config:
                            config['model_name'] = config['model_name'].strip()
                    if self.session_apis not in st.session_state:
                        st.session_state[self.session_apis] = saved_configs
            except Exception as e:
                st.error(f"Error loading saved configs: {e}")
                if self.session_apis not in st.session_state:
                    st.session_state[self.session_apis] = []
        else:
            if self.session_apis not in st.session_state:
                st.session_state[self.session_apis] = []
    
    def _save_configs(self):
        """Save current API configurations to file"""
        try:
            # Fix any configuration issues before saving
            current_apis = st.session_state.get(self.session_apis, [])
            for config in current_apis:
                if 'base_url' in config:
                    config['base_url'] = config['base_url'].strip()
                if 'model_name' in config:
                    config['model_name'] = config['model_name'].strip()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(current_apis, f, indent=2)
        except Exception as e:
            st.error(f"Error saving configs: {e}")
    
    def render_api_management_ui(self):
        """Render the API management interface"""
        st.subheader("🔑 API Configuration Manager")
        
        # Display current APIs
        current_apis = st.session_state.get(self.session_apis, [])
        
        if current_apis:
            st.write(f"**Currently configured: {len(current_apis)} API(s)**")
            
            # Create columns for better layout
            cols = st.columns([3, 2, 1, 1])
            cols[0].write("**Provider**")
            cols[1].write("**Model**")
            cols[2].write("**Rate Limit**")
            cols[3].write("**Actions**")
            
            # Display each API with edit/delete options
            apis_to_remove = []
            for i, api_config in enumerate(current_apis):
                cols = st.columns([3, 2, 1, 1])
                
                # Provider info
                provider_display = f"{api_config['provider']} (Key: ...{api_config['api_key'][-8:] if len(api_config['api_key']) > 8 else '***'})"
                cols[0].write(provider_display)
                
                # Model info
                cols[1].write(api_config['model_name'])
                
                # Rate limit
                cols[2].write(f"{api_config['max_requests_per_minute']}/min")
                
                # Actions
                if cols[3].button("🗑️", key=f"delete_{i}", help="Delete this API"):
                    apis_to_remove.append(i)
            
            # Remove APIs marked for deletion
            for idx in reversed(apis_to_remove):
                current_apis.pop(idx)
                st.session_state[self.session_apis] = current_apis
                self._save_configs()
                st.rerun()
        
        else:
            st.info("No APIs configured yet. Add your first API below!")
        
        # Add new API form
        with st.expander("➕ Add New API", expanded=len(current_apis) == 0):
            self._render_add_api_form()
        
        # Bulk operations
        if current_apis:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Save All Configs"):
                    self._save_configs()
                    st.success("✅ Configurations saved!")
            
            with col2:
                if st.button("🧪 Test All APIs"):
                    self._test_all_apis()
            
            with col3:
                if st.button("🗑️ Clear All APIs"):
                    if st.checkbox("Confirm deletion of all APIs"):
                        st.session_state[self.session_apis] = []
                        self._save_configs()
                        st.success("All APIs cleared!")
                        st.rerun()
    
    def _render_add_api_form(self):
        """Render form to add new API"""
        with st.form("add_api_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                provider = st.selectbox(
                    "Select Provider",
                    options=["gemini", "openai", "claude", "deepseek"],
                    format_func=lambda x: {
                        "gemini": "🔷 Google Gemini",
                        "openai": "🤖 OpenAI GPT",
                        "claude": "🧠 Anthropic Claude", 
                        "deepseek": "🔍 DeepSeek"
                    }.get(x, str(x))
                )
                
                api_key = st.text_input(
                    "API Key", 
                    type="password",
                    help="Your API key for the selected provider"
                )
            
            with col2:
                # Default configurations based on provider
                default_configs = {
                    "gemini": {
                        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                        "model_name": "gemini-2.5-flash",
                        "max_requests_per_minute": 15
                    },
                    "openai": {
                        "base_url": "https://api.openai.com/v1/",
                        "model_name": "gpt-3.5-turbo",
                        "max_requests_per_minute": 20
                    },
                    "claude": {
                        "base_url": "https://api.anthropic.com/v1/",
                        "model_name": "claude-3-haiku-20240307",
                        "max_requests_per_minute": 10
                    },
                    "deepseek": {
                        "base_url": "https://api.deepseek.com/v1/",
                        "model_name": "deepseek-chat",
                        "max_requests_per_minute": 12
                    }
                }
                
                config = default_configs.get(provider, default_configs["gemini"])
                
                base_url = st.text_input(
                    "Base URL",
                    value=config["base_url"].strip(),  # Strip whitespace/newlines
                    help="API endpoint URL"
                )
                
                model_name = st.text_input(
                    "Model Name",
                    value=config["model_name"].strip(),  # Strip whitespace/newlines
                    help="Model identifier to use"
                )
                
                max_requests = st.number_input(
                    "Rate Limit (requests/minute)",
                    min_value=1,
                    max_value=100,
                    value=config["max_requests_per_minute"],
                    help="Maximum requests per minute for this API"
                )
            
            # Custom name for this API instance
            custom_name = st.text_input(
                "Custom Name (optional)",
                placeholder=f"My {provider.title()} API",
                help="Give this API configuration a custom name"
            )
            
            submitted = st.form_submit_button("➕ Add API")
            
            if submitted:
                if not api_key.strip():
                    st.error("❌ API Key is required!")
                else:
                    self._add_api_config(
                        provider=provider,
                        api_key=api_key.strip(),
                        base_url=base_url.strip() if base_url else config["base_url"].strip(),  # Strip whitespace/newlines
                        model_name=model_name.strip() if model_name else config["model_name"].strip(),  # Strip whitespace/newlines
                        max_requests_per_minute=max_requests,
                        custom_name=custom_name.strip() or f"{provider.title()} API"
                    )
    
    def _add_api_config(self, provider: str, api_key: str, base_url: str, 
                       model_name: str, max_requests_per_minute: int, custom_name: str):
        """Add new API configuration"""
        new_config = {
            "provider": provider,
            "api_key": api_key.strip(),
            "base_url": base_url.strip(),  # Strip whitespace/newlines
            "model_name": model_name.strip(),  # Strip whitespace/newlines
            "max_requests_per_minute": max_requests_per_minute,
            "custom_name": custom_name,
            "is_active": True
        }
        
        # Check for duplicates
        current_apis = st.session_state.get(self.session_apis, [])
        for existing in current_apis:
            if existing["provider"] == provider and existing["api_key"] == api_key:
                st.error("❌ This API key is already configured!")
                return
        
        # Add to session state
        current_apis.append(new_config)
        st.session_state[self.session_apis] = current_apis
        
        # Save to file
        self._save_configs()
        
        st.success(f"✅ Added {custom_name} successfully!")
        st.rerun()
    
    def _test_all_apis(self):
        """Test all configured APIs"""
        current_apis = st.session_state.get(self.session_apis, [])
        
        if not current_apis:
            st.warning("No APIs to test!")
            return
        
        progress_bar = st.progress(0)
        results_container = st.container()
        
        for i, api_config in enumerate(current_apis):
            progress_bar.progress((i + 1) / len(current_apis))
            
            with results_container:
                with st.expander(f"Testing {api_config['custom_name']}..."):
                    success = self._test_single_api(api_config)
                    if success:
                        st.success(f"✅ {api_config['custom_name']} - Connection successful!")
                    else:
                        st.error(f"❌ {api_config['custom_name']} - Connection failed!")
        
        st.success("🎉 API testing completed!")
    
    def _test_single_api(self, api_config: dict) -> bool:
        """Test a single API configuration"""
        try:
            from openai import OpenAI
            import httpx
            
            # Strip whitespace from config values
            api_key = api_config["api_key"].strip()
            base_url = api_config["base_url"].strip()
            model_name = api_config["model_name"].strip()
            
            # Validate config values
            if not api_key:
                st.error("API key is missing or empty")
                return False
            if not base_url:
                st.error("Base URL is missing or empty")
                return False
            if not model_name:
                st.error("Model name is missing or empty")
                return False
            
            st.info(f"Testing with:\n- API Key: ...{api_key[-8:]}\n- Base URL: {base_url}\n- Model: {model_name}")
            
            # Create client with timeout
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=httpx.Timeout(30.0)
            )
            
            # Simple test request
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello, this is a test."}],
                max_tokens=10
            )
            
            result_content = response.choices[0].message.content if response.choices[0].message.content else ""
            st.info(f"Response: {result_content[:100]}{'...' if len(result_content) > 100 else ''}")
            
            return response.choices[0].message.content is not None
            
        except Exception as e:
            st.error(f"Error testing API: {str(e)}")
            return False
    
    def get_dynamic_apis(self, provider_filter: Optional[str] = None) -> List[Dict]:
        """Get current dynamic API configurations"""
        current_apis = st.session_state.get(self.session_apis, [])
        
        if provider_filter:
            current_apis = [api for api in current_apis if api["provider"] == provider_filter and api.get("is_active", True)]
        else:
            current_apis = [api for api in current_apis if api.get("is_active", True)]
        
        return current_apis
    
    def has_apis_for_provider(self, provider: str) -> bool:
        """Check if there are any APIs configured for the given provider"""
        return len(self.get_dynamic_apis(provider)) > 0
    
    def get_active_apis(self, provider_filter=None) -> List[Dict]:
        """Get active API configurations, optionally filtered by provider"""
        current_apis = st.session_state.get(self.session_apis, [])
        
        # Filter by active status
        active_apis = [api for api in current_apis if api.get("is_active", True)]
        
        # Filter by provider if specified
        if provider_filter:
            if hasattr(provider_filter, 'value'):
                provider_name = provider_filter.value
            else:
                provider_name = str(provider_filter)
            active_apis = [api for api in active_apis if api["provider"] == provider_name]
        
        return active_apis
    
    def get_api_distribution(self, provider_filter=None) -> List[APIConfig]:
        """Get API configurations as APIConfig objects for load balancing"""
        active_apis = self.get_active_apis(provider_filter)
        
        api_configs = []
        for api_data in active_apis:
            try:
                # Convert provider string to APIProvider enum
                provider_enum = APIProvider(api_data["provider"])
                
                config = APIConfig(
                    provider=provider_enum,
                    api_key=api_data["api_key"].strip(),
                    base_url=api_data["base_url"].strip(),
                    model_name=api_data["model_name"].strip(),
                    max_requests_per_minute=api_data.get("max_requests_per_minute", 15)
                )
                api_configs.append(config)
            except ValueError as e:
                st.error(f"Invalid provider in config: {api_data['provider']}")
                continue
        
        return api_configs