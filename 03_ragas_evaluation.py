import os
import json
import warnings
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

# Bỏ qua các cảnh báo không cần thiết từ RAGAS
warnings.filterwarnings("ignore")

# ── 1. Môi trường và Import ──────────────────────────────────────────────────
load_dotenv()

from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import danh sách câu hỏi và câu trả lời chuẩn
try:
    from qa_pairs import QA_PAIRS
except ImportError:
    print("❌ Lỗi: Không tìm thấy qa_pairs.py")
    QA_PAIRS = []

# ── 2. Cấu hình Prompt (Giống Bước 2) ─────────────────────────────────────────

SYSTEM_V1 = (
    "Bạn là một trợ lý AI chỉ được phép sử dụng thông tin từ ngữ cảnh được cung cấp. "
    "Nhiệm vụ: Trả lời ngắn gọn (1-2 câu). "
    "QUY TẮC NGHIÊM NGẶT: Nếu câu trả lời không có trong ngữ cảnh, hãy nói 'Tôi không biết'. "
    "Tuyệt đối không sử dụng kiến thức bên ngoài hoặc tự bịa ra thông tin.\n\n"
    "Ngữ cảnh:\n{context}"
)
PROMPT_V1 = ChatPromptTemplate.from_messages([("system", SYSTEM_V1), ("human", "{question}")])

SYSTEM_V2 = (
    "Bạn là một chuyên gia AI có nhiệm vụ trích xuất thông tin chính xác từ tài liệu.\n\n"
    "Quy trình làm việc:\n"
    "1. Kiểm tra xem ngữ cảnh có chứa câu trả lời không.\n"
    "2. Nếu có, hãy trả lời chi tiết và có cấu trúc (3-5 câu) dựa TRÊN DUY NHẤT ngữ cảnh đó.\n"
    "3. Nếu không có, hãy trả lời: 'Dựa trên tài liệu được cung cấp, tôi không thể tìm thấy thông tin này.'\n"
    "4. Cấm sử dụng bất kỳ kiến thức nào không xuất hiện trong ngữ cảnh.\n\n"
    "Ngữ cảnh:\n{context}"
)
PROMPT_V2 = ChatPromptTemplate.from_messages([("system", SYSTEM_V2), ("human", "{question}")])

PROMPTS = {"v1": PROMPT_V1, "v2": PROMPT_V2}

# ── 3. Xây dựng Vector Store (Tương tự Bước 1 & 2) ─────────────────────────────
def build_vectorstore():
    embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small"))
    kb_path = Path("data/knowledge_base.txt")
    text = kb_path.read_text(encoding="utf-8")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    return FAISS.from_texts(chunks, embeddings)

# ── 4. Hàm chạy RAG và thu thập kết quả ───────────────────────────────────────
def run_rag_for_eval(retriever, llm, prompt, question: str) -> dict:
    """Chạy RAG và trả về câu trả lời cùng danh sách ngữ cảnh."""
    docs = retriever.invoke(question)
    contexts = [doc.page_content for doc in docs] # RAGAS cần danh sách các chuỗi
    
    ctx_str = "\n\n".join(contexts)
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": ctx_str, "question": question})
    
    return {"answer": answer, "contexts": contexts}

def collect_results(vectorstore, llm, version: str):
    """Chạy 50 câu hỏi cho một phiên bản prompt cụ thể."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    prompt = PROMPTS[version]
    results = []
    
    print(f"\n🏃 Đang thu thập câu trả lời cho phiên bản {version.upper()}...")
    for i, qa in enumerate(QA_PAIRS, 1):
        out = run_rag_for_eval(retriever, llm, prompt, qa["question"])
        results.append({
            "question": qa["question"],
            "reference": qa["answer"], # Câu trả lời chuẩn
            "answer": out["answer"],
            "contexts": out["contexts"]
        })
        if i % 10 == 0: print(f"  Processed {i}/{len(QA_PAIRS)} questions")
        
    return results

# ── 5. Đánh giá bằng RAGAS ───────────────────────────────────────────────────
def evaluate_with_ragas(rag_results, llm_eval, emb_eval, version: str):
    """Sử dụng RAGAS để tính toán các chỉ số."""
    print(f"\n📐 Đang tính toán chỉ số RAGAS cho phiên bản {version.upper()}...")
    
    # Chuyển đổi sang định dạng EvaluationDataset của RAGAS
    samples = [
        SingleTurnSample(
            user_input=r["question"],
            response=r["answer"],
            retrieved_contexts=r["contexts"],
            reference=r["reference"]
        )
        for r in rag_results
    ]
    dataset = EvaluationDataset(samples=samples)
    
    # Thực hiện đánh giá
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=llm_eval,
        embeddings=emb_eval
    )
    
    # Tính điểm trung bình cho từng chỉ số
    scores = {}
    for key in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]:
        raw_scores = result[key]
        # Loại bỏ các giá trị None nếu có
        valid_scores = [v for v in raw_scores if v is not None and not np.isnan(v)]
        scores[key] = float(np.mean(valid_scores)) if valid_scores else 0.0
        
    return scores

# ── 6. Chương trình chính ────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🚀 Bắt đầu Step 3: RAGAS Evaluation (Dự kiến 15-20 phút)")
    print("=" * 60)

    # Khởi tạo các thành phần
    vectorstore = build_vectorstore()
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"), temperature=0)
    
    # LLM và Embeddings dùng để chấm điểm (Evaluation)
    llm_eval = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    emb_eval = OpenAIEmbeddings(model="text-embedding-3-small")

    # 1. Thu thập dữ liệu từ cả 2 phiên bản
    v1_results = collect_results(vectorstore, llm, "v1")
    v2_results = collect_results(vectorstore, llm, "v2")

    # 2. Đánh giá bằng RAGAS
    v1_scores = evaluate_with_ragas(v1_results, llm_eval, emb_eval, "v1")
    v2_scores = evaluate_with_ragas(v2_results, llm_eval, emb_eval, "v2")

    # 3. In bảng so sánh kết quả
    print("\n" + "=" * 60)
    print(f"{'Chỉ số (Metric)':<25} | {'V1 (Concise)':<15} | {'V2 (Structured)':<15}")
    print("-" * 60)
    
    metrics = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
    for m in metrics:
        s1, s2 = v1_scores[m], v2_scores[m]
        winner = "🏆 V1" if s1 > s2 else "🏆 V2" if s2 > s1 else "Hòa"
        print(f"{m:<25} | {s1:<15.4f} | {s2:<15.4f} | {winner}")

    # 4. Kiểm tra mục tiêu Faithfulness >= 0.8
    best_faith = max(v1_scores["faithfulness"], v2_scores["faithfulness"])
    print("\n" + "=" * 60)
    if best_faith >= 0.8:
        print(f"✅ ĐẠT MỤC TIÊU: Faithfulness cao nhất là {best_faith:.4f}")
    else:
        print(f"⚠️ CHƯA ĐẠT MỤC TIÊU: Faithfulness cao nhất chỉ đạt {best_faith:.4f}")

    # 5. Lưu báo cáo JSON
    report = {
        "v1_scores": v1_scores,
        "v2_scores": v2_scores,
        "comparison": {m: "v1" if v1_scores[m] > v2_scores[m] else "v2" for m in metrics},
        "target_met": best_faith >= 0.8
    }
    
    output_path = Path("data/ragas_report.json")
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n💾 Đã lưu báo cáo tại: {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
