# Yêu cầu bài Lab — Ngày 22: LangSmith + Prompt Versioning

## Phiên bản Python
Python 3.10 trở lên

## Cài đặt tất cả các thư viện phụ thuộc

```bash
pip install -r requirements.txt
```

## requirements.txt

```
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.3.0
langchain-community>=0.3.0
langchain-text-splitters>=0.3.0
langsmith>=0.2.0
openai>=1.0.0
faiss-cpu>=1.7.0
ragas>=0.4.0
guardrails-ai>=0.5.0
python-dotenv>=1.0.0
tiktoken>=0.5.0
datasets>=2.0.0
numpy>=1.25.0
```

## Mục đích của các gói thư viện

| Gói thư viện | Được dùng cho |
|---------|---------|
| `langchain` | Khung làm việc (framework) chính cho LLM |
| `langchain-openai` | ChatOpenAI, OpenAIEmbeddings |
| `langchain-community` | Tích hợp vectorstore FAISS |
| `langchain-text-splitters` | RecursiveCharacterTextSplitter |
| `langsmith` | LangSmith tracing, Prompt Hub client |
| `openai` | Gọi trực tiếp OpenAI API |
| `faiss-cpu` | Chỉ mục tìm kiếm tương đồng |
| `ragas` | Các chỉ số đánh giá RAG |
| `guardrails-ai` | Khung làm việc kiểm soát đầu ra |
| `python-dotenv` | Tải tệp cấu hình `.env` |
| `tiktoken` | Đếm token cho bộ chia văn bản |
| `datasets` | Được yêu cầu nội bộ bởi RAGAS |
| `numpy` | Tính trung bình danh sách điểm số RAGAS |

## Các lưu ý quan trọng về phiên bản

### RAGAS 0.4.x
- Sử dụng `from ragas.metrics import faithfulness, answer_relevancy, ...` (KHÔNG sử dụng từ `ragas.metrics.collections`)
- `result[metric_name]` trả về một **danh sách** (list) các số thực cho nhiều mẫu — hãy sử dụng `numpy.mean()` để tính trung bình
- Truyền `llm=` và `embeddings=` vào hàm `evaluate()`, không truyền vào hàm khởi tạo chỉ số (metric constructors)

### Guardrails AI 0.10.x
- Tham số `on_fail` nằm trong **hàm khởi tạo của validator**: `MyValidator(on_fail=OnFailAction.FIX)`
- `Guard.use()` nhận các **thực thể (instances)** validator, không phải các lớp (classes)
- `Guard.validate(text)` là điểm bắt đầu chính

### LangChain 0.3.x
- Sử dụng `ChatOpenAI(api_key=..., base_url=..., model=...)` cho các endpoint tùy chỉnh
- Sử dụng `OpenAIEmbeddings(api_key=..., base_url=..., model=...)` cho các endpoint nhúng tùy chỉnh

## Biến môi trường

Sao chép nội dung này vào tệp `.env` của bạn:


> ⚠️ **Tuyệt đối không commit `.env` lên git.** Hãy thêm nó vào `.gitignore`.

## Xác minh cài đặt

Chạy kiểm tra cấu hình:
```bash
python config.py
```

Kết quả mong đợi:
```
✅ Config loaded successfully
   LangSmith project : your-project-name
   OpenAI endpoint   : https://...
   Default LLM model : gpt-5.4-mini
   Embedding model   : text-embedding-3-small
```
