from pathlib import Path
import xlwings as xw
from ..domain.translator import Translator
from ..infrastructure.file_handler import FileHandler

class TranslationService:
    def __init__(self):
        self.file_handler = FileHandler()
        self.translator = Translator()

    def translate_document(self, input_path: str, target_lang: str) -> str:
        """Translate document content and save to output"""
        try:
            # Extract text and images from document
            texts, image_locations = self.file_handler.extract_text(input_path)
            
            # Translate texts
            translated_texts = self.translator.translate_batch(texts, target_lang)
            
            # Create output path
            input_file = Path(input_path)
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"{input_file.stem}-translated{input_file.suffix}"
            
            # Save translated content with images
            self.file_handler.save_translated_content(  # Removed underscore
                input_path, 
                str(output_path), 
                translated_texts,
                image_locations
            )
            
            return str(output_path)
            
        except Exception as e:
            print(f"Translation failed: {str(e)}")
            return None