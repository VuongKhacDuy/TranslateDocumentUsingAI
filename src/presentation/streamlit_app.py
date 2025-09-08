import streamlit as st
import os
import sys
from pathlib import Path
import warnings
import asyncio
import signal
import threading

# Ignore RuntimeWarnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.application.translation_service import TranslationService
from src.infrastructure.file_handler import FileHandler

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

def main():
    # Only set signal handler if running in main thread (avoid Streamlit error)
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, handle_shutdown)
    
    init_session_state()

if __name__ == "__main__":
    main()