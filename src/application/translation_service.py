import os
from pathlib import Path
from src.domain.translator import Translator
from src.infrastructure.file_handler import FileHandler

class TranslationService:
    def __init__(self, model_type="gemini"):
        self.file_handler = FileHandler()
        self.translator = Translator(model_type=model_type)

    def translate_document(self, input_path: str, target_lang: str) -> str:
        """Translate document content and save to output"""
        try:
            # Extract text from document
            texts = self.file_handler.extract_text(input_path)
            
            # Translate texts
            translated_texts = self.translator.translate_batch(texts, target_lang)
            
            # Create output path - keep original format
            input_file = Path(input_path)
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"{input_file.stem}-translated{input_file.suffix}"
            
            # Save translated content
            self._save_translated_content(input_path, str(output_path), translated_texts)
            
            return str(output_path)
            
        except Exception as e:
            print(f"Translation failed: {str(e)}")
            return None

    def _save_translated_content(self, input_path: str, output_path: str, translated_texts: list):
        """Save translated content back to file with original formatting"""
        file_ext = Path(input_path).suffix.lower()
        
        if file_ext in ['.xlsx', '.xls']:
            try:
                # Import xlwings only when needed
                import xlwings as xw
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
            except ImportError:
                print("⚠️ xlwings not available. Creating CSV instead...")
                # Fallback to CSV if xlwings not available
                import pandas as pd
                csv_output_path = str(Path(output_path).with_suffix('.csv'))
                df = pd.DataFrame({'Translated_Text': translated_texts})
                df.to_csv(csv_output_path, index=False, encoding='utf-8-sig')
                print(f"📊 CSV file created: {csv_output_path}")
                return csv_output_path
        elif file_ext == '.pdf':
            # For PDF files, create new PDF with translated content
            try:
                # Import ReportLab components only when needed
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.pdfgen import canvas
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.units import inch
                
                # Try to register Unicode font
                from src.infrastructure.font_utils import register_unicode_font
                unicode_font = register_unicode_font()
                font_registered = unicode_font is not None
                
                # Create PDF document
                doc = SimpleDocTemplate(output_path, pagesize=A4)
                styles = getSampleStyleSheet()
                story = []
                
                # Title
                title_style = styles['Title']
                if font_registered:
                    title_style.fontName = unicode_font
                story.append(Paragraph("Translated Document", title_style))
                story.append(Spacer(1, 0.2*inch))
                
                # Content
                normal_style = styles['Normal']
                if font_registered:
                    normal_style.fontName = unicode_font
                
                for text in translated_texts:
                    if text and text.strip():
                        # Escape XML characters for reportlab
                        escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        story.append(Paragraph(escaped_text, normal_style))
                        story.append(Spacer(1, 0.1*inch))
                
                doc.build(story)
                print(f"📄 PDF translated and saved: {output_path}")
                
            except ImportError as e:
                print(f"⚠️ ReportLab not available: {e}")
                print("📄 Creating text file instead of PDF...")
                # Fallback to text file if ReportLab not available
                text_output_path = str(Path(output_path).with_suffix('.txt'))
                with open(text_output_path, 'w', encoding='utf-8') as f:
                    f.write("=== TRANSLATED DOCUMENT ===\n\n")
                    for text in translated_texts:
                        if text and text.strip():
                            f.write(text + '\n\n')
                print(f"📄 Text file created: {text_output_path}")
                return text_output_path
                
            except Exception as e:
                print(f"⚠️ Failed to create PDF with Unicode support: {e}")
                print("📄 Creating simple PDF with basic text...")
                
                try:
                    # Import for fallback PDF
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    
                    # Fallback: Create simple PDF
                    c = canvas.Canvas(output_path, pagesize=letter)
                    width, height = letter
                    y_position = height - 50
                    
                    c.setFont("Helvetica", 12)
                    c.drawString(50, height - 30, "Translated Document")
                    
                    for text in translated_texts:
                        if text and text.strip():
                            # Handle long text by wrapping
                            lines = self._wrap_text(text, 80)  # 80 chars per line
                            for line in lines:
                                if y_position < 50:  # New page if needed
                                    c.showPage()
                                    y_position = height - 50
                                    c.setFont("Helvetica", 10)
                                
                                # Try to encode text, skip problematic characters
                                try:
                                    c.drawString(50, y_position, line)
                                except:
                                    # If encoding fails, use ASCII only
                                    ascii_line = line.encode('ascii', 'ignore').decode('ascii')
                                    c.drawString(50, y_position, ascii_line)
                                
                                y_position -= 15
                    
                    c.save()
                    print(f"📄 Simple PDF created: {output_path}")
                    
                except ImportError:
                    # Ultimate fallback to text file
                    print("📄 Creating text file as final fallback...")
                    text_output_path = str(Path(output_path).with_suffix('.txt'))
                    with open(text_output_path, 'w', encoding='utf-8') as f:
                        f.write("=== TRANSLATED DOCUMENT ===\n\n")
                        for text in translated_texts:
                            if text and text.strip():
                                f.write(text + '\n\n')
                    print(f"📄 Text file created: {text_output_path}")
                    return text_output_path
            
        elif file_ext in ['.doc', '.docx']:
            # For Word documents, create new document with translations
            from docx import Document
            doc = Document()
            doc.add_heading('Translated Content', 0)
            
            for text in translated_texts:
                if text.strip():  # Skip empty texts
                    doc.add_paragraph(text)
            
            doc.save(output_path)
            
        elif file_ext == '.csv':
            # For CSV files, save as CSV
            import pandas as pd
            df = pd.DataFrame({'Translated_Text': translated_texts})
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
        else:
            # For other text files
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(translated_texts))

    def _wrap_text(self, text: str, width: int) -> list:
        """Wrap text to specified width"""
        import textwrap
        return textwrap.wrap(text, width=width)