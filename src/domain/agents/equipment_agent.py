"""Equipment Agent for specialized equipment and machinery data analysis"""
import re
from typing import List, Dict

class EquipmentAgent:
    """Specialized agent for equipment and machinery data analysis"""
    
    def __init__(self):
        # Equipment keywords for identification and analysis
        self.equipment_keywords = {
            'equipment', 'machine', 'machinery', 'device', 'tool', 'instrument',
            'vehicle', 'engine', 'motor', 'generator', 'pump', 'compressor',
            'boiler', 'furnace', 'oven', 'printer', 'computer', 'server',
            'maintenance', 'repair', 'calibration', 'inspection', 'warranty',
            'specification', 'capacity', 'power', 'voltage', 'frequency',
            'serial', 'model', 'brand', 'manufacturer', 'production', 'output',
            'thiết bị', 'máy móc', 'công cụ', 'dụng cụ', 'xe', 'động cơ', 
            'máy phát', 'máy bơm', 'máy nén', 'lò', 'tủ', 'máy in', 
            'máy tính', 'máy chủ', 'bảo trì', 'sửa chữa', 'hiệu chuẩn',
            'kiểm tra', 'bảo hành', 'thông số', 'công suất', 'điện áp'
        }
        
        # Equipment data patterns
        self.equipment_patterns = {
            'serial_number': r'(?:serial\s*(?:number)?|s/n)[:\s]*([A-Z0-9\-]+)',
            'model_number': r'(?:model\s*(?:number)?|m/n)[:\s]*([A-Z0-9\-]+)',
            'specifications': r'(?:\d+(?:[.,]\d+)*\s*(?:kw|w|hp|kw|hertz|hz|v|a|kg|tons?|liters?|l))',
            'manufacturer': r'(?:made\s+by|manufactured\s+by|by)[:\s]*([A-Z][a-zA-Z\s]+(?:Co|Inc|Ltd|Corporation))'
        }
    
    def is_relevant(self, text: str) -> bool:
        """Check if text contains equipment content"""
        text_lower = text.lower()
        equipment_matches = sum(1 for keyword in self.equipment_keywords if keyword in text_lower)
        return equipment_matches >= 2  # At least 2 equipment keywords
    
    def extract_equipment_data(self, text: str) -> Dict[str, List[str]]:
        """Extract equipment data from text"""
        data = {}
        for data_type, pattern in self.equipment_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            data[data_type] = matches
        return data
    
    def analyze_equipment_document(self, text: str) -> Dict:
        """Analyze equipment document and extract key information"""
        analysis = {
            'is_equipment': self.is_relevant(text),
            'keywords_found': [],
            'equipment_data': {},
            'summary': ''
        }
        
        if not analysis['is_equipment']:
            return analysis
        
        # Extract equipment keywords found
        text_lower = text.lower()
        analysis['keywords_found'] = [kw for kw in self.equipment_keywords if kw in text_lower]
        
        # Extract equipment data
        analysis['equipment_data'] = self.extract_equipment_data(text)
        
        # Generate summary
        key_data = []
        if analysis['equipment_data'].get('serial_number'):
            key_data.append(f"{len(analysis['equipment_data']['serial_number'])} số serial")
        if analysis['equipment_data'].get('model_number'):
            key_data.append(f"{len(analysis['equipment_data']['model_number'])} mã model")
        if analysis['equipment_data'].get('specifications'):
            key_data.append(f"{len(analysis['equipment_data']['specifications'])} thông số kỹ thuật")
        
        analysis['summary'] = f"Tài liệu chứa {len(analysis['keywords_found'])} từ khóa thiết bị và {', '.join(key_data) if key_data else 'các thông tin thiết bị khác'}."
        
        return analysis
    
    def answer_equipment_question(self, document_text: str, question: str) -> str:
        """Answer equipment questions based on document content"""
        try:
            # Analyze the document
            analysis = self.analyze_equipment_document(document_text)
            
            if not analysis['is_equipment']:
                return "Tài liệu này không chứa thông tin thiết bị phù hợp."
            
            # Extract relevant sentences
            sentences = re.split(r'[.!?]+', document_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Score sentences based on equipment relevance to question
            question_words = set(question.lower().split())
            equipment_sentences = []
            
            for sentence in sentences:
                sentence_words = set(sentence.lower().split())
                # Check for equipment keywords and question word overlap
                equipment_matches = sum(1 for kw in self.equipment_keywords if kw in sentence.lower())
                question_overlap = len(question_words.intersection(sentence_words))
                
                if equipment_matches > 0 and question_overlap > 0:
                    score = equipment_matches * 2 + question_overlap
                    equipment_sentences.append((sentence, score))
            
            # Sort by score
            equipment_sentences.sort(key=lambda x: x[1], reverse=True)
            
            if not equipment_sentences:
                return f"Không tìm thấy thông tin thiết bị liên quan đến '{question}' trong tài liệu."
            
            # Generate response
            response_parts = [
                "Phân tích thiết bị:",
                ""
            ]
            
            # Add top relevant sentences
            for i, (sentence, score) in enumerate(equipment_sentences[:3], 1):
                response_parts.append(f"{i}. {sentence}")
            
            # Add equipment data if available
            if analysis['equipment_data']:
                response_parts.append("")
                response_parts.append("Thông tin thiết bị tìm thấy:")
                for data_type, values in analysis['equipment_data'].items():
                    if values:
                        response_parts.append(f"- {data_type.replace('_', ' ').title()}: {', '.join(values[:3])}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"Lỗi khi phân tích tài liệu thiết bị: {str(e)}"