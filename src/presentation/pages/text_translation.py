import streamlit as st
import sys
from pathlib import Path
import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.domain.translator import Translator
from src.infrastructure.multi_api_manager import APIProvider

class TextTranslationPage:
    def __init__(self):
        pass
    
    def render(self):
        st.header("📝 Text Translation")
        # Check for configured APIs
        if "api_manager" in st.session_state:
            active_apis = st.session_state.api_manager.get_active_apis()
            if not active_apis:
                st.warning("⚠️ No APIs configured. Please go to API Management to add at least one API.")
                return
        else:
            st.error("API Manager not initialized. Please restart the application.")
            return
        # Provider selection
        col1, col2 = st.columns(2)
        with col1:
            provider_options = [provider.value for provider in APIProvider]
            def format_provider(x):
                return {
                    "gemini": "Google Gemini",
                    "openai": "OpenAI GPT",
                    "claude": "Anthropic Claude",
                    "deepseek": "DeepSeek"
                }.get(x, str(x))
            provider_filter = st.selectbox(
                "Select Provider",
                provider_options,
                format_func=format_provider,
                help="Choose which AI provider to use for translation"
            )
        with col2:
            def format_language(x):
                return {
                    "en": "English",
                    "ja": "Japanese",
                    "vi": "Vietnamese"
                }.get(x, str(x))
            target_lang = st.selectbox(
                "Select target language",
                ["en", "ja", "vi"],
                format_func=format_language
            )
        # Text input
        if 'ocr_text' not in st.session_state:
            st.session_state['ocr_text'] = ''
        input_text = st.text_area(
            "Enter text to translate",
            value=st.session_state['ocr_text'],
            height=200
        )
        # Nút OCR vùng màn hình
        if st.button("🖼️ OCR vùng màn hình"):
            try:
                ocr_text = self._perform_screen_ocr()
                if ocr_text:
                    st.session_state['ocr_text'] = ocr_text
                    st.success("OCR completed successfully!")
                    st.rerun()
                else:
                    st.warning("No text detected in the selected region.")
            except Exception as e:
                st.error(f"OCR failed: {str(e)}")
                st.info("Make sure you have installed all required dependencies: pip install pyautogui opencv-python")
        
        # Tách đoạn
        segments = [p for p in input_text.split('\n') if p.strip()] if input_text else []
        selected_segments = []
        if segments:
            selected_segments = st.multiselect(
                "Chọn vùng (đoạn) để dịch:",
                segments,
                default=segments,
                help="Chỉ các đoạn được chọn sẽ được dịch"
            )
        if st.button("🚀 Translate", type="primary"):
            if input_text:
                if selected_segments:
                    self._perform_text_translation_segments(selected_segments, target_lang, provider_filter)
                else:
                    st.warning("Vui lòng chọn ít nhất một vùng (đoạn) để dịch.")
            else:
                st.warning("Please enter text to translate")
    
    def _perform_screen_ocr(self):
        """Perform screen OCR and return detected text"""
        try:
            # Step 1: Capture screenshot
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # Step 2: Select ROI (Region of Interest)
            st.info("Please select the region on the screen for OCR. Press ENTER to confirm or ESC to cancel.")
            cv2.imshow('Select region', screenshot_bgr)
            roi = cv2.selectROI('Select region', screenshot_bgr, showCrosshair=True)
            cv2.destroyAllWindows()
            
            # Check if user cancelled selection
            x, y, w, h = roi
            if w == 0 or h == 0:
                return ""
            
            # Step 3: Crop the selected region
            region_img = screenshot.crop((x, y, x + w, y + h))
            
            # Step 4: OCR
            # Try multiple languages for better detection
            text = pytesseract.image_to_string(region_img, lang='eng+jpn+vie')
            return text.strip()
            
        except Exception as e:
            st.error(f"OCR Error: {str(e)}")
            return ""
    
    def _perform_text_translation_segments(self, segments, target_lang, provider_filter):
        """Translate only selected segments"""
        with st.spinner("Translating các vùng đã chọn..."):
            try:
                api_manager = st.session_state.api_manager
                provider_enum = APIProvider(provider_filter)
                selected_apis = api_manager.get_active_apis(provider_filter=provider_enum)
                if not selected_apis:
                    st.error(f"No active APIs found for provider: {provider_filter}")
                    return
                selected_api = selected_apis[0]
                translator = Translator(
                    model_type=selected_api["provider"],
                    api_key=selected_api["api_key"],
                    base_url=selected_api.get("base_url"),
                    model_name=selected_api.get("model_name")
                )
                translated_segments = translator.translate_batch(segments, target_lang)
                translated_text = '\n'.join(translated_segments)
                st.success("Đã dịch các vùng đã chọn!")
                st.text_area("Kết quả dịch:", value=translated_text, height=200, disabled=True)
            except (ValueError, KeyError, TypeError) as e:
                st.error(f"Translation failed: {str(e)}")
                st.exception(e)