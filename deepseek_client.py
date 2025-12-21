import json
import re
from typing import Any, Dict, List, Optional

import requests

from config import Config


SYSTEM_PROMPT = """
Bạn là trợ lý dinh dưỡng. Hãy trích xuất các món ăn/đồ uống từ câu tiếng Việt (có thể kèm tiếng Anh) và đề xuất thêm dữ liệu để lưu vào DB (alias, canonicalName...).
Luôn trả về đúng JSON với cấu trúc:
{
  "foods": [
    {
      "food_name": "tên món đã chuẩn hóa ngắn gọn (trùng canonicalName nếu có)",
      "canonicalName": "tên chuẩn để lưu DB; nếu không chắc, lặp lại food_name",
      "alias": "cách gọi trong câu gốc hoặc biến thể phổ biến nhất",
      "aliases": ["các cách viết khác nếu có"],
      "category": "rice|noodle|bread|drink|meat|fish|snack|fruit|veggie|custom",
      "quantity": { "amount": number, "unit": "đơn vị (dùng 'phần' nếu không rõ)", "confidence": 0.0-1.0 },
      "confidence": 0.0-1.0,
      "nutrition_hint": {
        "calories_per_100g": number,
        "carbs_per_100g": number,
        "sugar_per_100g": number,
        "protein_per_100g": number,
        "fat_per_100g": number,
        "fiber_per_100g": number
      }
    }
  ],
  "analysis": "tóm tắt ngắn gọn về bữa ăn (tiếng Việt)",
  "suggestions": ["mẹo cải thiện sức khỏe/dinh dưỡng ngắn gọn"]
}
Ghi nhớ:
- Luôn điền canonicalName và alias để hỗ trợ lưu DB (giữ lại dấu tiếng Việt nếu có).
- nutrition_hint là ước lượng theo 100g/100ml; nếu không biết có thể để 0.
- Chỉ trả về JSON, không thêm giải thích khác.
"""


class DeepSeekClient:
    """Client đơn giản gọi DeepSeek API để trích xuất món ăn."""

    def __init__(self) -> None:
        self.api_key = Config.DEEPSEEK_API_KEY
        self.base_url = Config.DEEPSEEK_BASE_URL.rstrip("/")
        self.model = Config.MODEL
        self.temperature = Config.TEMPERATURE
        self.max_tokens = Config.MAX_TOKENS
        self.timeout = Config.REQUEST_TIMEOUT

    def is_available(self) -> bool:
        return bool(self.api_key)

    def analyze(self, user_input: str) -> Dict[str, Any]:
        """Gửi câu người dùng tới DeepSeek và cố gắng parse JSON."""
        if not self.is_available():
            return {
                "success": False,
                "error": "DeepSeek API key not configured",
                "foods": [],
                "analysis": "",
                "suggestions": [],
                "raw_content": "",
            }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": user_input},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network errors are runtime issues
            return {
                "success": False,
                "error": str(exc),
                "foods": [],
                "analysis": "",
                "suggestions": [],
                "raw_content": "",
            }

        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        parsed = self._extract_json(content)

        return {
            "success": parsed is not None,
            "error": None if parsed is not None else "Cannot parse DeepSeek JSON response",
            "foods": parsed.get("foods", []) if parsed else [],
            "analysis": parsed.get("analysis", "") if parsed else "",
            "suggestions": parsed.get("suggestions", []) if parsed else [],
            "raw_content": content,
        }

    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Tìm và parse JSON trong nội dung trả về."""
        if not content:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

        return None
