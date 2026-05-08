# 📋 Tiêu chí chấm điểm (Lab Rubric) — Ngày 22: LangSmith + Prompt Versioning

**Tổng điểm: 100 điểm**  
**Sản phẩm bàn giao:** Kho lưu trữ GitHub công khai với mã nguồn + thư mục `evidence/` + URL dự án LangSmith

---

## Tổng quan điểm số (Scoring Overview)

| Nhiệm vụ | Điểm tối đa | Sản phẩm bàn giao chính |
|------|-----------|-----------------|
| Nhiệm vụ 1 — LangSmith RAG Pipeline | 25 điểm | ≥ 50 vết (traces) trong LangSmith |
| Nhiệm vụ 2 — Prompt Hub & Điều hướng A/B | 25 điểm | 2 phiên bản Hub + thêm 50 vết |
| Nhiệm vụ 3 — Đánh giá bằng RAGAS | 25 điểm | Báo cáo JSON, faithfulness ≥ 0.8 |
| Nhiệm vụ 4 — Trình xác thực Guardrails | 25 điểm | PII được chặn, JSON được sửa |

---

## Nhiệm vụ 1 — LangSmith RAG Pipeline (25 điểm)

### Tiêu chí

| # | Tiêu chí | Điểm |
|---|-----------|--------|
| 1.1 | Cơ sở tri thức được chia đoạn và lập chỉ mục với FAISS chính xác | 5 điểm |
| 1.2 | Chuỗi RAG được xây dựng bằng LangChain (retriever → prompt → LLM → parser) | 5 điểm |
| 1.3 | Decorator `@traceable` được áp dụng; ít nhất 50 vết hiển thị trong giao diện LangSmith | 10 điểm |
| 1.4 | Các vết LangSmith chứa câu hỏi đầu vào, ngữ cảnh được truy xuất và câu trả lời của LLM | 5 điểm |

### Điểm trừ (Deductions)

| Lỗi | Hình phạt |
|-------|---------|
| Ít hơn 50 vết trong LangSmith | −5 điểm |
| Các vết thiếu ngữ cảnh được truy xuất (sai cấu trúc chuỗi) | −3 điểm |
| API keys được commit cứng vào mã nguồn | −10 điểm |
| `LANGCHAIN_TRACING_V2` không được bật → không có vết | −10 điểm |

---

## Nhiệm vụ 2 — Prompt Hub & Điều hướng A/B (25 điểm)

### Tiêu chí

| # | Tiêu chí | Điểm |
|---|-----------|--------|
| 2.1 | Viết hai prompt hệ thống khác biệt về mặt ngữ nghĩa | 5 điểm |
| 2.2 | Cả hai prompt được đẩy lên LangSmith Prompt Hub (hiển thị trong UI) | 8 điểm |
| 2.3 | Các prompt được kéo (pull) từ Hub (không chỉ sử dụng cục bộ) | 4 điểm |
| 2.4 | Điều hướng A/B là **xác định (deterministic)** — cùng một `request_id` luôn ánh xạ đến cùng một phiên bản | 5 điểm |
| 2.5 | Cả hai phiên bản đều nhận được truy vấn; console log hiển thị nhãn phiên bản cho mỗi truy vấn | 3 điểm |

### Điểm trừ (Deductions)

| Lỗi | Hình phạt |
|-------|---------|
| Chỉ có 1 phiên bản prompt trong Hub | −8 điểm |
| Điều hướng ngẫu nhiên (không xác định) | −5 điểm |
| Các prompt không được kéo từ Hub (bị bỏ qua) | −4 điểm |
| Không có nhãn phiên bản trong nhật ký (logs) | −3 điểm |

---

## Nhiệm vụ 3 — Đánh giá bằng RAGAS (25 điểm)

### Tiêu chí

| # | Tiêu chí | Điểm |
|---|-----------|--------|
| 3.1 | Tất cả 50 cặp QA được chạy qua **cả hai** phiên bản prompt | 5 điểm |
| 3.2 | `EvaluationDataset` được xây dựng với các trường `SingleTurnSample` chính xác | 5 điểm |
| 3.3 | Tính toán đủ 4 chỉ số: `faithfulness`, `answer_relevancy`, `context_recall`, `context_precision` | 8 điểm |
| 3.4 | Faithfulness ≥ 0.8 cho ít nhất một phiên bản prompt | 5 điểm |
| 3.5 | `data/ragas_report.json` được lưu với điểm số của V1 và V2 | 2 điểm |

### Điểm trừ (Deductions)

| Lỗi | Hình phạt |
|-------|---------|
| Ít hơn 50 cặp QA được đánh giá | −1 điểm mỗi 5 cặp thiếu |
| Chỉ có 1 phiên bản prompt được đánh giá | −5 điểm |
| Thiếu bất kỳ chỉ số nào trong 4 chỉ số RAGAS | −2 điểm mỗi chỉ số thiếu |
| Faithfulness < 0.8 cho cả hai phiên bản | −5 điểm |
| Không có tệp báo cáo được lưu | −2 điểm |

### Điểm thưởng (Bonus)

| Thưởng | Điểm |
|-------|--------|
| Faithfulness ≥ 0.9 cho cả hai phiên bản prompt | +3 điểm |
| Nhận xét phân tích giải thích lý do tại sao V1 hoặc V2 có điểm cao hơn | +2 điểm |

---

## Nhiệm vụ 4 — Trình xác thực Guardrails (25 điểm)

### Phát hiện PII (13 điểm)

| # | Tiêu chí | Điểm |
|---|-----------|--------|
| 4.1 | Trình xác thực tùy chỉnh được tạo bằng `@register_validator` | 3 điểm |
| 4.2 | Phát hiện ít nhất 3 loại PII (email, điện thoại, SSN, hoặc thẻ tín dụng) | 5 điểm |
| 4.3 | Sử dụng `on_fail=OnFailAction.FIX`; đầu ra bị chặn được thay thế bằng chuỗi an toàn | 3 điểm |
| 4.4 | Được trình bày trên 5+ trường hợp kiểm thử (bao gồm chuỗi sạch và nhiều loại PII) | 2 điểm |

### Định dạng JSON (12 điểm)

| # | Tiêu chí | Điểm |
|---|-----------|--------|
| 4.5 | Trình xác thực tùy chỉnh được tạo để kiểm tra khả năng phân tích JSON | 3 điểm |
| 4.6 | Triển khai tự động sửa lỗi (ít nhất 2 trong số: loại bỏ fence, sửa nháy đơn, dấu phẩy thừa) | 5 điểm |
| 4.7 | Trả về JSON lỗi dự phòng khi sửa lỗi thất bại | 2 điểm |
| 4.8 | Được trình bày trên 4+ trường hợp kiểm thử (hợp lệ, có fence/sai định dạng, bị hỏng) | 2 điểm |

### Điểm trừ (Deductions)

| Lỗi | Hình phạt |
|-------|---------|
| Sử dụng trình xác thực Hub có sẵn thay vì tự triển khai | −5 điểm |
| `on_fail` được truyền vào `Guard.use()` thay vì hàm khởi tạo trình xác thực | −3 điểm |
| Phát hiện PII không sử dụng regex (chỉ so khớp chuỗi) | −3 điểm |

---

## Chất lượng Bằng chứng & Nộp bài (tối đa +5 điểm)

| Tiêu chí | Điểm |
|-----------|--------|
| Đầy đủ 7 tệp bằng chứng yêu cầu và được dán nhãn rõ ràng | +3 điểm |
| URL dự án LangSmith được nộp và có thể truy cập công khai | +1 điểm |
| `evidence/README.md` với phân tích ngắn gọn về kết quả V1 và V2 | +1 điểm |

---

## Điểm thưởng Chất lượng Mã nguồn (tối đa +5 điểm)

| Tiêu chí | Điểm |
|-----------|--------|
| Mã nguồn sạch, cấu trúc tốt với đầy đủ docstrings | +2 điểm |
| Tất cả các bước hoạt động qua `run_all.py` mà không cần chỉnh sửa | +2 điểm |
| Xử lý lỗi và các phương án dự phòng được triển khai tốt | +1 điểm |

---

## Danh sách kiểm tra trước khi nộp (Submission Checklist)

**Các tệp mã nguồn — tất cả phải chạy không lỗi:**
- [ ] `01_langsmith_rag_pipeline.py`
- [ ] `02_prompt_hub_ab_routing.py`
- [ ] `03_ragas_evaluation.py`
- [ ] `04_guardrails_validator.py`
- [ ] `data/ragas_report.json` — tồn tại và chứa điểm số V1 + V2

**Thư mục bằng chứng (Evidence) — tất cả đều bắt buộc:**
- [ ] `evidence/01_langsmith_traces.png` — LangSmith UI với ≥ 50 vết hiển thị
- [ ] `evidence/02_prompt_hub.png` — Prompt Hub UI hiển thị 2 phiên bản prompt có tên
- [ ] `evidence/02_ab_routing_log.txt` — console log của điều hướng A/B (50 truy vấn, nhãn v1/v2)
- [ ] `evidence/03_ragas_scores.png` — đầu ra terminal với bảng so sánh V1 và V2
- [ ] `evidence/03_ragas_report.json` — bản sao của `data/ragas_report.json`
- [ ] `evidence/04_pii_demo_log.txt` — đầu ra console của các trường hợp kiểm thử PII
- [ ] `evidence/04_json_demo_log.txt` — đầu ra console của các trường hợp kiểm thử sửa lỗi JSON

**Nộp bài:**
- [ ] URL kho lưu trữ GitHub công khai đã nộp
- [ ] URL dự án LangSmith đã nộp (hiển thị tổng cộng ≥ 100 vết)
- [ ] Không commit tệp `.env`; không có API keys trong mã nguồn

**Hình phạt: −10 điểm nếu tìm thấy API keys trong mã nguồn đã commit.**
