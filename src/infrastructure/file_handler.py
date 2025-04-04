import os
import tempfile
from pathlib import Path
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
import xlwings as xw

class FileHandler:
    def __init__(self):
        self.input_dir = Path("input")
        self.output_dir = Path("output")
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def save_uploaded_file(self, uploaded_file):
        """Save uploaded file to input directory"""
        input_path = self.input_dir / uploaded_file.name
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(input_path)

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
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _extract_from_excel(self, file_path):
        """Extract text from Excel files"""
        texts = []
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

    def _extract_from_pdf(self, file_path):
        """Extract text from PDF files"""
        texts = []
        with open(file_path, 'rb') as file:
            pdf = PdfReader(file)
            for page in pdf.pages:
                texts.append(page.extract_text())
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