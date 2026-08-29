import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


load_dotenv()
loader = PyPDFDirectoryLoader(".")
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
splits = text_splitter.split_documents(docs)

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

template = (
    "Bạn là một trợ lý ảo nội bộ nghiêm ngặt.\n"
    "LUẬT:\n"
    "1) CHỈ sử dụng thông tin trong tài liệu (Context) bên dưới để trả lời.\n"
    "2) Nếu thông tin không có trong tài liệu, hãy nói: 'Huhu, tớ tìm hoài trong tài liệu mà không thấy thông tin này đâu cả. Cậu hỏi câu khác liên quan đến tài liệu nha! 🥺'\n"
    "3) KHÔNG sử dụng kiến thức bên ngoài, không bịa đặt.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}"
)
prompt = ChatPromptTemplate.from_template(template)

llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)

if __name__ == "__main__":
    print("\nCHATBOT SẴN SÀNG ^^")
    while True:
        question = input("\nCâu hỏi (nhập 'q' để thoát): ")
        if question.lower() == 'q':
            break

        print("Đang suy nghĩ...")
        try:
            answer = rag_chain.invoke(question)
            print(answer)
        except Exception as e:
            print("\nKhông tìm thấy:", e)