# Font utilities for PDF generation
import os

def register_unicode_font():
    """Try to register a Unicode-compatible font"""
    try:
        # Import ReportLab only when needed
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return None  # ReportLab not available
    
    # Common system fonts that support Unicode
    font_candidates = [
        # Windows fonts
        ("C:/Windows/Fonts/NotoSansCJK-Regular.ttc", "NotoSansCJK"),
        ("C:/Windows/Fonts/msmincho.ttc", "MSMincho"),
        ("C:/Windows/Fonts/msgothic.ttc", "MSGothic"),
        ("C:/Windows/Fonts/arial.ttf", "Arial"),
        ("C:/Windows/Fonts/calibri.ttf", "Calibri"),
        
        # macOS fonts
        ("/System/Library/Fonts/Arial.ttf", "Arial"),
        ("/System/Library/Fonts/Helvetica.ttc", "Helvetica"),
        
        # Linux fonts
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "Liberation"),
    ]
    
    for font_path, font_name in font_candidates:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                return font_name
            except Exception:
                continue
    
    return None  # No Unicode font available, use default