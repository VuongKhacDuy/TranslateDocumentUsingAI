# Screen OCR + Translate Demo
# Requirements: pip install pyautogui pillow pytesseract opencv-python
# For translation: import your Translator class and API config as needed

import pyautogui
import pytesseract
try:
    import cv2
    assert hasattr(cv2, 'imshow') and hasattr(cv2, 'selectROI') and hasattr(cv2, 'destroyAllWindows') and hasattr(cv2, 'cvtColor')
except (ImportError, AssertionError):
    raise ImportError("Lỗi import OpenCV. Đảm bảo đã cài đúng opencv-contrib-python và không bị xung đột với các gói khác.")
import numpy as np

 # Step 1: Capture screenshot
screenshot = pyautogui.screenshot()
screenshot_np = np.array(screenshot)
screenshot_bgr = cv2.cvtColor(screenshot_np, getattr(cv2, 'COLOR_RGB2BGR', 4))



# Step 2: Select ROI (Region of Interest) - suppress OpenCV messages
import contextlib
class DummyFile(object):
    def write(self, x): pass

with contextlib.redirect_stdout(DummyFile()), contextlib.redirect_stderr(DummyFile()):
    cv2.imshow('Select region', screenshot_bgr)
    roi = cv2.selectROI('Select region', screenshot_bgr, showCrosshair=True)
    cv2.destroyAllWindows()



x, y, w, h = roi
if w == 0 or h == 0:
    print('--- OCR Text ---')
    print('')
    print('--- Translated ---')
    print('')
    exit()

region_img = screenshot.crop((x, y, x + w, y + h))
region_img.save('selected_region.png')

from src.domain.translator import Translator


# Step 3: OCR
text = pytesseract.image_to_string(region_img, lang='eng+jpn+vie')
print('--- OCR Text ---')
print(text if text else '')

# Step 4: Translate (auto)
import os
api_key = os.getenv('GEMINI_API_KEY') or 'YOUR_KEY'
translator = Translator(model_type='gemini', api_key=api_key)
translated = translator.translate_batch([text], 'vi')[0] if text else ''
print('--- Translated ---')
print(translated)
