import sys
import os
import importlib.util
import streamlit as st
from pathlib import Path
import warnings
import asyncio
import signal
import threading

# More robust way to determine project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def import_module_from_path(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not load spec for module {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise ImportError(f"Could not load loader for module {module_name} from {module_path}")
    loader.exec_module(module)
    return module

# Import required modules with proper error handling
try:
    TranslationService = import_module_from_path(
        "translation_service",
        os.path.join(project_root, "src", "application", "translation_service.py")
    ).TranslationService
except FileNotFoundError as e:
    print(f"Error importing translation_service: {e}")
    print(f"project_root: {project_root}")
    print(f"Files in src/application/: {os.listdir(os.path.join(project_root, 'src', 'application')) if os.path.exists(os.path.join(project_root, 'src', 'application')) else 'Directory not found'}")
    raise
except Exception as e:
    print(f"Error importing translation_service: {e}")
    raise

try:
    FileHandler = import_module_from_path(
        "file_handler",
        os.path.join(project_root, "src", "infrastructure", "file_handler.py")
    ).FileHandler
except FileNotFoundError as e:
    print(f"Error importing file_handler: {e}")
    raise
except Exception as e:
    print(f"Error importing file_handler: {e}")
    raise

try:
    FileTranslationPage = import_module_from_path(
        "file_translation",
        os.path.join(project_root, "src", "presentation", "pages", "file_translation.py")
    ).FileTranslationPage
except FileNotFoundError as e:
    print(f"Error importing file_translation: {e}")
    raise
except Exception as e:
    print(f"Error importing file_translation: {e}")
    raise

try:
    TextTranslationPage = import_module_from_path(
        "text_translation",
        os.path.join(project_root, "src", "presentation", "pages", "text_translation.py")
    ).TextTranslationPage
except FileNotFoundError as e:
    print(f"Error importing text_translation: {e}")
    raise
except Exception as e:
    print(f"Error importing text_translation: {e}")
    raise

# Import DynamicAPIManager
try:
    DynamicAPIManager = import_module_from_path(
        "api_management",
        os.path.join(project_root, "src", "presentation", "pages", "api_management.py")
    ).DynamicAPIManager
except FileNotFoundError as e:
    print(f"Error importing api_management: {e}")
    raise
except Exception as e:
    print(f"Error importing api_management: {e}")
    raise

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