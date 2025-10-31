"""HR Agent for specialized human resources data analysis"""
import re
from typing import List, Dict

class HRAgent:
    """Specialized agent for human resources data analysis"""
    
    def __init__(self):
        # HR keywords for identification and analysis
        self.hr_keywords = {
            'employee', 'staff', 'worker', 'team', 'department', 'manager', 
            'supervisor', 'recruitment', 'hiring', 'interview', 'candidate',
            'training', 'development', 'performance', 'appraisal', 'review',
            'benefits', 'salary', 'wage', 'compensation', 'payroll', 'leave',
            'vacation', 'sick', 'health', 'insurance', 'policy', 'contract',
            'promotion', 'career', 'growth', 'resignation', 'termination',
            'nhân viên', 'nhân sự', 'tuyển dụng', 'phỏng vấn', 'ứng viên',
            'đào tạo', 'phát triển', 'hiệu suất', 'lương', 'thưởng', 'bảo hiểm',
            'hợp đồng', 'thăng chức', 'nghỉ phép', 'từ chức'
        }
        
        # HR data patterns
        self.hr_patterns = {
            'employee_count': r'(?:\d+\s*(?:nhân viên|employees?|staff))|(?:staff\s+of\s+\d+)',
            'department': r'(?:phòng\s+ban)|(?:department)|(?:team)',
            'position': r'(?:vị trí)|(?:position)|(?:role)|(?:chức vụ)'
        }
    
    def is_relevant(self, text: str) -> bool:
        """Check if text contains HR content"""
        text_lower = text.lower()
        hr_matches = sum(1 for keyword in self.hr_keywords if keyword in text_lower)
        return hr_matches >= 2  # At least 2 HR keywords
    
    def extract_hr_data(self, text: str) -> Dict[str, List[str]]:
        """Extract HR data from text"""
        data = {}
        for data_type, pattern in self.hr_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            data[data_type] = matches
        return data
    
    def analyze_hr_document(self, text: str) -> Dict:
        """Analyze HR document and extract key information"""
        analysis = {
            'is_hr': self.is_relevant(text),
            'keywords_found': [],
            'hr_data': {},
            'summary': ''
        }
        
        if not analysis['is_hr']:
            return analysis
        
        # Extract HR keywords found
        text_lower = text.lower()
        analysis['keywords_found'] = [kw for kw in self.hr_keywords if kw in text_lower]
        
        # Extract HR data
        analysis['hr_data'] = self.extract_hr_data(text)
        
        # Generate summary
        key_data = []
        if analysis['hr_data'].get('employee_count'):
            key_data.append(f"{len(analysis['hr_data']['employee_count'])} thông tin về nhân sự")
        if analysis['hr_data'].get('department'):
            key_data.append(f"{len(analysis['hr_data']['department'])} phòng ban")
        
        analysis['summary'] = f"Tài liệu chứa {len(analysis['keywords_found'])} từ khóa nhân sự và {', '.join(key_data) if key_data else 'các thông tin nhân sự khác'}."
        
        return analysis
    
    def answer_hr_question(self, document_text: str, question: str) -> str:
        """Answer HR questions based on document content"""
        try:
            # Analyze the document
            analysis = self.analyze_hr_document(document_text)
            
            if not analysis['is_hr']:
                return "Tài liệu này không chứa thông tin nhân sự phù hợp."
            
            # Extract relevant sentences
            sentences = re.split(r'[.!?]+', document_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Score sentences based on HR relevance to question
            question_words = set(question.lower().split())
            hr_sentences = []
            
            for sentence in sentences:
                sentence_words = set(sentence.lower().split())
                # Check for HR keywords and question word overlap
                hr_matches = sum(1 for kw in self.hr_keywords if kw in sentence.lower())
                question_overlap = len(question_words.intersection(sentence_words))
                
                if hr_matches > 0 and question_overlap > 0:
                    score = hr_matches * 2 + question_overlap
                    hr_sentences.append((sentence, score))
            
            # Sort by score
            hr_sentences.sort(key=lambda x: x[1], reverse=True)
            
            if not hr_sentences:
                return f"Không tìm thấy thông tin nhân sự liên quan đến '{question}' trong tài liệu."
            
            # Generate response
            response_parts = [
                "Phân tích nhân sự:",
                ""
            ]
            
            # Add top relevant sentences
            for i, (sentence, score) in enumerate(hr_sentences[:3], 1):
                response_parts.append(f"{i}. {sentence}")
            
            # Add HR data if available
            if analysis['hr_data']:
                response_parts.append("")
                response_parts.append("Thông tin nhân sự tìm thấy:")
                for data_type, values in analysis['hr_data'].items():
                    if values:
                        response_parts.append(f"- {data_type.replace('_', ' ').title()}: {', '.join(values[:3])}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"Lỗi khi phân tích tài liệu nhân sự: {str(e)}"