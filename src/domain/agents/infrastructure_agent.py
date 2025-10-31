"""Infrastructure Agent for specialized infrastructure data analysis"""
import re
from typing import List, Dict

class InfrastructureAgent:
    """Specialized agent for infrastructure data analysis"""
    
    def __init__(self):
        # Infrastructure keywords for identification and analysis
        self.infrastructure_keywords = {
            'infrastructure', 'building', 'construction', 'facility', 'plant', 
            'factory', 'warehouse', 'office', 'headquarters', 'site', 'location',
            'address', 'area', 'space', 'floor', 'room', 'capacity', 'layout',
            'blueprint', 'design', 'architecture', 'structure', 'foundation',
            'roof', 'wall', 'window', 'door', 'elevator', 'stair', 'parking',
            'utilities', 'electricity', 'water', 'gas', 'internet', 'network',
            'security', 'fire', 'safety', 'emergency', 'maintenance', 'upkeep',
            'hạ tầng', 'công trình', 'xây dựng', 'cơ sở', 'nhà máy', 
            'kho hàng', 'văn phòng', 'trụ sở', 'địa điểm', 'khu vực',
            'diện tích', 'không gian', 'tầng', 'phòng', 'sức chứa',
            'thiết kế', 'kiến trúc', 'cấu trúc', 'móng', 'mái', 'tường',
            'cửa sổ', 'cửa', 'thang máy', 'cầu thang', 'đỗ xe',
            'tiện ích', 'điện', 'nước', 'khí gas', 'internet', 'mạng',
            'an ninh', 'cháy', 'an toàn', 'khẩn cấp', 'bảo trì'
        }
        
        # Infrastructure data patterns
        self.infrastructure_patterns = {
            'area': r'(?:\d+(?:[.,]\d+)*\s*(?:m2|sqm|square meters?|diện tích))',
            'floors': r'(?:\d+\s*(?:floors?|tầng))',
            'capacity': r'(?:\d+\s*(?:people|persons?|persons|người))',
            'address': r'(?:\d+[\w\s]+(?:street|avenue|road|đường|phố))'
        }
    
    def is_relevant(self, text: str) -> bool:
        """Check if text contains infrastructure content"""
        text_lower = text.lower()
        infrastructure_matches = sum(1 for keyword in self.infrastructure_keywords if keyword in text_lower)
        return infrastructure_matches >= 2  # At least 2 infrastructure keywords
    
    def extract_infrastructure_data(self, text: str) -> Dict[str, List[str]]:
        """Extract infrastructure data from text"""
        data = {}
        for data_type, pattern in self.infrastructure_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            data[data_type] = matches
        return data
    
    def analyze_infrastructure_document(self, text: str) -> Dict:
        """Analyze infrastructure document and extract key information"""
        analysis = {
            'is_infrastructure': self.is_relevant(text),
            'keywords_found': [],
            'infrastructure_data': {},
            'summary': ''
        }
        
        if not analysis['is_infrastructure']:
            return analysis
        
        # Extract infrastructure keywords found
        text_lower = text.lower()
        analysis['keywords_found'] = [kw for kw in self.infrastructure_keywords if kw in text_lower]
        
        # Extract infrastructure data
        analysis['infrastructure_data'] = self.extract_infrastructure_data(text)
        
        # Generate summary
        key_data = []
        if analysis['infrastructure_data'].get('area'):
            key_data.append(f"{len(analysis['infrastructure_data']['area'])} diện tích")
        if analysis['infrastructure_data'].get('floors'):
            key_data.append(f"{len(analysis['infrastructure_data']['floors'])} tầng")
        if analysis['infrastructure_data'].get('capacity'):
            key_data.append(f"{len(analysis['infrastructure_data']['capacity'])} sức chứa")
        
        analysis['summary'] = f"Tài liệu chứa {len(analysis['keywords_found'])} từ khóa hạ tầng và {', '.join(key_data) if key_data else 'các thông tin hạ tầng khác'}."
        
        return analysis
    
    def answer_infrastructure_question(self, document_text: str, question: str) -> str:
        """Answer infrastructure questions based on document content"""
        try:
            # Analyze the document
            analysis = self.analyze_infrastructure_document(document_text)
            
            if not analysis['is_infrastructure']:
                return "Tài liệu này không chứa thông tin hạ tầng phù hợp."
            
            # Extract relevant sentences
            sentences = re.split(r'[.!?]+', document_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Score sentences based on infrastructure relevance to question
            question_words = set(question.lower().split())
            infrastructure_sentences = []
            
            for sentence in sentences:
                sentence_words = set(sentence.lower().split())
                # Check for infrastructure keywords and question word overlap
                infrastructure_matches = sum(1 for kw in self.infrastructure_keywords if kw in sentence.lower())
                question_overlap = len(question_words.intersection(sentence_words))
                
                if infrastructure_matches > 0 and question_overlap > 0:
                    score = infrastructure_matches * 2 + question_overlap
                    infrastructure_sentences.append((sentence, score))
            
            # Sort by score
            infrastructure_sentences.sort(key=lambda x: x[1], reverse=True)
            
            if not infrastructure_sentences:
                return f"Không tìm thấy thông tin hạ tầng liên quan đến '{question}' trong tài liệu."
            
            # Generate response
            response_parts = [
                "Phân tích hạ tầng:",
                ""
            ]
            
            # Add top relevant sentences
            for i, (sentence, score) in enumerate(infrastructure_sentences[:3], 1):
                response_parts.append(f"{i}. {sentence}")
            
            # Add infrastructure data if available
            if analysis['infrastructure_data']:
                response_parts.append("")
                response_parts.append("Thông tin hạ tầng tìm thấy:")
                for data_type, values in analysis['infrastructure_data'].items():
                    if values:
                        response_parts.append(f"- {data_type.replace('_', ' ').title()}: {', '.join(values[:3])}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"Lỗi khi phân tích tài liệu hạ tầng: {str(e)}"