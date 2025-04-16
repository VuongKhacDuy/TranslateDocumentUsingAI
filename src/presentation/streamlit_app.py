import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.application.translation_service import TranslationService
from src.infrastructure.file_handler import FileHandler

def init_session_state():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "File Translation"
def main():
    init_session_state()
if __name__ == "__main__":
    main()