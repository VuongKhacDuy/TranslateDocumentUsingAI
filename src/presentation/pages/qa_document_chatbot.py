# QA Document Chatbot with Multi-Provider Support
# Uses the existing translator infrastructure from the project

import streamlit as st
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.domain.translator import Translator
from src.infrastructure.multi_api_manager import APIProvider

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

if available_providers:
    provider = st.selectbox(
        "Chọn nhà cung cấp AI",
        available_providers,
        format_func=format_provider
    )
else:
    provider = st.selectbox(
        "Chọn nhà cung cấp AI",
        ["gemini", "openai", "claude", "deepseek"],
        format_func=format_provider
    )
    st.info("Bạn có thể cấu hình API trong trang 'API Management' để sử dụng các nhà cung cấp này.")

uploaded_file = st.file_uploader("Tải lên tài liệu (txt)", type=["txt"])
question = st.text_input("Nhập câu hỏi về tài liệu:")

# Document processing
if uploaded_file is not None:
    # Read document content
    doc_text = uploaded_file.read().decode("utf-8")
    st.session_state.document_content = doc_text
    
    # Process document only if not already processed
    if st.session_state.vectorstore is None:
        with st.spinner("Đang xử lý tài liệu..."):
            # Split text into chunks
            splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs = splitter.split_text(doc_text)
            
            # Create documents for LangChain
            documents = [Document(page_content=doc) for doc in docs]
            
            # For demo purposes, we'll use a simple in-memory vectorstore
            # In a production environment, you would use a proper embedding model
            st.session_state.vectorstore = Chroma.from_documents(documents, embedding=None)
            
            st.success("Tài liệu đã được xử lý thành công!")

# Process question
if st.button("Gửi câu hỏi") and question:
    if st.session_state.vectorstore is None:
        st.warning("Vui lòng tải lên tài liệu trước khi đặt câu hỏi.")
    else:
        with st.spinner("Đang xử lý câu hỏi..."):
            try:
                # Add to chat history
                st.session_state.chat_history.append(("Người dùng", question))
                
                # Perform similarity search
                docs = st.session_state.vectorstore.similarity_search(question, k=4)
                
                # Create context from retrieved documents
                context = "\n\n".join([doc.page_content for doc in docs])
                
                # Create prompt
                prompt = f"""
                Dựa trên tài liệu sau đây:
                
                {context}
                
                Hãy trả lời câu hỏi sau:
                
                {question}
                
                Nếu thông tin trong tài liệu không đủ để trả lời câu hỏi, hãy nói rằng bạn không tìm thấy thông tin liên quan.
                """
                
                # Use the existing translator infrastructure
                answer = ""
                provider_str = provider if provider is not None else "gemini"
                if api_manager and api_manager.has_apis_for_provider(APIProvider(provider_str)):
                    # Get active APIs for the selected provider
                    selected_apis = api_manager.get_active_apis(provider_filter=APIProvider(provider_str))
                    if selected_apis:
                        # Use the first available API
                        api_config = selected_apis[0]
                        translator = Translator(
                            model_type=api_config.provider.value,
                            api_key=api_config.api_key,
                            base_url=api_config.base_url,
                            model_name=api_config.model_name
                        )
                        
                        # Translate the prompt (in this case, we're using it for QA)
                        # Since translate_batch expects a list, we pass a list with one item
                        translated_texts = translator.translate_batch([prompt], "vi")
                        answer = translated_texts[0] if translated_texts else prompt
                    else:
                        provider_name = provider_labels.get(provider_str, str(provider_str))
                        answer = f"Không tìm thấy API đang hoạt động cho nhà cung cấp {provider_name}."
                else:
                    # Fallback: simulate response
                    provider_name = provider_labels.get(provider_str, str(provider_str))
                    answer = f"[{provider_name}] Đây là câu trả lời mẫu cho câu hỏi của bạn về tài liệu. Trong triển khai thực tế, hệ thống sẽ sử dụng {provider_name} API để tạo câu trả lời chính xác. Tài liệu có {len(context)} ký tự liên quan đến câu hỏi của bạn."
                
                # Add to chat history
                st.session_state.chat_history.append(("AI", answer))
                
                # Display response
                st.success("Câu trả lời:")
                st.write(answer)
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
st.info("Lưu ý: Để sử dụng chức năng đầy đủ, hãy cấu hình API trong trang 'API Management'.")