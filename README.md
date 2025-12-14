# Nutrition Chatbot API (FastAPI)

API phân tích món ăn/dinh dưỡng, có thể gọi từ React Native/Expo hoặc bất kỳ HTTP client nào. Kèm storage SQLite cho daily logs bệnh nhân.

## Chạy server nhanh
```bash
cd /Users/hus/WORKSPACE/Python/datn
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- Health: http://localhost:8000/
- Swagger: http://localhost:8000/docs
- Thiết bị thật/Expo: dùng IP LAN (Android emulator: http://10.0.2.2:8000).

## Biến môi trường
- `DEEPSEEK_API_KEY` (tùy chọn) và `DEEPSEEK_BASE_URL` nếu cần. Không có key vẫn chạy local; DeepSeek chỉ bật khi key tồn tại và độ tin cậy thấp.

## Lưu trữ (DBS)
- File SQLite: `nutrition.db` tự tạo tại thư mục dự án.
- Bảng `daily_logs` lưu: `patient_id`, `day (YYYY-MM-DD)`, `daily_totals`, `meals[]`, `last_updated`.

## Endpoints chính
- `GET /` — health check.
- `POST /analyze` — phân tích text -> foods, meal_summary, memory/daily totals, DeepSeek fallback khi cần.
  ```json
  { "text": "2 tô bún chả và 1 ly sữa đậu nành", "user_id": "optional-id" }
  ```
- `POST /update-quantity` — cập nhật món trong lần nhập gần nhất.
  ```json
  { "food_name": "bún chả", "new_quantity": 3, "new_unit": "tô" }
  ```
- `POST /reset-daily` — reset tổng ngày.
- `POST /reset-memory` — xóa bộ nhớ hội thoại gần nhất.
- `GET /statistics` — tổng hợp memory/daily/recent foods.

## Endpoints DBS (daily logs bệnh nhân)
- `GET /patients/{patientId}` hoặc `/patients/{patientId}/daily-logs` — trả toàn bộ daily_logs (mảng, rỗng nếu chưa có).
- `GET /patients/{patientId}/daily-logs/{day}` — lấy log 1 ngày; trả `{}` nếu không tồn tại.
- `POST /patients/{patientId}/daily-logs` — tạo/cập nhật log.
  ```json
  {
    "day": "2024-12-15",
    "daily_totals": { "calories": 1200, "carbs": 180, "sugar": 40, "protein": 70, "fat": 30, "fiber": 15 },
    "meals": [
      {
        "timestamp": "2024-12-15T08:00:00",
        "text": "2 bát cơm và thịt kho",
        "meal_summary": { "calories": 600, "carbs": 90, "sugar": 10, "protein": 30, "fat": 15, "fiber": 4 },
        "foods": [
          { "food_name": "cơm trắng", "quantity_info": { "amount": 2, "unit": "bát", "type": "relative", "confidence": 0.9 }, "estimated_weight_g": 320, "category": "rice" }
        ]
      }
    ],
    "last_updated": "2024-12-15T12:00:00"
  }
  ```
- `DELETE /patients/{patientId}/daily-logs/{day}` — xóa log ngày, trả `success: true/false`.

## Gọi mẫu từ client (React Native/Expo)
```ts
const API = "http://<IP>:8000";

export async function analyzeFood(text: string) {
  const res = await fetch(`${API}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, user_id: "mobile" })
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```
