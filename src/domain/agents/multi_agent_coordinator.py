"""Multi-Agent Coordinator for routing questions to specialized agents"""
from typing import Dict, List, Tuple, Optional
from src.domain.agents.finance_agent import FinanceAgent
from src.domain.agents.hr_agent import HRAgent
from src.domain.agents.equipment_agent import EquipmentAgent
from src.domain.agents.infrastructure_agent import InfrastructureAgent

class MultiAgentCoordinator:
    """Coordinates multiple specialized agents for domain-specific question answering"""
    
    def __init__(self):
        # Initialize all specialized agents
        self.agents = {
            'finance': FinanceAgent(),
            'hr': HRAgent(),
            'equipment': EquipmentAgent(),
            'infrastructure': InfrastructureAgent()
        }
        
        # Domain keywords for initial routing
        self.domain_keywords = {
            'finance': {
                'revenue', 'profit', 'loss', 'expense', 'budget', 'investment', 
                'cash', 'assets', 'liabilities', 'equity', 'debt', 'loan', 
                'interest', 'tax', 'dividend', 'doanh thu', 'lợi nhuận', 
                'chi phí', 'thu nhập', 'tài sản', 'nợ', 'vốn', 'đầu tư', 
                'lãi suất', 'thuế', 'cổ tức', 'financial', 'income', 'earnings'
            },
            'hr': {
                'employee', 'staff', 'worker', 'team', 'department', 'manager', 
                'recruitment', 'hiring', 'interview', 'candidate', 'training', 
                'salary', 'benefits', 'leave', 'promotion', 'career', 
                'nhân viên', 'nhân sự', 'tuyển dụng', 'phỏng vấn', 'ứng viên', 
                'đào tạo', 'lương', 'thưởng', 'bảo hiểm', 'nghỉ phép', 
                'thăng chức', 'phát triển', 'human resources', 'personnel'
            },
            'equipment': {
                'equipment', 'machine', 'device', 'tool', 'instrument', 
                'vehicle', 'engine', 'motor', 'generator', 'pump', 'maintenance', 
                'repair', 'specification', 'thiết bị', 'máy móc', 'công cụ', 
                'dụng cụ', 'xe', 'động cơ', 'bảo trì', 'sửa chữa', 'thông số',
                'machinery', 'tools', 'devices'
            },
            'infrastructure': {
                'infrastructure', 'building', 'construction', 'facility', 'plant', 
                'factory', 'warehouse', 'office', 'area', 'space', 'floor', 
                'capacity', 'design', 'structure', 'hạ tầng', 'công trình', 
                'xây dựng', 'cơ sở', 'nhà máy', 'kho hàng', 'vản phòng', 
                'diện tích', 'không gian', 'tầng', 'sức chứa', 'thiết kế', 'cấu trúc',
                'facilities', 'buildings', 'plants'
            }
        }
    
    def identify_domains(self, question: str, document_text: str) -> List[str]:
        """Identify relevant domains for a question based on keywords"""
        relevant_domains = []
        question_lower = question.lower()
        document_lower = document_text.lower()
        
        # Check question for domain keywords
        for domain, keywords in self.domain_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in question_lower)
            # Also check document for domain relevance
            doc_matches = sum(1 for keyword in keywords if keyword in document_lower)
            
            # If question has strong domain indicators or both have moderate indicators
            if matches >= 2 or (matches >= 1 and doc_matches >= 3):
                relevant_domains.append(domain)
        
        # If no specific domains identified, try to identify from question context
        if not relevant_domains:
            # Check for general keywords that might indicate domain
            for domain, keywords in self.domain_keywords.items():
                for keyword in keywords:
                    if keyword in question_lower:
                        relevant_domains.append(domain)
                        break  # Only add domain once
        
        # If still no domains identified, return empty list (will use all agents)
        return relevant_domains
    
    def route_question(self, question: str, document_text: str) -> Dict[str, str]:
        """Route question to appropriate agents and collect responses"""
        # Identify relevant domains
        relevant_domains = self.identify_domains(question, document_text)
        
        # If no specific domains identified, analyze document to find relevant ones
        if not relevant_domains:
            # Check document content for domain indicators
            document_lower = document_text.lower()
            domain_scores = {}
            
            for domain, keywords in self.domain_keywords.items():
                score = sum(1 for keyword in keywords if keyword in document_lower)
                if score >= 2:  # At least 2 keywords to be considered relevant
                    domain_scores[domain] = score
            
            # Sort by score and take top 2 domains
            sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
            relevant_domains = [domain for domain, score in sorted_domains[:2]]
        
        # If still no domains, return empty dict
        if not relevant_domains:
            return {}
        
        # Collect responses from relevant agents
        responses = {}
        
        for domain in relevant_domains:
            if domain in self.agents:
                agent = self.agents[domain]
                try:
                    # Call the appropriate method for each agent
                    if domain == 'finance':
                        response = agent.answer_financial_question(document_text, question)
                    elif domain == 'hr':
                        response = agent.answer_hr_question(document_text, question)
                    elif domain == 'equipment':
                        response = agent.answer_equipment_question(document_text, question)
                    elif domain == 'infrastructure':
                        response = agent.answer_infrastructure_question(document_text, question)
                    else:
                        response = f"Không có agent phù hợp cho lĩnh vực {domain}"
                    
                    # Only include response if it's relevant (contains actual information)
                    if not response.startswith("Tài liệu này không chứa") and not response.startswith("Không tìm thấy thông tin"):
                        responses[domain] = response
                except Exception as e:
                    responses[domain] = f"Lỗi khi xử lý câu hỏi cho lĩnh vực {domain}: {str(e)}"
        
        return responses
    
    def synthesize_response(self, question: str, responses: Dict[str, str]) -> str:
        """Synthesize responses from multiple agents into a coherent answer"""
        if not responses:
            return "Không tìm thấy thông tin phù hợp trong tài liệu để trả lời câu hỏi."
        
        # If only one domain has a response, return it directly
        if len(responses) == 1:
            return list(responses.values())[0]
        
        # Synthesize multiple responses
        response_parts = [f"Phân tích đa lĩnh vực cho câu hỏi: '{question}'", ""]
        
        domain_names = {
            'finance': 'Tài chính',
            'hr': 'Nhân sự',
            'equipment': 'Thiết bị',
            'infrastructure': 'Hạ tầng'
        }
        
        for domain, response in responses.items():
            domain_name = domain_names.get(domain, domain)
            response_parts.append(f"## {domain_name}")
            response_parts.append(response)
            response_parts.append("")  # Empty line for spacing
        
        return "\n".join(response_parts)
    
    def answer_question(self, document_text: str, question: str) -> str:
        """Main method to answer question using specialized agents"""
        try:
            # Route question to appropriate agents
            responses = self.route_question(question, document_text)
            
            # If no relevant responses, try local analysis
            if not responses:
                # Use a simple local analyzer for basic response
                sentences = document_text.split('.')
                relevant_sentences = []
                question_words = set(question.lower().split())
                
                for sentence in sentences:
                    sentence_words = set(sentence.lower().split())
                    overlap = len(question_words.intersection(sentence_words))
                    if overlap > 0:
                        relevant_sentences.append((sentence.strip(), overlap))
                
                relevant_sentences.sort(key=lambda x: x[1], reverse=True)
                
                if relevant_sentences:
                    top_sentences = [sentence for sentence, score in relevant_sentences[:3]]
                    return "Dựa trên tài liệu, đây là thông tin liên quan:\n\n" + "\n".join(f"- {s}" for s in top_sentences)
                else:
                    return "Không tìm thấy thông tin phù hợp trong tài liệu để trả lời câu hỏi."
            
            # Synthesize final response
            final_response = self.synthesize_response(question, responses)
            
            return final_response
        except Exception as e:
            return f"Lỗi trong hệ thống multi-agent: {str(e)}"