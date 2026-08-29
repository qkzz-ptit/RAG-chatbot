import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


st.set_page_config(page_title="PTIT AI Chatbot", page_icon="🤖")
st.title("Trợ lý ảo AI - PTIT 🎓")


load_dotenv()

@st.cache_resource
def init_vectorstore():
    docs = []
    if os.path.exists("."):
        for file in os.listdir("."):
            if file.endswith(".pdf"):
                try:
                    loader = PyPDFDirectoryLoader(".")
                    docs = loader.load()
                except Exception as e:
                    pass

        loader = PyPDFDirectoryLoader(".")
        docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 5})


with st.spinner("Đang tải dữ liệu và khởi động hệ thống..."):
    retriever = init_vectorstore()

llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

template = (
    "Bạn là một trợ lý ảo RAG vô cùng đáng yêu, thân thiện và ngọt ngào.\n"
    "LUẬT SIÊU CẤP QUAN TRỌNG:\n"
    "1) Bạn CHỈ được phép sử dụng thông tin có sẵn trong phần tài liệu (Context) bên dưới để trả lời thôi nhé.\n"
    "2) Nếu thông tin không có trong tài liệu, hãy nhẹ nhàng trả lời rằng: "
    "\"Huhu, tớ tìm hoài trong tài liệu mà không thấy thông tin này đâu cả. Cậu hỏi câu khác liên quan đến tài liệu nha! 🥺\"\n"
    "3) Tuyệt đối không tự bịa đặt hay dùng kiến thức ngoài nha.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}"
)
prompt = ChatPromptTemplate.from_template(template)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_query := st.chat_input("Nhập câu hỏi của bạn về PTIT..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Đang suy nghĩ..."):
            try:
                response = rag_chain.invoke(user_query)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                err_msg = f"Đã xảy ra lỗi: {e}"
                st.error(err_msg)