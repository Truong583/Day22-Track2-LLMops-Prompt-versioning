import os
from pathlib import Path
from dotenv import load_dotenv

# ── 1. Môi trường (Environment Setup) ────────────────────────────────────────
# Tải các biến môi trường từ tệp .env TRƯỚC KHI import LangChain
load_dotenv()

# Các biến môi trường cho LangSmith (đã được load từ .env)
# Nếu chưa có trong .env, bạn có thể thiết lập trực tiếp ở đây:
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = "your_key"
# os.environ["LANGCHAIN_PROJECT"] = "Day22_RAG_Lab"

# ── 2. Import các thư viện LangChain và LangSmith ──────────────────────────
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable

# Import danh sách câu hỏi từ qa_pairs.py
try:
    from qa_pairs import QA_PAIRS
    SAMPLE_QUESTIONS = [pair["question"] for pair in QA_PAIRS]
except ImportError:
    print("⚠️ Không tìm thấy qa_pairs.py, sử dụng danh sách câu hỏi mặc định.")
    SAMPLE_QUESTIONS = ["What is RAG?", "How does LangSmith help?"]

# ── 3. Khởi tạo LLM và Embeddings ──────────────────────────────────────────
# Sử dụng gpt-4o-mini làm mặc định nếu không có trong .env
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
    temperature=0
)

embeddings = OpenAIEmbeddings(
    model=os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
)

# ── 4. Xây dựng Vector Store từ Cơ sở tri thức ──────────────────────────────
def build_vectorstore():
    """
    Nạp dữ liệu từ knowledge_base.txt, chia nhỏ và lập chỉ mục bằng FAISS.
    """
    kb_path = Path("data/knowledge_base.txt")
    if not kb_path.exists():
        raise FileNotFoundError(f"❌ Không tìm thấy file dữ liệu tại {kb_path}")

    text = kb_path.read_text(encoding="utf-8")

    # Chia nhỏ văn bản: chunk_size=500, overlap=50
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=50
    )
    chunks = splitter.split_text(text)
    print(f"📦 Đã chia cơ sở tri thức thành {len(chunks)} đoạn văn bản.")

    # Tạo vector store bằng FAISS
    vectorstore = FAISS.from_texts(chunks, embeddings)
    print("✅ Đã xây dựng xong index FAISS.")
    return vectorstore

# ── 5. Thiết lập Prompt Template cho RAG ────────────────────────────────────
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Bạn là một chuyên gia AI. Hãy sử dụng các thông tin ngữ cảnh dưới đây để trả lời câu hỏi.\nNếu không có thông tin trong ngữ cảnh, hãy nói bạn không biết, đừng tự bịa ra câu trả lời.\n\nNgữ cảnh:\n{context}"),
    ("human", "{question}"),
])

# ── 6. Xây dựng chuỗi RAG (RAG Chain) ──────────────────────────────────────
def build_rag_chain(vectorstore):
    """
    Xây dựng chuỗi RAG bằng LCEL.
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Cấu trúc chuỗi: retriever -> prompt -> llm -> parser
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    
    return chain

# ── 7. Hàm truy vấn có giám sát (Traced Query) ──────────────────────────────
# Gắn nhãn @traceable để LangSmith tự động ghi lại vết chạy
@traceable(name="rag-query", tags=["day22", "step1"])
def ask(chain, question: str) -> str:
    """
    Thực hiện truy vấn qua chuỗi RAG và trả về câu trả lời.
    """
    return chain.invoke(question)

# ── 8. Chương trình chính (Main) ────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🚀 Đang khởi chạy Step 1: LangSmith RAG Pipeline")
    print("=" * 60)

    try:
        # 1. Xây dựng kho tri thức
        vectorstore = build_vectorstore()

        # 2. Tạo chuỗi xử lý RAG
        chain = build_rag_chain(vectorstore)

        # 3. Chạy qua tất cả các câu hỏi để tạo 50 traces
        print(f"🔍 Bắt đầu chạy {len(SAMPLE_QUESTIONS)} câu hỏi truy vấn...")
        
        for i, question in enumerate(SAMPLE_QUESTIONS, 1):
            answer = ask(chain, question)
            print(f"[{i:02d}/{len(SAMPLE_QUESTIONS)}] Q: {question[:50]}...")
            # print(f"       A: {answer[:100]}...") # Bỏ comment nếu muốn xem câu trả lời chi tiết

        print("\n" + "=" * 60)
        print(f"✅ Hoàn thành! Đã gửi {len(SAMPLE_QUESTIONS)} traces lên dự án '{os.getenv('LANGCHAIN_PROJECT')}'")
        print("🔗 Hãy truy cập: https://smith.langchain.com để kiểm tra kết quả.")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    main()
