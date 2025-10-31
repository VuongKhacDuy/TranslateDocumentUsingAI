# QA Document Chatbot with Multi-Provider Support
# Uses the existing translator infrastructure from the project

import streamlit as st
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import os
import sys
from pathlib import Path
from openai import OpenAI
import re
from collections import Counter

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.domain.translator import Translator
from src.infrastructure.multi_api_manager import APIProvider
from src.infrastructure.file_handler import FileHandler

class LocalDocumentAnalyzer:
    """Local document analysis and question answering without third-party AI models"""
    
    def __init__(self):
        pass
    
    def preprocess_text(self, text):
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep Vietnamese characters
        text = re.sub(r'[^\w\s\u00C0-\u1EF9]', ' ', text)
        return text.strip()
    
    def extract_keywords(self, text, num_keywords=10):
        """Extract keywords from text"""
        # Preprocess text
        processed_text = self.preprocess_text(text)
        # Split into words
        words = processed_text.split()
        # Filter out common Vietnamese stop words
        stop_words = {'và', 'hoặc', 'nhưng', 'mà', 'thì', 'là', 'của', 'trong', 'với', 'cho', 'đến', 'từ', 'bởi', 'tại', 'theo', 'về', 'như', 'nên', 'ra', 'vào', 'lên', 'xuống', 'đi', 'đứng', 'ngồi', 'nằm', 'ăn', 'uống', 'ở', 'tới', 'qua', 'lại', 'rồi', 'sau', 'trước', 'giữa', 'trên', 'dưới', 'trong', 'ngoài', 'bên', 'gần', 'xa', 'nhiều', 'ít', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười'}
        filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]
        # Count word frequencies
        word_freq = Counter(filtered_words)
        # Get most common words
        keywords = [word for word, freq in word_freq.most_common(num_keywords)]
        return keywords
    
    def find_relevant_sentences(self, text, question, num_sentences=3):
        """Find sentences most relevant to the question"""
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Preprocess question
        question_words = set(self.preprocess_text(question).split())
        
        # Score sentences based on word overlap with question
        sentence_scores = []
        for sentence in sentences:
            sentence_words = set(self.preprocess_text(sentence).split())
            # Calculate overlap score
            overlap = len(question_words.intersection(sentence_words))
            sentence_scores.append((sentence, overlap))
        
        # Sort by score and return top sentences
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        relevant_sentences = [sentence for sentence, score in sentence_scores[:num_sentences] if score > 0]
        
        return relevant_sentences
    
    def answer_question(self, document_text, question):
        """Answer question based on document content using local processing"""
        try:
            # Extract keywords from document
            keywords = self.extract_keywords(document_text, 15)
            
            # Find relevant sentences
            relevant_sentences = self.find_relevant_sentences(document_text, question, 5)
            
            if not relevant_sentences:
                return "Tôi không tìm thấy thông tin liên quan đến câu hỏi này trong tài liệu đã cung cấp."
            
            # Create answer based on relevant sentences
            answer_parts = []
            answer_parts.append("Dựa trên tài liệu được cung cấp, đây là câu trả lời cho câu hỏi của bạn:")
            answer_parts.append("")
            
            for i, sentence in enumerate(relevant_sentences[:3], 1):
                answer_parts.append(f"{i}. {sentence}")
            
            answer_parts.append("")
            answer_parts.append(f"Từ khóa chính trong tài liệu: {', '.join(keywords[:10])}")
            
            return "\n".join(answer_parts)
            
        except Exception as e:
            return f"Không thể xử lý câu hỏi do lỗi: {str(e)}"

class QADocumentChatbotPage:
    def __init__(self):
        pass
    
    def render(self):
        st.header("📄 AI Chatbot hỏi đáp tài liệu")

        # Initialize session state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'vectorstore' not in st.session_state:
            st.session_state.vectorstore = None
        if 'document_content' not in st.session_state:
            st.session_state.document_content = ""
        if 'selected_provider' not in st.session_state:
            st.session_state.selected_provider = "gemini"

        # Initialize file handler
        file_handler = FileHandler()
        
        # Initialize local analyzer
        local_analyzer = LocalDocumentAnalyzer()

        # Check for configured APIs
        api_manager = None
        if "api_manager" in st.session_state:
            api_manager = st.session_state.api_manager
            active_apis = api_manager.get_active_apis()
            if not active_apis:
                st.warning("⚠️ No APIs configured. Please go to API Management to add at least one API.")
        else:
            st.warning("API Manager not initialized. Please restart the application.")

        # Provider selection (only show providers that have active APIs)
        available_providers = []
        provider_labels = {
            "gemini": "Google Gemini",
            "openai": "OpenAI GPT",
            "claude": "Anthropic Claude",
            "deepseek": "DeepSeek"
        }

        if api_manager:
            for provider in APIProvider:
                if api_manager.has_apis_for_provider(provider):
                    available_providers.append(provider.value)

        def format_provider(x):
            return provider_labels.get(x, str(x))

        # Add local processing option
        all_providers = available_providers + ["local"] if available_providers else ["local", "gemini", "openai", "claude", "deepseek"]
        provider_labels["local"] = "🧠 Xử lý cục bộ (không AI bên ngoài)"

        provider = st.selectbox(
            "Chọn nhà cung cấp AI",
            all_providers,
            format_func=format_provider
        )

        # Support for multiple file types
        uploaded_file = st.file_uploader("Tải lên tài liệu (txt, csv, xlsx, xls, pdf, doc, docx)", type=["txt", "csv", "xlsx", "xls", "pdf", "doc", "docx"])

        # Clear button to reset uploaded file and conversation
        if st.button("🗑️ Xóa tài liệu và lịch sử trò chuyện"):
            # Reset session state
            st.session_state.chat_history = []
            st.session_state.vectorstore = None
            st.session_state.document_content = ""
            st.success("Đã xóa tài liệu và lịch sử trò chuyện!")
            st.rerun()

        question = st.text_input("Nhập câu hỏi về tài liệu:")

        # Document processing
        if uploaded_file is not None:
            # Save uploaded file
            temp_file_path = file_handler.save_uploaded_file(uploaded_file)
            
            # Read document content using the existing file handler
            try:
                with st.spinner("Đang xử lý tài liệu..."):
                    # Show file size for user awareness
                    file_size = os.path.getsize(temp_file_path)
                    if file_size > 1024 * 1024:  # > 1MB
                        st.info(f"Kích thước file: {file_size / (1024*1024):.1f} MB. Quá trình xử lý có thể mất vài phút...")
                    
                    # Extract text from the document
                    texts = file_handler.extract_text(temp_file_path)
                    
                    # Combine all extracted texts
                    doc_text = "\n\n".join(texts) if texts else ""
                    st.session_state.document_content = doc_text
                    
                    # Show processing progress for large documents
                    if len(doc_text) > 50000:  # > 50KB
                        st.info(f"Tài liệu có {len(doc_text)} ký tự. Đang xử lý...")
                    
                    # Process document only if not already processed
                    if st.session_state.vectorstore is None:
                        # Split text into chunks
                        with st.spinner("Đang chia nhỏ tài liệu..."):
                            splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                            docs = splitter.split_text(doc_text)
                        
                        # Show number of chunks
                        st.info(f"Đã chia tài liệu thành {len(docs)} đoạn.")
                        
                        # Create documents for LangChain
                        with st.spinner("Đang tạo vector store..."):
                            documents = [Document(page_content=doc) for doc in docs]
                            
                            # For demo purposes, we'll use a simple in-memory vectorstore
                            # In a production environment, you would use a proper embedding model
                            st.session_state.vectorstore = Chroma.from_documents(documents, embedding=None)
                        
                        st.success("Tài liệu đã được xử lý thành công!")
            except Exception as e:
                st.error(f"Lỗi khi xử lý tài liệu: {str(e)}")

        # Process question
        if st.button("Gửi câu hỏi") and question:
            if st.session_state.vectorstore is None and not st.session_state.document_content:
                st.warning("Vui lòng tải lên tài liệu trước khi đặt câu hỏi.")
            else:
                with st.spinner("Đang xử lý câu hỏi..."):
                    try:
                        # Add to chat history
                        st.session_state.chat_history.append(("Người dùng", question))
                        
                        answer = ""
                        
                        # Check if using local processing
                        if provider == "local":
                            # Use local document analyzer
                            if st.session_state.document_content:
                                answer = local_analyzer.answer_question(st.session_state.document_content, question)
                            else:
                                answer = "Không có nội dung tài liệu để phân tích."
                        else:
                            # Use AI provider (existing code)
                            # Perform similarity search
                            if st.session_state.vectorstore:
                                docs = st.session_state.vectorstore.similarity_search(question, k=4)
                                
                                # Create context from retrieved documents
                                context = "\n\n".join([doc.page_content for doc in docs])
                            else:
                                # Fallback to document content if no vectorstore
                                context = st.session_state.document_content[:4000] if st.session_state.document_content else ""
                            
                            # Create prompt for QA
                            system_prompt = """You are a helpful AI assistant that answers questions based on provided documents. 
                            Use the document context to answer the user's question accurately. 
                            If the information is not in the document, say so clearly.
                            Answer in Vietnamese."""
                            
                            user_prompt = f"""
                            Based on the following document context:
                            
                            {context}
                            
                            Please answer this question:
                            
                            {question}
                            
                            If the information needed to answer the question is not in the document context, please say: 
                            "Tôi không tìm thấy thông tin liên quan đến câu hỏi này trong tài liệu đã cung cấp."
                            """

                            # Use the existing API infrastructure
                            provider_str = provider if provider is not None else "gemini"
                            if api_manager and api_manager.has_apis_for_provider(APIProvider(provider_str)):
                                # Get active APIs for the selected provider
                                selected_apis = api_manager.get_active_apis(provider_filter=APIProvider(provider_str))
                                if selected_apis:
                                    # Use the first available API
                                    api_config = selected_apis[0]
                                    
                                    # Create OpenAI client directly for QA (not translation)
                                    client = OpenAI(
                                        api_key=api_config["api_key"],
                                        base_url=api_config["base_url"].strip()  # Strip whitespace/newlines
                                    )
                                    
                                    model_name = api_config["model_name"].strip() if api_config["model_name"] else "gemini-2.5-flash"
                                    
                                    # Call the API for question answering
                                    response = client.chat.completions.create(
                                        model=model_name,
                                        messages=[
                                            {"role": "system", "content": system_prompt},
                                            {"role": "user", "content": user_prompt}
                                        ],
                                        temperature=0.7,
                                        max_tokens=1000
                                    )
                                    
                                    answer = response.choices[0].message.content if response.choices[0].message.content else "Không có câu trả lời."
                                else:
                                    provider_name = provider_labels.get(provider_str, str(provider_str))
                                    answer = f"Không tìm thấy API đang hoạt động cho nhà cung cấp {provider_name}."
                            else:
                                # Fallback: simulate response with actual context
                                provider_name = provider_labels.get(provider_str, str(provider_str))
                                answer = f"[{provider_name}] {question}\n\nTài liệu có {len(context)} ký tự liên quan đến câu hỏi của bạn. Trong triển khai thực tế, hệ thống sẽ sử dụng {provider_name} API để tạo câu trả lời chính xác dựa trên nội dung tài liệu."
                        
                        # Add to chat history
                        st.session_state.chat_history.append(("AI", answer))
                        
                        # Display response with proper formatting
                        st.success("Câu trả lời:")
                        st.markdown(f"**AI:** {answer}")
                    except Exception as e:
                        st.error(f"Lỗi khi xử lý câu hỏi: {str(e)}")

        # Display chat history
        if st.session_state.chat_history:
            st.subheader("Lịch sử trò chuyện")
            for role, message in st.session_state.chat_history:
                if role == "Người dùng":
                    st.markdown(f"**Bạn:** {message}")
                else:
                    st.markdown(f"**AI:** {message}")

        # Document info
        if st.session_state.document_content:
            with st.expander("Thông tin tài liệu"):
                st.write(f"Độ dài tài liệu: {len(st.session_state.document_content)} ký tự")
                if st.checkbox("Hiển thị nội dung tài liệu"):
                    st.text_area("Nội dung tài liệu:", value=st.session_state.document_content[:1000] + ("..." if len(st.session_state.document_content) > 1000 else ""), height=200)

        st.info("Hướng dẫn: Tải lên tài liệu của bạn, chọn nhà cung cấp AI, sau đó đặt câu hỏi về tài liệu đó.")
        st.info("💡 Mẹo: Chọn 'Xử lý cục bộ (không AI bên ngoài)' để xử lý tài liệu mà không cần kết nối internet hoặc API key.")