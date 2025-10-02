import streamlit as st
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.application.translation_service import TranslationService
from src.infrastructure.file_handler import FileHandler
from src.infrastructure.multi_api_manager import APIProvider

class FileTranslationPage:
    def __init__(self):
        self.file_handler = FileHandler()
    
    def render(self):
        st.header("📄 File Translation")
        
        # Check for configured APIs
        if "api_manager" in st.session_state:
            active_apis = st.session_state.api_manager.get_active_apis()
            if not active_apis:
                st.warning("⚠️ No APIs configured. Please go to API Management to add at least one API.")
                return
        else:
            st.error("API Manager not initialized. Please restart the application.")
            return
        
        # Provider selection for parallel processing
        col1, col2 = st.columns(2)
        
        with col1:
            provider_filter = st.selectbox(
                "Select Provider",
                ["all"] + [provider.value for provider in APIProvider],
                format_func=lambda x: {
                    "all": "All Providers",
                    "gemini": "Google Gemini",
                    "openai": "OpenAI GPT",
                    "claude": "Anthropic Claude",
                    "deepseek": "DeepSeek"
                }.get(x, x),
                help="Choose which AI provider(s) to use for translation"
            )
        
        with col2:
            target_lang = st.selectbox(
                "Select target language",
                ["en", "ja", "vi"],
                format_func=lambda x: {
                    "en": "English",
                    "ja": "Japanese", 
                    "vi": "Vietnamese"
                }.get(x)
            )
        
        # Parallel processing option
        use_parallel = st.checkbox(
            "Enable parallel processing (for multi-page documents)",
            value=True,
            help="Uses multiple APIs simultaneously to speed up translation of large documents"
        )
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a file", 
            type=["xlsx", "xls", "pdf", "doc", "docx", "csv"]
        )
        
        if uploaded_file is not None:
            input_path = self.file_handler.save_uploaded_file(uploaded_file)
            
            if st.button("🚀 Translate", type="primary"):
                self._perform_translation(input_path, target_lang, use_parallel, provider_filter)
    
    def _perform_translation(self, input_path, target_lang, use_parallel, provider_filter):
        """Handle the translation process"""
        with st.spinner("Translating document..."):
            try:
                # Get file extension to determine translation approach
                file_ext = Path(input_path).suffix.lower()
                
                # Initialize translation service without default translator (we'll use dynamic APIs)
                translation_service = TranslationService(create_default_translator=False)
                
                if use_parallel and file_ext == ".pdf":
                    st.info("Using parallel processing for PDF translation...")
                    
                    # Get the API manager from session state
                    api_manager = st.session_state.api_manager
                    
                    # Get APIs based on provider filter
                    if provider_filter == "all":
                        selected_apis = api_manager.get_active_apis()
                        provider_enum = None
                    else:
                        # Convert string to APIProvider enum
                        try:
                            provider_enum = APIProvider(provider_filter)
                            selected_apis = api_manager.get_active_apis(provider_filter=provider_enum)
                        except ValueError:
                            st.error(f"Invalid provider: {provider_filter}")
                            return
                    
                    if selected_apis:
                        provider_name = provider_enum.value if provider_enum else "All providers"
                        st.success(f"Found {len(selected_apis)} active {provider_name} API(s) for parallel processing")
                        
                        output_path = translation_service.translate_document(
                            input_path=input_path,
                            target_lang=target_lang,
                            use_parallel=True,
                            provider_filter=provider_filter if provider_filter != "all" else None
                        )
                    else:
                        st.error("No active APIs found for the selected provider")
                        return
                else:
                    # Use sequential processing
                    if use_parallel:
                        st.info("Sequential processing (parallel processing only available for PDF files)")
                    
                    output_path = translation_service.translate_document(
                        input_path=input_path,
                        target_lang=target_lang,
                        use_parallel=False
                    )
                
                st.success(f"Translation completed! File saved to: {output_path}")
                
                # Show download button
                if os.path.exists(output_path):
                    with open(output_path, "rb") as file:
                        st.download_button(
                            label=f"📥 Download {Path(output_path).name}",
                            data=file.read(),
                            file_name=Path(output_path).name,
                            mime=self.file_handler.get_mime_type(output_path)
                        )
            
            except Exception as e:
                st.error(f"Translation failed: {str(e)}")
                st.exception(e)
