import re
import json
from guardrails import Guard, OnFailAction
from guardrails.validator_base import (
    Validator,
    register_validator,
    PassResult,
    FailResult,
)

# ── 1. PII Detector Validator ─────────────────────────────────────────────────

@register_validator(name="custom/pii-detector", data_type="string")
class PIIDetector(Validator):
    """
    Phát hiện và che giấu thông tin định danh cá nhân (PII).
    Hỗ trợ: Email, Điện thoại, SSN, Thẻ tín dụng.
    """

    # Các mẫu Regex để nhận diện PII
    PII_PATTERNS = {
        "EMAIL":       r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "PHONE":       r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b",
        "SSN":         r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    }

    def validate(self, value: str, metadata: dict) -> PassResult:
        """
        Kiểm tra PII; nếu thấy thì thay thế bằng [REDACTED].
        """
        redacted_text = value
        found_any = False

        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, value)
            if matches:
                found_any = True
                for match in matches:
                    redacted_text = redacted_text.replace(match, f"[{pii_type}_REDACTED]")

        if found_any:
            # Trả về kết quả đã sửa đổi (FIX)
            return FailResult(
                error_message="Phát hiện thông tin nhạy cảm!",
                fix_value=redacted_text
            )
        
        return PassResult()

# ── 2. JSON Formatter Validator ───────────────────────────────────────────────

@register_validator(name="custom/json-formatter", data_type="string")
class JSONFormatter(Validator):
    """
    Kiểm tra và tự động sửa lỗi các chuỗi JSON bị sai định dạng nhẹ.
    """

    def _repair(self, text: str) -> str:
        """Thực hiện các bước sửa lỗi cơ bản."""
        # 1. Loại bỏ khoảng trắng thừa
        text = text.strip()

        # 2. Loại bỏ markdown code fences (```json ... ```)
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$',          '', text)
        text = text.strip()

        # 3. Thay nháy đơn bằng nháy kép (lưu ý: cách này đơn giản, có thể lỗi với chuỗi phức tạp)
        text = text.replace("'", '"')

        # 4. Loại bỏ dấu phẩy thừa trước dấu đóng ngoặc
        text = re.sub(r',\s*([}\]])', r'\1', text)

        return text

    def validate(self, value: str, metadata: dict) -> PassResult:
        """Thử phân tích JSON, nếu lỗi thì thử sửa."""
        # Thử parse trực tiếp
        try:
            parsed = json.loads(value)
            return PassResult()
        except json.JSONDecodeError:
            pass

        # Thử sửa lỗi
        try:
            repaired_text = self._repair(value)
            parsed = json.loads(repaired_text)
            print(f"  🔧 Đã tự động sửa lỗi JSON thành công.")
            return FailResult(
                error_message="JSON sai định dạng, đã tự động sửa.",
                fix_value=json.dumps(parsed, indent=2)
            )
        except json.JSONDecodeError:
            # Nếu không sửa được, trả về JSON thông báo lỗi
            error_json = json.dumps({"error": "Không thể phục hồi JSON", "raw": value})
            return FailResult(
                error_message="JSON bị hỏng nặng không thể sửa.",
                fix_value=error_json
            )

# ── 3. Demo Phát hiện PII ───────────────────────────────────────────────────

def demo_pii_guard():
    print("\n" + "=" * 55)
    print("  [PII Detection Demo]")
    print("=" * 55)

    # Khởi tạo Guard với PIIDetector và chế độ tự động sửa (FIX)
    guard = Guard().use(PIIDetector(on_fail=OnFailAction.FIX))

    test_cases = [
        ("Email",       "Liên hệ John tại john.doe@example.com để biết thêm."),
        ("Điện thoại",  "Số hỗ trợ khách hàng: (555) 867-5309."),
        ("SSN",         "Số an sinh xã hội: 123-45-6789."),
        ("Thẻ tín dụng","Thanh toán qua thẻ 4532 1234 5678 9010."),
        ("Hỗn hợp",     "Email: alice@web.com, SĐT: 555-123-4567"),
        ("Sạch",        "Văn bản này không chứa thông tin nhạy cảm."),
    ]

    for label, text in test_cases:
        outcome = guard.validate(text)
        print(f"\n[{label}]")
        print(f"  Đầu vào: {text}")
        print(f"  Đầu ra:  {outcome.validated_output}")

# ── 4. Demo Định dạng JSON ──────────────────────────────────────────────────

def demo_json_guard():
    print("\n" + "=" * 55)
    print("  [JSON Formatting Demo]")
    print("=" * 55)

    # Khởi tạo Guard với JSONFormatter
    guard = Guard().use(JSONFormatter(on_fail=OnFailAction.FIX))

    test_cases = [
        ("Hợp lệ",          '{"name": "Alice", "age": 30}'),
        ("Có Markdown",     '```json\n{"name": "Bob"}\n```'),
        ("Dùng nháy đơn",   "{'name': 'Charlie', 'score': 95}"),
        ("Dấu phẩy thừa",   '{"key": "value",}'),
        ("Bị hỏng nặng",    "Đây không phải JSON: {abc]"),
    ]

    for label, text in test_cases:
        outcome = guard.validate(text)
        status = "✅ Hợp lệ/Đã sửa" if outcome.validation_passed else "❌ Thất bại"
        print(f"\n[{label}] {status}")
        print(f"  Đầu vào: {text}")
        print(f"  Đầu ra:  {outcome.validated_output}")

# ── 5. Main ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Step 4: Guardrails AI Validators")
    print("=" * 60)

    demo_pii_guard()
    demo_json_guard()

    print("\n✅ Hoàn thành Nhiệm vụ 4!")

if __name__ == "__main__":
    main()
