import os
from pathlib import Path
from src.domain.translator import Translator
from src.infrastructure.file_handler import FileHandler

class TranslationService:
    def __init__(self, model_type="gemini", create_default_translator=True):
        self.file_handler = FileHandler()
        self.model_type = model_type
        
        # Only create default translator if needed (for backward compatibility)
        if create_default_translator:
            try:
                self.translator = Translator(model_type=model_type)
            except Exception as e:
                print(f"⚠️ Could not create default translator: {e}")
                print("💡 Use dynamic API configuration instead")
                self.translator = None
        else:
            self.translator = None

    def translate_document(self, input_path: str, target_lang: str, use_parallel: bool = False, provider_filter: str = None) -> str:
        """Translate document content and save to output"""
        try:
            if use_parallel:
                return self._translate_with_dynamic_apis(input_path, target_lang, provider_filter)
            else:
                # Sequential translation - use dynamic APIs if available, otherwise default translator
                if self.translator is None:
                    # No default translator, use dynamic APIs
                    return self._translate_with_dynamic_apis(input_path, target_lang, provider_filter)
                else:
                    # Original sequential translation with default translator
                    texts = self.file_handler.extract_text(input_path)
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

    def _translate_with_dynamic_apis(self, input_path: str, target_lang: str, provider_filter: str = None) -> str:
        """Translate using dynamic API configurations from Streamlit session"""
        try:
            import streamlit as st
            
            # Get dynamic API manager from session
            if 'api_manager' not in st.session_state:
                raise Exception("No API manager found in session state")
            
            api_manager = st.session_state.api_manager
            active_apis = api_manager.get_active_apis(provider_filter)
            
            if not active_apis:
                raise Exception(f"No active APIs found for provider filter: {provider_filter}")
            
            # Check if this is a multi-page document that benefits from page-level processing
            file_ext = Path(input_path).suffix.lower()
            page_count = self.file_handler.get_page_count(input_path)
            
            # Create output path
            input_file = Path(input_path)
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"{input_file.stem}-translated{input_file.suffix}"
            
            if file_ext == '.pdf' and page_count > 1:
                # Use page-level processing for multi-page PDFs
                pages_texts = self.file_handler.extract_text_by_pages(input_path)
                
                print(f"📄 Processing {len(pages_texts)} pages from PDF...")
                
                # Process each page with available APIs (round-robin for now)
                translated_pages = []
                for page_index, page_texts in enumerate(pages_texts):
                    if not page_texts:  # Skip empty pages
                        translated_pages.append([])
                        continue
                    
                    # Use different APIs in rotation
                    api_config = active_apis[page_index % len(active_apis)]
                    
                    # Create translator for this page
                    translator = Translator(
                        model_type=api_config["provider"],
                        api_key=api_config["api_key"],
                        base_url=api_config.get("base_url"),
                        model_name=api_config.get("model_name")
                    )
                    
                    # Translate this page
                    translated_page = translator.translate_batch(page_texts, target_lang)
                    translated_pages.append(translated_page)
                    
                    print(f"✅ Page {page_index + 1}/{len(pages_texts)} completed with {api_config['custom_name']}")
                
                # Save using page-aware method
                self._save_translated_content_pages(input_path, str(output_path), translated_pages)
                
            else:
                # Use regular processing for single page or non-PDF documents
                api_config = active_apis[0]
                
                # Create a translator with the first API configuration
                translator = Translator(
                    model_type=api_config["provider"],
                    api_key=api_config["api_key"],
                    base_url=api_config.get("base_url"),
                    model_name=api_config.get("model_name")
                )
                
                # Extract text from document
                texts = self.file_handler.extract_text(input_path)
                
                # Translate texts
                translated_texts = translator.translate_batch(texts, target_lang)
                
                # Save translated content
                self._save_translated_content(input_path, str(output_path), translated_texts)
            
            return str(output_path)
            
        except Exception as e:
            print(f"Dynamic API translation failed: {str(e)}")
            # Fallback to default translator
            return self.translate_document(input_path, target_lang, use_parallel=False)

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
    
    def _save_translated_content_pages(self, input_path: str, output_path: str, translated_pages: list):
        """Save translated content organized by pages"""
        file_ext = Path(input_path).suffix.lower()
        
        if file_ext == '.pdf':
            # For PDF files, create new PDF with translated content, preserving page structure
            try:
                # Import ReportLab components only when needed
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib.units import inch
                
                # Try to register Unicode font
                try:
                    from src.infrastructure.font_utils import register_unicode_font
                    unicode_font = register_unicode_font()
                    font_registered = unicode_font is not None
                except:
                    font_registered = False
                
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
                
                # Content organized by pages
                normal_style = styles['Normal']
                if font_registered:
                    normal_style.fontName = unicode_font
                
                for page_index, page_texts in enumerate(translated_pages):
                    if page_index > 0:
                        story.append(PageBreak())  # New page for each original page
                    
                    # Add page header
                    story.append(Paragraph(f"<b>Page {page_index + 1}</b>", title_style))
                    story.append(Spacer(1, 0.1*inch))
                    
                    # Add translated content for this page
                    for text in page_texts:
                        if text and text.strip():
                            # Escape XML characters for reportlab
                            escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            story.append(Paragraph(escaped_text, normal_style))
                            story.append(Spacer(1, 0.1*inch))
                
                # Build PDF
                doc.build(story)
                print(f"📄 Multi-page PDF created: {output_path}")
                
            except Exception as e:
                print(f"⚠️ Failed to create structured PDF: {e}")
                print("📄 Creating simple PDF...")
                
                # Fallback: flatten pages and use simple method
                flattened_texts = []
                for page_texts in translated_pages:
                    flattened_texts.extend(page_texts)
                self._save_translated_content(input_path, output_path, flattened_texts)
        
        else:
            # For other file types, flatten the pages and use regular method
            flattened_texts = []
            for page_texts in translated_pages:
                flattened_texts.extend(page_texts)
            self._save_translated_content(input_path, output_path, flattened_texts)