# Screen OCR + Translate Demo
# Requirements: pip install pyautogui pillow pytesseract opencv-python
# For translation: import your Translator class and API config as needed

import pyautogui
from PIL import Image
import pytesseract
import cv2
import numpy as np

# Step 1: Capture screenshot
screenshot = pyautogui.screenshot()
screenshot_np = np.array(screenshot)
screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

# Step 2: Select ROI (Region of Interest)
cv2.imshow('Select region and press ENTER', screenshot_bgr)
roi = cv2.selectROI('Select region and press ENTER', screenshot_bgr, showCrosshair=True)
cv2.destroyAllWindows()

x, y, w, h = roi
if w == 0 or h == 0:
    print('No region selected.')
    exit()

region_img = screenshot.crop((x, y, x + w, y + h))
region_img.save('selected_region.png')

from src.domain.translator import Translator
import os

# Step 3: OCR
text = pytesseract.image_to_string(region_img, lang='eng+jpn+vie')
print('--- OCR Text ---')
print(text)

# Step 4: Translate (auto)
# Lấy thông tin API từ biến môi trường hoặc cấu hình
api_key = os.getenv('GEMINI_API_KEY') or 'YOUR_KEY'
translator = Translator(model_type='gemini', api_key=api_key)
translated = translator.translate_batch([text], 'vi')[0]
print('--- Translated ---')
print(translated)
