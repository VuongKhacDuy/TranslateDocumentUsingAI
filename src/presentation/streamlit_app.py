import streamlit as st
import os
import sys
from pathlib import Path
import warnings
import asyncio
import signal
import threading

from src.application.translation_service import TranslationService
from src.infrastructure.file_handler import FileHandler
from src.presentation.pages.file_translation import FileTranslationPage
from src.presentation.pages.text_translation import TextTranslationPage
from src.presentation.pages.api_management import DynamicAPIManager

# Ignore RuntimeWarnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))



def handle_shutdown(signal, frame):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.stop()
        loop.close()
    except Exception:
        pass

def init_session_state():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "File Translation"
    if 'api_manager' not in st.session_state:
        st.session_state.api_manager = DynamicAPIManager()

def main():
    # Only set signal handler if running in main thread (avoid Streamlit error)
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, handle_shutdown)
    
    init_session_state()
    
    # Set page config
    st.set_page_config(
        page_title="Multi-Modal Document Translator",
        page_icon="🌐",
        layout="wide"
    )
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    pages = ["File Translation", "Text Translation", "API Management"]
    selected_page = st.sidebar.selectbox("Select Page", pages, index=pages.index(st.session_state.current_page))
    
    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()
    
    # Main content area
    st.title("🌐 Multi-Modal Document Translator")
    
    if st.session_state.current_page == "File Translation":
        file_page = FileTranslationPage()
        file_page.render()
    elif st.session_state.current_page == "Text Translation":
        text_page = TextTranslationPage()
        text_page.render()
    elif st.session_state.current_page == "API Management":
        st.session_state.api_manager.render_api_management_ui()

if __name__ == "__main__":
    main()