"""Finance Agent for specialized financial data analysis"""
import re
from collections import Counter
from typing import List, Dict, Tuple

class FinanceAgent:
    """Specialized agent for financial data analysis"""
    
    def __init__(self):
        # Financial keywords for identification and analysis
        self.financial_keywords = {
            'revenue', 'income', 'profit', 'loss', 'expense', 'cost', 'budget', 
            'investment', 'return', 'roi', 'cash', 'assets', 'liabilities', 
            'equity', 'debt', 'loan', 'interest', 'tax', 'dividend', 'shareholder',
            'balance', 'statement', 'ledger', 'accounting', 'audit', 'capital',
            'funding', 'valuation', 'earnings', 'margin', 'revenue', 'turnover',
            'doanh thu', 'lợi nhuận', 'chi phí', 'thu nhập', 'tài sản', 'nợ', 
            'vốn', 'đầu tư', 'lãi suất', 'thuế', 'cổ tức', 'cổ đông'
        }
        
        # Financial metrics patterns
        self.metric_patterns = {
            'currency': r'[\$€£¥₫]\s*\d+(?:[.,]\d+)*|\d+(?:[.,]\d+)*\s*(?:USD|EUR|VND|million|billion)',
            'percentage': r'\d+(?:[.,]\d+)*\s*%',
            'ratio': r'\d+(?:[.,]\d+)*\s*:\s*\d+(?:[.,]\d+)*'
        }
    
    def is_relevant(self, text: str) -> bool:
        """Check if text contains financial content"""
        text_lower = text.lower()
        financial_matches = sum(1 for keyword in self.financial_keywords if keyword in text_lower)
        return financial_matches >= 2  # At least 2 financial keywords
    
    def extract_financial_metrics(self, text: str) -> Dict[str, List[str]]:
        """Extract financial metrics from text"""
        metrics = {}
        for metric_type, pattern in self.metric_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            metrics[metric_type] = matches
        return metrics
    
    def analyze_financial_document(self, text: str) -> Dict:
        """Analyze financial document and extract key information"""
        analysis = {
            'is_financial': self.is_relevant(text),
            'keywords_found': [],
            'metrics': {},
            'summary': ''
        }
        
        if not analysis['is_financial']:
            return analysis
        
        # Extract financial keywords found
        text_lower = text.lower()
        analysis['keywords_found'] = [kw for kw in self.financial_keywords if kw in text_lower]
        
        # Extract metrics
        analysis['metrics'] = self.extract_financial_metrics(text)
        
        # Generate summary
        key_metrics = []
        if analysis['metrics'].get('currency'):
            key_metrics.append(f"{len(analysis['metrics']['currency'])} giá trị tiền tệ")
        if analysis['metrics'].get('percentage'):
            key_metrics.append(f"{len(analysis['metrics']['percentage'])} tỷ lệ phần trăm")
        
        analysis['summary'] = f"Tài liệu chứa {len(analysis['keywords_found'])} từ khóa tài chính và {', '.join(key_metrics) if key_metrics else 'các thông tin tài chính khác'}."
        
        return analysis
    
    def answer_financial_question(self, document_text: str, question: str) -> str:
        """Answer financial questions based on document content"""
        try:
            # Analyze the document
            analysis = self.analyze_financial_document(document_text)
            
            if not analysis['is_financial']:
                return "Tài liệu này không chứa thông tin tài chính phù hợp."
            
            # Extract relevant sentences
            sentences = re.split(r'[.!?]+', document_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Score sentences based on financial relevance to question
            question_words = set(question.lower().split())
            financial_sentences = []
            
            for sentence in sentences:
                sentence_words = set(sentence.lower().split())
                # Check for financial keywords and question word overlap
                financial_matches = sum(1 for kw in self.financial_keywords if kw in sentence.lower())
                question_overlap = len(question_words.intersection(sentence_words))
                
                if financial_matches > 0 and question_overlap > 0:
                    score = financial_matches * 2 + question_overlap
                    financial_sentences.append((sentence, score))
            
            # Sort by score
            financial_sentences.sort(key=lambda x: x[1], reverse=True)
            
            if not financial_sentences:
                return f"Không tìm thấy thông tin tài chính liên quan đến '{question}' trong tài liệu."
            
            # Generate response
            response_parts = [
                "Phân tích tài chính:",
                ""
            ]
            
            # Add top relevant sentences
            for i, (sentence, score) in enumerate(financial_sentences[:3], 1):
                response_parts.append(f"{i}. {sentence}")
            
            # Add metrics if available
            if analysis['metrics']:
                response_parts.append("")
                response_parts.append("Thông tin định lượng tìm thấy:")
                for metric_type, values in analysis['metrics'].items():
                    if values:
                        response_parts.append(f"- {metric_type.title()}: {', '.join(values[:3])}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"Lỗi khi phân tích tài liệu tài chính: {str(e)}"