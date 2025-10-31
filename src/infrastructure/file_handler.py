import os
import tempfile
from pathlib import Path
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document

class FileHandler:
    def __init__(self):
        self.input_dir = Path("input")
        self.output_dir = Path("output")
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def save_uploaded_file(self, uploaded_file):
        """Save uploaded file to input directory"""
        # Ensure input directory exists
        self.input_dir.mkdir(parents=True, exist_ok=True)
        input_path = self.input_dir / uploaded_file.name
        try:
            # Nếu file đã tồn tại, thử xóa trước
            if input_path.exists():
                try:
                    input_path.unlink()
                except Exception as e:
                    raise PermissionError(f"Không thể ghi đè file {input_path}. Hãy đóng file nếu đang mở hoặc kiểm tra quyền ghi. Chi tiết: {e}")
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return str(input_path)
        except Exception as e:
            # Có thể dùng st.error nếu muốn hiển thị trên Streamlit
            import streamlit as st
            st.error(f"Lỗi khi lưu file: {e}")
            raise

    def get_mime_type(self, file_path):
        """Get MIME type based on file extension"""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.csv': 'text/csv'
        }
        return mime_types.get(ext, 'application/octet-stream')

    def extract_text(self, file_path):
        """Extract text from different file types"""
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.xlsx', '.xls']:
            return self._extract_from_excel(file_path)
        elif ext == '.pdf':
            return self._extract_from_pdf(file_path)
        elif ext in ['.doc', '.docx']:
            return self._extract_from_word(file_path)
        elif ext == '.csv':
            return self._extract_from_csv(file_path)
        elif ext == '.txt':
            return self._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def extract_text_by_pages(self, file_path):
        """Extract text grouped by pages/sheets for parallel processing"""
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.xlsx', '.xls']:
            return self._extract_from_excel_by_sheets(file_path)
        elif ext == '.pdf':
            return self._extract_from_pdf_by_pages(file_path)
        elif ext in ['.doc', '.docx']:
            return self._extract_from_word_by_pages(file_path)
        elif ext == '.csv':
            # CSV is single "page"
            return [self._extract_from_csv(file_path)]
        elif ext == '.txt':
            # TXT is single "page"
            return [self._extract_from_txt(file_path)]
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def get_page_count(self, file_path):
        """Get total number of pages/sheets in document"""
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.xlsx', '.xls']:
            return self._get_excel_sheet_count(file_path)
        elif ext == '.pdf':
            return self._get_pdf_page_count(file_path)
        elif ext in ['.doc', '.docx']:
            return self._get_word_page_count(file_path)
        elif ext == '.csv':
            return 1
        elif ext == '.txt':
            return 1
        else:
            return 1

    def _extract_from_excel(self, file_path):
        """Extract text from Excel files"""
        texts = []
        try:
            # Import xlwings only when needed
            import xlwings as xw
            app = xw.App(visible=False)
            try:
                wb = app.books.open(file_path)
                for sheet in wb.sheets:
                    used_range = sheet.used_range
                    if used_range.count > 1:
                        for cell in used_range:
                            if cell.value:
                                texts.append(str(cell.value))
                return texts
            finally:
                app.quit()
        except ImportError:
            print("⚠️ xlwings not available. Using openpyxl as fallback...")
            # Fallback using openpyxl (read-only)
            try:
                from openpyxl import load_workbook
                workbook = load_workbook(file_path, data_only=True)
                for sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]
                    for row in sheet.iter_rows(values_only=True):
                        for cell in row:
                            if cell is not None and str(cell).strip():
                                texts.append(str(cell))
                workbook.close()
                return texts
            except ImportError:
                print("⚠️ openpyxl also not available. Cannot read Excel files.")
                return ["Excel file reading not supported - missing dependencies"]

    def _extract_from_pdf(self, file_path):
        """Extract text from PDF files"""
        texts = []
        with open(file_path, 'rb') as file:
            pdf = PdfReader(file)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text.strip():  # Skip empty pages
                    # Split long pages into paragraphs for better translation
                    paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
                    if paragraphs:
                        texts.extend(paragraphs)
                    else:
                        # If no paragraph breaks, split by single newlines
                        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                        texts.extend(lines)
        return texts

    def _extract_from_word(self, file_path):
        """Extract text from Word documents"""
        doc = Document(file_path)
        return [paragraph.text for paragraph in doc.paragraphs if paragraph.text]

    def _extract_from_csv(self, file_path):
        """Extract text from CSV files"""
        df = pd.read_csv(file_path)
        texts = []
        for column in df.columns:
            texts.extend(df[column].astype(str).tolist())
        return texts
    
    def _extract_from_txt(self, file_path):
        """Extract text from TXT files - optimized for performance"""
        try:
            # Read file in chunks for better memory management
            texts = []
            with open(file_path, 'r', encoding='utf-8', buffering=8192) as file:
                content = file.read()
                
                # For very large files, limit processing
                max_chars = 100000  # Limit to 100KB for performance
                if len(content) > max_chars:
                    content = content[:max_chars]
                    print(f"⚠️ File truncated to {max_chars} characters for performance")
                
                # Split by paragraphs (double newlines) or lines
                if '\n\n' in content:
                    # Split by paragraphs first
                    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                    # Limit number of paragraphs for performance
                    if len(paragraphs) > 1000:
                        paragraphs = paragraphs[:1000]
                        print(f"⚠️ Limited to first 1000 paragraphs for performance")
                    texts.extend(paragraphs)
                else:
                    # Split by lines
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    # Limit number of lines for performance
                    if len(lines) > 2000:
                        lines = lines[:2000]
                        print(f"⚠️ Limited to first 2000 lines for performance")
                    texts.extend(lines)
                    
            return texts
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                texts = []
                with open(file_path, 'r', encoding='utf-8-sig', buffering=8192) as file:
                    content = file.read()
                    
                    # For very large files, limit processing
                    max_chars = 100000  # Limit to 100KB for performance
                    if len(content) > max_chars:
                        content = content[:max_chars]
                        print(f"⚠️ File truncated to {max_chars} characters for performance")
                    
                    # Split by paragraphs (double newlines) or lines
                    if '\n\n' in content:
                        # Split by paragraphs first
                        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                        # Limit number of paragraphs for performance
                        if len(paragraphs) > 1000:
                            paragraphs = paragraphs[:1000]
                            print(f"⚠️ Limited to first 1000 paragraphs for performance")
                        texts.extend(paragraphs)
                    else:
                        # Split by lines
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        # Limit number of lines for performance
                        if len(lines) > 2000:
                            lines = lines[:2000]
                            print(f"⚠️ Limited to first 2000 lines for performance")
                        texts.extend(lines)
                        
                return texts
            except Exception as e:
                print(f"Error reading TXT file: {e}")
                return [f"Error reading TXT file: {e}"]
        except Exception as e:
            print(f"Error reading TXT file: {e}")
            return [f"Error reading TXT file: {e}"]
    
    # Page-level extraction methods
    def _extract_from_pdf_by_pages(self, file_path):
        """Extract text from PDF files, one list per page"""
        pages_texts = []
        with open(file_path, 'rb') as file:
            pdf = PdfReader(file)
            print(f"🔍 DEBUG - PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    # Split page into paragraphs/lines for better translation
                    paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
                    if paragraphs:
                        pages_texts.append(paragraphs)
                        if page_num < 3:  # Debug first 3 pages
                            print(f"🔍 DEBUG - Page {page_num + 1} has {len(paragraphs)} paragraphs:")
                            for i, p in enumerate(paragraphs[:2]):  # Show first 2 paragraphs
                                print(f"    [{i}]: {p[:50]}...")
                    else:
                        # If no paragraph breaks, split by single newlines
                        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                        pages_texts.append(lines)
                        if page_num < 3:
                            print(f"🔍 DEBUG - Page {page_num + 1} has {len(lines)} lines")
                else:
                    pages_texts.append([])  # Empty page
                    print(f"🔍 DEBUG - Page {page_num + 1} is empty")
        return pages_texts
    
    def _extract_from_excel_by_sheets(self, file_path):
        """Extract text from Excel files, one list per sheet"""
        sheets_texts = []
        try:
            import xlwings as xw
            app = xw.App(visible=False)
            try:
                wb = app.books.open(file_path)
                for sheet in wb.sheets:
                    sheet_texts = []
                    used_range = sheet.used_range
                    if used_range and used_range.count > 1:
                        for cell in used_range:
                            if cell.value:
                                sheet_texts.append(str(cell.value))
                    sheets_texts.append(sheet_texts)
            finally:
                app.quit()
        except ImportError:
            # Fallback using openpyxl
            try:
                from openpyxl import load_workbook
                workbook = load_workbook(file_path, data_only=True)
                for sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]
                    sheet_texts = []
                    for row in sheet.iter_rows(values_only=True):
                        for cell in row:
                            if cell is not None and str(cell).strip():
                                sheet_texts.append(str(cell))
                    sheets_texts.append(sheet_texts)
                workbook.close()
            except ImportError:
                sheets_texts = [["Excel file reading not supported - missing dependencies"]]
        return sheets_texts
    
    def _extract_from_word_by_pages(self, file_path):
        """Extract text from Word documents by paragraphs (simulated pages)"""
        doc = Document(file_path)
        paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
        
        # Group paragraphs into "pages" (chunks of ~10 paragraphs each)
        page_size = 10
        pages_texts = []
        for i in range(0, len(paragraphs), page_size):
            page_paragraphs = paragraphs[i:i+page_size]
            pages_texts.append(page_paragraphs)
        
        return pages_texts if pages_texts else [[]]
    
    # Page count methods
    def _get_pdf_page_count(self, file_path):
        """Get number of pages in PDF"""
        with open(file_path, 'rb') as file:
            pdf = PdfReader(file)
            return len(pdf.pages)
    
    def _get_excel_sheet_count(self, file_path):
        """Get number of sheets in Excel file"""
        try:
            import xlwings as xw
            app = xw.App(visible=False)
            try:
                wb = app.books.open(file_path)
                count = len(wb.sheets)
                return count
            finally:
                app.quit()
        except ImportError:
            try:
                from openpyxl import load_workbook
                workbook = load_workbook(file_path, read_only=True)
                count = len(workbook.sheetnames)
                workbook.close()
                return count
            except ImportError:
                return 1
    
    def _get_word_page_count(self, file_path):
        """Get estimated page count for Word documents"""
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        # Estimate ~10 paragraphs per page
        return max(1, (len(paragraphs) + 9) // 10)