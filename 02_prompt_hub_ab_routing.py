import os
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# ── 1. Môi trường và Import ──────────────────────────────────────────────────
load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import Client, traceable

# Import danh sách câu hỏi từ file qa_pairs.py (đã tạo ở Bước 1)
try:
    from qa_pairs import QA_PAIRS
    SAMPLE_QUESTIONS = [pair["question"] for pair in QA_PAIRS]
except ImportError:
    SAMPLE_QUESTIONS = ["What is RAG?"] * 50 # Fallback

# ── 2. Định nghĩa 2 phiên bản Prompt ─────────────────────────────────────────

# Phiên bản V1: Ngắn gọn (Concise)
SYSTEM_V1 = (
    "Bạn là một trợ lý AI hữu ích. Hãy trả lời câu hỏi của người dùng CHỈ sử dụng ngữ cảnh được cung cấp. "
    "Hãy trả lời thật ngắn gọn (từ 1-3 câu). "
    "Nếu ngữ cảnh không có câu trả lời, hãy nói: 'Tôi không có đủ thông tin.'\n\n"
    "Ngữ cảnh:\n{context}"
)
PROMPT_V1 = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_V1),
    ("human", "{question}"),
])

# Phiên bản V2: Chi tiết và có cấu trúc (Structured)
SYSTEM_V2 = (
    "Bạn là một chuyên gia đào tạo AI. Hãy cung cấp câu trả lời chính xác và có cấu trúc.\n\n"
    "Hướng dẫn:\n"
    "1. Đọc kỹ ngữ cảnh được cung cấp.\n"
    "2. Xác định các ý chính liên quan đến câu hỏi.\n"
    "3. Viết câu trả lời rõ ràng, trình bày theo từng ý (từ 3-5 câu).\n"
    "4. Nếu ngữ cảnh không đủ thông tin, hãy nêu rõ điều đó.\n\n"
    "Ngữ cảnh:\n{context}"
)
PROMPT_V2 = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_V2),
    ("human", "{question}"),
])

# Tên của các Prompt trên LangSmith Hub (Sử dụng tên duy nhất của bạn)
# Lấy tên project từ .env để làm tiền tố cho tên prompt
PROJECT_PREFIX = os.getenv("LANGCHAIN_PROJECT", "day22-lab").replace("-", "_")
PROMPT_V1_NAME = f"{PROJECT_PREFIX}_v1"
PROMPT_V2_NAME = f"{PROJECT_PREFIX}_v2"

# ── 3. Đẩy Prompts lên LangSmith Hub ─────────────────────────────────────────
def push_prompts_to_hub(client):
    """Đẩy cả 2 phiên bản prompt lên LangSmith Prompt Hub."""
    print("📤 Đang đẩy prompts lên LangSmith Hub...")
    
    # Đẩy V1
    try:
        url_v1 = client.push_prompt(PROMPT_V1_NAME, object=PROMPT_V1, description="V1 – Trả lời ngắn gọn")
        print(f"✅ Đã đẩy V1 thành công: {url_v1}")
    except Exception as e:
        print(f"⚠️ Lỗi khi đẩy V1: {e}")

    # Đẩy V2
    try:
        url_v2 = client.push_prompt(PROMPT_V2_NAME, object=PROMPT_V2, description="V2 – Trả lời chi tiết/cấu trúc")
        print(f"✅ Đã đẩy V2 thành công: {url_v2}")
    except Exception as e:
        print(f"⚠️ Lỗi khi đẩy V2: {e}")

# ── 4. Kéo Prompts từ Hub về ────────────────────────────────────────────────
def pull_prompts_from_hub(client):
    """Tải các prompt từ Hub về để sử dụng."""
    print("📥 Đang kéo prompts từ LangSmith Hub...")
    prompts = {}

    # Thử kéo V1, nếu lỗi thì dùng bản local
    try:
        prompts[PROMPT_V1_NAME] = client.pull_prompt(PROMPT_V1_NAME)
        print(f"  ↓ Đã kéo '{PROMPT_V1_NAME}'")
    except Exception:
        prompts[PROMPT_V1_NAME] = PROMPT_V1
        print(f"  ℹ️ Sử dụng bản V1 local (fallback)")

    # Thử kéo V2, nếu lỗi thì dùng bản local
    try:
        prompts[PROMPT_V2_NAME] = client.pull_prompt(PROMPT_V2_NAME)
        print(f"  ↓ Đã kéo '{PROMPT_V2_NAME}'")
    except Exception:
        prompts[PROMPT_V2_NAME] = PROMPT_V2
        print(f"  ℹ️ Sử dụng bản V2 local (fallback)")

    return prompts

# ── 5. Điều hướng A/B (Deterministic Routing) ───────────────────────────────
def get_prompt_version(request_id: str) -> str:
    """
    Sử dụng hàm băm (hash) MD5 để đảm bảo cùng một request_id 
    luôn được điều hướng tới cùng một phiên bản prompt (Deterministic).
    """
    # Chuyển hash MD5 thành số nguyên
    hash_int = int(hashlib.md5(request_id.encode()).hexdigest(), 16)
    
    # Số chẵn dùng V1, số lẻ dùng V2 -> Chia đều 50/50
    return PROMPT_V1_NAME if hash_int % 2 == 0 else PROMPT_V2_NAME

# ── 6. Xây dựng Vector Store (Tương tự Bước 1) ─────────────────────────────
def build_vectorstore():
    embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small"))
    kb_path = Path("data/knowledge_base.txt")
    text = kb_path.read_text(encoding="utf-8")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    return FAISS.from_texts(chunks, embeddings)

# ── 7. Hàm truy vấn A/B có giám sát ──────────────────────────────────────────
@traceable(name="ab-rag-query", tags=["ab-test", "step2"])
def ask_ab(retriever, llm, prompt, question: str, version_tag: str) -> str:
    """Thực hiện truy vấn với prompt được chỉ định."""
    
    # 1. Truy xuất thông tin
    docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    
    # 2. Tạo chuỗi và thực thi
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": question})

# ── 8. Chương trình chính (Main) ────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🚀 Đang khởi chạy Step 2: Prompt Hub & A/B Routing")
    print("=" * 60)

    # Khởi tạo client LangSmith và các mô hình
    client = Client()
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"), temperature=0)
    
    # 1. Đẩy và Kéo Prompt từ Hub
    push_prompts_to_hub(client)
    prompts = pull_prompts_from_hub(client)

    # 2. Chuẩn bị Vector Store và Retriever
    print("📦 Đang chuẩn bị cơ sở dữ liệu vector...")
    vectorstore = build_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 3. Chạy A/B Testing qua 50 câu hỏi
    v1_count = 0
    v2_count = 0
    
    print(f"🔍 Bắt đầu chạy A/B Test cho {len(SAMPLE_QUESTIONS)} câu hỏi...")
    
    for i, question in enumerate(SAMPLE_QUESTIONS):
        # Tạo request_id duy nhất cho mỗi câu hỏi
        request_id = f"req-{i:04d}"
        
        # Quyết định dùng phiên bản nào
        version_key = get_prompt_version(request_id)
        version_tag = "v1" if version_key == PROMPT_V1_NAME else "v2"
        
        if version_tag == "v1": v1_count += 1
        else: v2_count += 1
        
        # Thực hiện truy vấn
        prompt = prompts[version_key]
        answer = ask_ab(retriever, llm, prompt, question, version_tag)
        
        print(f"[{i+1:02d}] [prompt-{version_tag}] Q: {question[:50]}...")

    print("\n" + "=" * 60)
    print(f"📊 Tổng kết điều hướng: V1 = {v1_count} | V2 = {v2_count}")
    print(f"✅ Hoàn thành! Thêm {len(SAMPLE_QUESTIONS)} traces đã được gửi lên LangSmith.")
    print("🔗 Hãy kiểm tra Prompt Hub: https://smith.langchain.com/hub")
    print("=" * 60)

if __name__ == "__main__":
    main()
