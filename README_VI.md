# 🧪 Bài Lab Ngày 22 — LangSmith + Prompt Versioning

## Tổng quan (Overview)

Trong bài lab này, bạn sẽ xây dựng một **hệ thống RAG (Retrieval-Augmented Generation) cấp độ sản xuất (production-grade)** và thực hiện giám sát toàn diện bằng cách sử dụng **LangSmith** để quan sát (observability), **Prompt Hub** để quản lý phiên bản prompt, **RAGAS** để đánh giá tự động, và **Guardrails AI** để đảm bảo an toàn đầu ra.

---

## Mục tiêu học tập (Learning Objectives)

Sau khi hoàn thành bài lab này, bạn sẽ có thể:

1. Thiết lập LangSmith tracing và kiểm tra các vết (traces) trong giao diện người dùng (UI)
2. Xây dựng một hệ thống RAG có giám sát với tìm kiếm vector bằng FAISS
3. Đẩy các phiên bản prompt lên LangSmith Prompt Hub và triển khai điều hướng A/B (A/B routing)
4. Chạy đánh giá RAG tự động bằng các chỉ số của RAGAS
5. Thêm các trình xác thực (validators) tùy chỉnh của Guardrails AI để phát hiện thông tin định danh cá nhân (PII) và xác thực JSON

---

## Điều kiện tiên quyết (Prerequisites)

- Python 3.10+
- Quyền truy cập vào API endpoint tương thích với OpenAI (được cung cấp qua tệp `.env`)
- Tài khoản LangSmith (đã cung cấp API key)

---

## Thiết lập môi trường (Environment Setup)

### 1. Cài đặt các thư viện phụ thuộc

```bash
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường

Tạo tệp `.env` (mẫu đã được cung cấp)

---

## Cấu trúc bài Lab (Lab Structure)

```
your_project/
├── .env                         # API keys (KHÔNG ĐƯỢC commit)
├── .gitignore                   # Phải loại trừ .env
├── requirements.txt
├── config.py                    # Các hàm hỗ trợ cấu hình dùng chung
├── qa_pairs.py                  # 50 cặp câu hỏi-đáp với câu trả lời chuẩn (ground-truth)
├── data/
│   ├── knowledge_base.txt       # Cơ sở tri thức cho RAG
│   └── ragas_report.json        # Được tạo ra bởi Bước 3
├── evidence/                    # ← Nộp thư mục này lên GitHub
│   ├── 01_langsmith_traces.png
│   ├── 02_prompt_hub.png
│   ├── 02_ab_routing_log.txt
│   ├── 03_ragas_scores.png
│   ├── 03_ragas_report.json
│   ├── 04_pii_demo_log.txt
│   └── 04_json_demo_log.txt
├── 01_langsmith_rag_pipeline.py # Bước 1: RAG + LangSmith tracing
├── 02_prompt_hub_ab_routing.py  # Bước 2: Prompt Hub + A/B routing
├── 03_ragas_evaluation.py       # Bước 3: Đánh giá bằng RAGAS
├── 04_guardrails_validator.py   # Bước 4: Guardrails AI
└── run_all.py                   # Chạy tất cả các bước theo thứ tự
```

---

## Các nhiệm vụ (Tasks)

---

### ✅ Nhiệm vụ 1 — LangSmith RAG Pipeline (25 điểm)

**Mục tiêu:** Xây dựng một hệ thống RAG đơn giản và xác minh rằng tất cả các truy vấn đều xuất hiện dưới dạng vết (traces) trong LangSmith.

**Những gì cần triển khai trong `01_langsmith_rag_pipeline.py`:**

1. Tải tập dữ liệu của bạn và chia nó thành các đoạn (chunks) bằng `RecursiveCharacterTextSplitter`
2. Tạo các bản nhúng văn bản (text embeddings) và lập chỉ mục các đoạn văn bản trong vector store FAISS
3. Xây dựng một chuỗi (chain) RAG bằng LangChain: retriever → prompt → LLM → output parser
4. Sử dụng decorator `@traceable` cho hàm truy vấn để mỗi lần gọi đều tạo ra một vết (trace) trong LangSmith
5. Chạy tất cả 50 câu hỏi từ `qa_pairs.py` thông qua hệ thống

**Xác minh:** Mở https://smith.langchain.com → chọn dự án của bạn → xác nhận có ≥ 50 vết (traces) với dữ liệu đầu vào/đầu ra/độ trễ hiển thị rõ ràng.

**Mẫu mã nguồn chính:**
```python
# Bật tính năng tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"]    = "<your-key>"
os.environ["LANGCHAIN_PROJECT"]    = "your-project-name"

# Gắn decorator cho hàm truy vấn
from langsmith import traceable

@traceable(name="rag-query")
def ask(chain, question: str) -> str:
    return chain.invoke(question)
```

---

### ✅ Nhiệm vụ 2 — Prompt Hub & Điều hướng A/B (25 điểm)

**Mục tiêu:** Đẩy hai phiên bản prompt lên LangSmith Prompt Hub và điều hướng các truy vấn một cách xác định (deterministically).

**Những gì cần triển khai trong `02_prompt_hub_ab_routing.py`:**

1. Viết hai prompt hệ thống khác biệt (V1: ngắn gọn, V2: có cấu trúc/chi tiết)
2. Đóng gói chúng trong `ChatPromptTemplate` và đẩy cả hai lên LangSmith Prompt Hub bằng `client.push_prompt()`
3. Kéo chúng ngược lại từ Hub bằng `client.pull_prompt()`
4. Triển khai hàm `get_prompt_version(request_id: str) -> str` sử dụng `hashlib.md5` để điều hướng 50/50 một cách xác định
5. Chạy tất cả 50 câu hỏi qua bộ điều hướng; ghi log phiên bản nào đã xử lý từng yêu cầu

**Xác minh:**
- LangSmith Prompt Hub hiển thị 2 phiên bản prompt có tên
- Đầu ra bảng điều khiển (console) hiển thị sự kết hợp giữa các nhãn `[prompt-v1]` và `[prompt-v2]`
- Thêm 50 vết (traces) xuất hiện trong LangSmith (tổng cộng ≥ 100)

**Mẫu mã nguồn chính:**
```python
import hashlib
from langsmith import Client

def get_prompt_version(request_id: str) -> str:
    h = int(hashlib.md5(request_id.encode()).hexdigest(), 16)
    return "prompt-v1" if h % 2 == 0 else "prompt-v2"

client = Client(api_key=LANGSMITH_API_KEY)
client.push_prompt("my-rag-prompt-v1", object=PROMPT_V1, description="...")
pulled = client.pull_prompt("my-rag-prompt-v1")
```

---

### ✅ Nhiệm vụ 3 — Đánh giá bằng RAGAS (25 điểm)

**Mục tiêu:** Đánh giá cả hai phiên bản prompt bằng RAGAS và so sánh điểm số mức độ trung thực (faithfulness scores).

**Những gì cần triển khai trong `03_ragas_evaluation.py`:**

1. Chạy tất cả 50 cặp QA qua **cả hai** phiên bản prompt; thu thập các câu trả lời và ngữ cảnh (contexts) đã được truy xuất
2. Xây dựng một `EvaluationDataset` từ các đối tượng `SingleTurnSample` (câu hỏi, câu trả lời, ngữ cảnh, tham chiếu)
3. Đánh giá với 4 chỉ số RAGAS: `faithfulness` (độ trung thực), `answer_relevancy` (độ liên quan của câu trả lời), `context_recall` (độ bao phủ ngữ cảnh), `context_precision` (độ chính xác ngữ cảnh)
4. In bảng so sánh: điểm số V1 so với V2 cho từng chỉ số
5. Lưu kết quả vào `data/ragas_report.json`

**Sản phẩm bàn giao:** Điểm faithfulness ≥ 0.8 cho ít nhất một phiên bản prompt.

**Mẫu mã nguồn chính:**
```python
import warnings; warnings.filterwarnings("ignore")
from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision

sample = SingleTurnSample(
    user_input="What is RAG?",
    response="RAG combines LLMs with retrieval.",
    retrieved_contexts=["RAG is Retrieval-Augmented Generation..."],
    reference="RAG augments LLMs with external knowledge.",
)
dataset = EvaluationDataset(samples=[sample])
result  = evaluate(dataset, metrics=[faithfulness], llm=llm_eval, embeddings=emb_eval)
# result['faithfulness'] → danh sách các số thực cho từng mẫu
import numpy as np
mean_faith = float(np.mean(result['faithfulness']))
```

---

### ✅ Nhiệm vụ 4 — Trình xác thực Guardrails AI (25 điểm)

**Mục tiêu:** Bảo vệ hệ thống RAG của bạn bằng các trình xác thực tùy chỉnh.

**Những gì cần triển khai trong `04_guardrails_validator.py`:**

**Trình xác thực A — Phát hiện PII:**
1. Tạo một lớp con `Validator` tùy chỉnh được gắn decorator `@register_validator`
2. Sử dụng regex để phát hiện: email, số điện thoại (Mỹ), số an sinh xã hội (SSN), số thẻ tín dụng
3. Khi phát hiện → Trả về `FailResult(fix_value="[REDACTED]")` với `on_fail=OnFailAction.FIX`
4. Kiểm tra trên 5+ chuỗi giả lập (chuỗi sạch, email, điện thoại, SSN, thẻ tín dụng)

**Trình xác thực B — Định dạng JSON:**
1. Tạo trình xác thực thứ hai để kiểm tra xem đầu ra có phải là JSON hợp lệ không
2. Triển khai tính năng tự động sửa lỗi (auto-repair): loại bỏ markdown fences, sửa dấu nháy đơn, loại bỏ dấu phẩy thừa ở cuối
3. Nếu sửa lỗi thành công → Trả về `PassResult(value_override=repaired)`
4. Nếu sửa lỗi thất bại → Trả về `FailResult(fix_value=json.dumps({"error": "...", "raw": "..."}))`
5. Kiểm tra trên 4+ trường hợp (JSON hợp lệ, có markdown fence, dùng nháy đơn, bị lỗi cấu trúc)

**Mẫu mã nguồn chính:**
```python
from guardrails import Guard, OnFailAction, Validator, register_validator
from guardrails.validators import PassResult, FailResult

@register_validator(name="custom/my-validator", data_type="string")
class MyValidator(Validator):
    def validate(self, value, metadata):
        if is_bad(value):
            return FailResult(error_message="...", fix_value="safe_output")
        return PassResult()

guard = Guard().use(MyValidator(on_fail=OnFailAction.FIX))
result = guard.validate(some_text)
print(result.validation_passed, result.validated_output)
```

---

## Chạy bài Lab

### Chạy từng bước riêng lẻ:
```bash
python 01_langsmith_rag_pipeline.py   # Bước 1
python 02_prompt_hub_ab_routing.py    # Bước 2
python 03_ragas_evaluation.py         # Bước 3 (~15-20 phút)
python 04_guardrails_validator.py     # Bước 4
```

### Chạy tất cả các bước:
```bash
python run_all.py
```

### Chạy một bước cụ thể:
```bash
python run_all.py --step 3
```

---

## 📤 Hướng dẫn nộp bài

Bạn sẽ nộp bài thông qua một **kho lưu trữ GitHub công khai (public GitHub repository)** chứa mã nguồn của bạn **và** một thư mục `evidence/` chứa các ảnh chụp màn hình và nhật ký (logs) theo yêu cầu.

### Bước 1 — Tạo kho lưu trữ của bạn

```bash
git init
git remote add origin https://github.com/<tên-người-dùng-của-bạn>/day22-langsmith-lab.git
```

Thêm tệp `.gitignore` để loại trừ `.env` và `__pycache__`:
```
.env
__pycache__/
*.pyc
.DS_Store
```

### Bước 2 — Thu thập bằng chứng trong quá trình chạy

Khi bạn hoàn thành mỗi bước, hãy lưu bằng chứng vào thư mục `evidence/` bên trong kho lưu trữ của bạn:

```
evidence/
├── 01_langsmith_traces.png        # Giao diện LangSmith hiển thị ≥ 50 vết (Bước 1)
├── 02_prompt_hub.png              # Giao diện Prompt Hub hiển thị 2 phiên bản prompt (Bước 2)
├── 02_ab_routing_log.txt          # Đầu ra console hiển thị điều hướng v1/v2 cho mỗi truy vấn
├── 03_ragas_scores.png            # Ảnh chụp màn hình bảng so sánh in ra console
├── 03_ragas_report.json           # Bản sao của tệp data/ragas_report.json
├── 04_pii_demo_log.txt            # Đầu ra console của các trường hợp kiểm thử phát hiện PII
├── 04_json_demo_log.txt           # Đầu ra console của các trường hợp kiểm thử sửa lỗi JSON
└── README.md                      # (tùy chọn) các ghi chú ngắn gọn về kết quả của bạn
```

### Cách lưu đầu ra console vào tệp log

```bash
# Chuyển hướng đầu ra đồng thời vẫn in ra màn hình
python 02_prompt_hub_ab_routing.py | tee evidence/02_ab_routing_log.txt
python 04_guardrails_validator.py  | tee evidence/04_pii_demo_log.txt
```

### Những ảnh chụp màn hình cần thực hiện

| Ảnh chụp | Nội dung cần hiển thị |
|---|---|
| `01_langsmith_traces.png` | Bảng điều khiển LangSmith → dự án của bạn → tab **Run**, hiển thị ≥ 50 vết với dữ liệu vào/ra rõ ràng |
| `02_prompt_hub.png` | Tab LangSmith **Prompt Hub** hiển thị cả `rag-prompt-v1` và `rag-prompt-v2` kèm số phiên bản |
| `03_ragas_scores.png` | Đầu ra terminal hiển thị bảng so sánh chỉ số V1 và V2 + dòng chữ "✅ Target met" |

> 💡 Trên Mac: `Cmd+Shift+4` để chụp một phần màn hình. Trên Windows: `Win+Shift+S`. Trên Linux: `gnome-screenshot -a` hoặc `Flameshot`.

### Bước 3 — Đẩy mọi thứ lên GitHub

```bash
# Sao chép báo cáo RAGAS của bạn vào thư mục evidence/
cp data/ragas_report.json evidence/03_ragas_report.json

git add .
git commit -m "Nộp bài lab Day22: LangSmith + Prompt Versioning + RAGAS + Guardrails"
git push origin main
```

### Bước 4 — Nộp bài

Nộp các thông tin sau lên cổng thông tin khóa học / Google Form:

1. **URL kho lưu trữ GitHub** — ví dụ: `https://github.com/yourname/day22-langsmith-lab`
2. **URL dự án LangSmith** — ví dụ: `https://smith.langchain.com/o/<org-id>/projects/p/<project-id>`
3. Xác nhận thư mục `evidence/` tồn tại trong repo với đầy đủ các tệp yêu cầu

> ⚠️ **Tuyệt đối không commit tệp `.env` hoặc dán API keys vào mã nguồn.** Vi phạm sẽ bị trừ ngay −10 điểm.

---

## Các sản phẩm bàn giao dự kiến (Expected Deliverables)

| Sản phẩm | Vị trí |
|---|---|
| LangSmith ≥ 100 vết (traces) | `evidence/01_langsmith_traces.png` + URL trực tiếp |
| Prompt Hub 2 phiên bản | `evidence/02_prompt_hub.png` |
| Nhật ký điều hướng A/B | `evidence/02_ab_routing_log.txt` |
| Báo cáo RAGAS (faithfulness ≥ 0.8) | `evidence/03_ragas_report.json` + `evidence/03_ragas_scores.png` |
| Nhật ký demo Guardrails | `evidence/04_pii_demo_log.txt` + `evidence/04_json_demo_log.txt` |

---

## Chấm điểm (Grading)

Xem tệp `rubric.md` để biết tiêu chí chấm điểm chi tiết.

---

## Mẹo (Tips)

- **LangSmith traces**: Hãy chắc chắn rằng `LANGCHAIN_TRACING_V2=true` được thiết lập trước khi import LangChain.
- **RAGAS chạy chậm**: Chạy 50 mẫu × 4 chỉ số mất khoảng 15-20 phút; hãy bắt đầu sớm.
- **Chia đoạn văn bản quan trọng**: Hãy thử `chunk_size=500` với `chunk_overlap=50` làm cơ sở ban đầu.
- **Faithfulness > 0.8**: Đảm bảo các ngữ cảnh được truy xuất thực sự chứa câu trả lời; giảm `chunk_size` nếu cần.
- **Guardrails on_fail**: Truyền `on_fail=OnFailAction.FIX` vào **hàm khởi tạo của validator**, không phải vào `Guard.use()`.

---

## Tham khảo (References)

- [Tài liệu LangSmith](https://docs.smith.langchain.com/)
- [LangChain LCEL](https://python.langchain.com/docs/expression_language/)
- [Tài liệu RAGAS](https://docs.ragas.io/)
- [Tài liệu Guardrails AI](https://www.guardrailsai.com/docs)
- [FAISS](https://github.com/facebookresearch/faiss)
