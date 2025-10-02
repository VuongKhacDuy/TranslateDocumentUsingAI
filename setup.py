# Editable install setup
# Run: pip install -e .

from setuptools import setup, find_packages

setup(
    name="translate-document",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "xlwings", 
        "PyPDF2",
        "python-docx",
        "pandas",
        "openai",
        "python-dotenv",
        "reportlab"
    ],
    python_requires=">=3.7",
)