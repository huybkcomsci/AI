# Nutrition Chatbot API (FastAPI)

API phục vụ phân tích món ăn/dinh dưỡng. Có thể gọi trực tiếp từ Expo React Native hoặc bất kỳ client HTTP nào.

## Khởi chạy server
```bash
cd /Users/hus/WORKSPACE/Python/datn
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- Truy cập `http://localhost:8000/` để kiểm tra health.
- Swagger UI: `http://localhost:8000/docs`.
- Nếu gọi từ thiết bị thật/Expo: dùng IP LAN thay cho `localhost` (Android emulator: `http://10.0.2.2:8000`).

## Cấu hình DeepSeek (tùy chọn)
- Đặt biến môi trường `DEEPSEEK_API_KEY` (và `DEEPSEEK_BASE_URL` nếu cần). Nếu không có key, pipeline vẫn chạy local logic; DeepSeek chỉ dùng khi key sẵn sàng và độ tin cậy thấp.

## Endpoints

### GET `/`
Health check.
- Response: `{"message": "Nutrition Chatbot API", "status": "running"}`

### POST `/analyze`
Phân tích câu nhập, trích xuất món ăn và tính dinh dưỡng.
- Request body:
```json
{
  "text": "2 tô bún chả và 1 ly sữa đậu nành",
  "user_id": "optional-id"
}
```
- Response (rút gọn ví dụ):
```json
{
  "success": true,
  "analysis": "🍽️ **PHÂN TÍCH BỮA ĂN** ...",
  "data": {
    "foods": [
      {
        "food_name": "bún chả",
        "original_text": "2 tô bún chả",
        "quantity_info": { "amount": 2, "unit": "tô", "type": "relative", "confidence": 0.9 },
        "estimated_weight_g": 880.0,
        "nutrition": {
          "calories": 968.0,
          "carbs": 158.4,
          "sugar": 26.4,
          "protein": 70.4,
          "fat": 19.2,
          "fiber": 8.8
        },
        "category": "noodle",
        "confidence": 0.9
      }
    ],
    "meal_summary": { "calories": 968.0, "carbs": 158.4, "sugar": 26.4, "protein": 70.4, "fat": 19.2, "fiber": 8.8, "food_count": 1 },
    "memory_summary": {
      "total_nutrition": { "calories": 968.0, "carbs": 158.4, "sugar": 26.4, "protein": 70.4, "fat": 19.2, "fiber": 8.8 },
      "food_counts": { "bún chả": 1 },
      "message_count": 1
    },
    "daily_totals": { "calories": 968.0, "carbs": 158.4, "sugar": 26.4, "protein": 70.4, "fat": 19.2, "fiber": 8.8 },
    "processing_method": "local",
    "deepseek_used": false,
    "deepseek_success": false,
    "deepseek_error": null,
    "deepseek_suggestions": []
  }
}
```

### POST `/update-quantity`
Cập nhật số lượng đơn vị món ăn trong lần nhập gần nhất.
- Request body:
```json
{ "food_name": "bún chả", "new_quantity": 3, "new_unit": "tô" }
```
- Response: `{"success": true, "message": "Đã cập nhật số lượng"}`

### POST `/reset-daily`
Reset tổng dinh dưỡng theo ngày.
- Response: `{"success": true, "message": "Đã reset tổng ngày"}`

### POST `/reset-memory`
Xóa bộ nhớ hội thoại gần nhất.
- Response: `{"success": true, "message": "Đã xóa bộ nhớ"}`

### GET `/statistics`
Xem thống kê hiện tại.
- Response ví dụ:
```json
{
  "success": true,
  "statistics": {
    "daily_totals": { "calories": 968.0, "carbs": 158.4, "sugar": 26.4, "protein": 70.4, "fat": 19.2, "fiber": 8.8 },
    "memory_summary": {
      "total_nutrition": { "calories": 968.0, "carbs": 158.4, "sugar": 26.4, "protein": 70.4, "fat": 19.2, "fiber": 8.8 },
      "food_counts": { "bún chả": 1 },
      "message_count": 1
    },
    "recent_foods": [
      { "timestamp": "2024-01-01T12:00:00", "food_name": "bún chả", "quantity_info": { "amount": 2, "unit": "tô", "type": "relative", "confidence": 0.9 }, "estimated_weight_g": 880.0, "nutrition": { "...": "..." }, "category": "noodle", "confidence": 0.9 }
    ]
  }
}
```

## Gợi ý client (React Native/Expo)
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
