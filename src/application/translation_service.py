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
            # Extract text from document
            texts = self.file_handler.extract_text(input_path)
            
            # Translate texts
            translated_texts = self.translator.translate_batch(texts, target_lang)
            
            # Create output path
            input_file = Path(input_path)
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"{input_file.stem}-translated{input_file.suffix}"
            
            # Save translated content
            self._save_translated_content(input_path, output_path, translated_texts)
            
            return str(output_path)
            
        except Exception as e:
            print(f"Translation failed: {str(e)}")
            return None

    def _save_translated_content(self, input_path: str, output_path: str, translated_texts: list):
        """Save translated content back to file with original formatting"""
        file_ext = Path(input_path).suffix.lower()
        
        if file_ext in ['.xlsx', '.xls']:
            app = xw.App(visible=False)
            try:
                # First copy the original file to preserve all formatting
                import shutil
                shutil.copy2(input_path, output_path)
                
                # Open the copied file
                wb = app.books.open(output_path)
                try:
                    text_index = 0
                    for sheet in wb.sheets:
                        used_range = sheet.used_range
                        if used_range.count > 1:
                            for cell in used_range:
                                if cell.value and isinstance(cell.value, str):
                                    if text_index < len(translated_texts):
                                        cell.value = translated_texts[text_index]
                                        text_index += 1
                    wb.save()
                finally:
                    wb.close()
            finally:
                app.quit()
        else:
            # For non-Excel files
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(translated_texts))