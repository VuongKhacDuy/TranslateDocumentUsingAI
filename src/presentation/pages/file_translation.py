import streamlit as st
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.application.translation_service import TranslationService
from src.infrastructure.file_handler import FileHandler

st.title("File Translation")

# Model selection
model_type = st.selectbox(
    "Select Translation Model",
    ["gemini", "gpt"],
    format_func=lambda x: "Google Gemini gemini-2.0-flash" if x == "gemini" else "OpenAI GPT gpt-3.5-turbo",
    help="Choose the AI model for translation"
)

uploaded_file = st.file_uploader(
    "Choose a file", 
    type=['xlsx', 'xls', 'pdf', 'doc', 'docx', 'csv']
)

# Language selection
target_lang = st.selectbox(
    "Select target language",
    ["en", "ja", "vi"],
    format_func=lambda x: {
        "en": "English",
        "ja": "Japanese",
        "vi": "Vietnamese"
    }.get(x)
)

if uploaded_file is not None:
    file_handler = FileHandler()
    input_path = file_handler.save_uploaded_file(uploaded_file)
    
    if st.button("Translate"):
        with st.spinner('Translating...'):
            try:
                translation_service = TranslationService(model_type=model_type)  # Pass model type
                output_path = translation_service.translate_document(
                    input_path=input_path,
                    target_lang=target_lang
                )
                
                if output_path:
                    with open(output_path, "rb") as file:
                        st.download_button(
                            label="Download translated file",
                            data=file,
                            file_name=os.path.basename(output_path),
                            mime=file_handler.get_mime_type(output_path)
                        )
                    st.success("✅ Translation completed successfully!")
                else:
                    st.error("Translation failed!")
                    
            except Exception as e:
                st.error(f"Error during translation: {str(e)}")