import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.domain.translator import Translator

st.title("Text Translation")

# Model selection
model_type = st.selectbox(
    "Select Translation Model",
    ["gemini", "gpt"],
    format_func=lambda x: "Google Gemini gemini-2.0-flash" if x == "gemini" else "OpenAI GPT gpt-3.5-turbo",
    help="Choose the AI model for translation"
)

# Text input
input_text = st.text_area(
    "Enter text to translate",
    height=200
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

if st.button("Translate") and input_text:
    with st.spinner('Translating...'):
        try:
            translator = Translator(model_type=model_type)
            translated_text = translator.translate_batch([input_text], target_lang)[0]
            st.text_area("Translated Text", translated_text, height=200)
        except Exception as e:
            st.error(f"Error during translation: {str(e)}")