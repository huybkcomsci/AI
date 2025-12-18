# Nutrition Chat API (FastAPI)

API phân tích bữa ăn gắn với bệnh nhân (`patientId` bắt buộc), lưu ngày ăn uống vào SQLite, hỗ trợ chỉnh sửa món/khẩu phần và xem lịch sử.

## Chạy nhanh
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

## Lưu trữ
- SQLite file: `nutrition.db` tự tạo tại thư mục dự án.
- Bảng `daily_logs`: `patient_id`, `day (YYYY-MM-DD)`, `daily_totals`, `meals/entries`, `last_updated`. Index: (patient_id, day). `entryId` unique trong phạm vi patient.
- Workflow học thêm (DeepSeek → duyệt → DB chính thức):
  - `pending_foods`: món/alias do DeepSeek gợi ý, chờ admin duyệt.
  - `learned_aliases`: (đã duyệt) map `alias` → `canonical_name` để tăng khả năng match local.
  - `learned_foods`: (đã duyệt) món mới tối thiểu (tên + aliases + metadata) để lần sau nhận diện không cần DeepSeek.

## Endpoints chính
- `GET /` — health check.

- `POST /analyze` — phân tích text cho 1 bệnh nhân, tạo entry mới trong ngày (`dateKey`).
  ```json
  {
    "patientId": "patient_001",
    "userId": "mobile",
    "text": "2 tô bún chả và 1 ly sữa đậu nành",
    "dateKey": "2025-12-15",
    "locale": "vi-VN"
  }
  ```
  Trả: `{ success, data: { foods[], mealSummary }, meta: { patientId, requestId(entryId), createdAt } }`.

- `POST /update-quantity` — chỉnh khẩu phần/đơn vị món (tìm món theo tên trong ngày).
  ```json
  {
    "patientId": "patient_001",
    "userId": "mobile",
    "foodName": "Bún chả",
    "newQuantity": 1.5,
    "newUnit": "tô",
    "dateKey": "2025-12-15",
    "source": "inline_edit"
  }
  ```
  Trả: `{ success, data: { patientId, foodName, savedQuantity, savedUnit, ruleId } }`.

- `POST /update-food` — patch 1 món trong entry (sửa tên/khẩu phần/macro).
  ```json
  {
    "patientId": "patient_001",
    "userId": "mobile",
    "entryId": "1734260000000",
    "foodId": "tmp_1",
    "patch": {
      "foodName": "Bún chả",
      "quantityInfo": { "amount": 1.5, "unit": "tô" },
      "nutrition": { "calories": 650, "carbs": 70, "sugar": 8, "protein": 28, "fat": 22, "fiber": 4 }
    }
  }
  ```
  Trả: `{ success, data: { patientId, entryId, foodId, updatedAt } }`.

- `POST /delete-food` — xoá 1 món khỏi entry.
  ```json
  { "patientId": "patient_001", "userId": "mobile", "entryId": "1734260000000", "foodId": "tmp_1" }
  ```
  Trả: `{ success, data: { patientId, entryId, deletedFoodId, mealSummary } }`.

- `POST /confirm-meal` — xác nhận bữa (✓ Tổng bữa này), có thể gửi `finalData`.
  ```json
  {
    "patientId": "patient_001",
    "userId": "mobile",
    "entryId": "1734260000000",
    "dateKey": "2025-12-15",
    "confirmed": true,
    "finalData": { "foods": [...], "mealSummary": {...} }
  }
  ```
  Trả: `{ success, data: { patientId, entryId, status, confirmedAt } }`.

- `GET /history?patientId=patient_001&from=2025-12-01&to=2025-12-15` — lịch sử ăn uống trong khoảng ngày. Nếu patient chưa tồn tại, hệ thống tự tạo patient rỗng và trả về `days: {}`.
  Trả: `{ success, data: { patientId, days: { "YYYY-MM-DD": { totals, entries[] } } } }`.

- `GET /foods?q=&limit=&offset=` — danh sách món trong database tra cứu + danh sách đơn vị (units).

- `GET /analytics/food-trends?from=YYYY-MM-DD&to=YYYY-MM-DD&limit=20` — thống kê xu hướng món ăn gộp tất cả bệnh nhân (top foods + trend theo ngày).

### Admin (duyệt món DeepSeek)
> Chưa có auth, bạn nên đặt phía sau gateway/VPN nếu dùng thật.

- `GET /admin/pending-foods?status=pending&action=alias&q=&limit=&offset=` — xem bảng tạm món/alias chờ duyệt.

- `POST /admin/review-pending-food` — duyệt/loại món từ bảng tạm.
  ```json
  { "pendingId": 1, "decision": "approve", "action": "alias" }
  ```
  Duyệt món mới (có thể gửi `foodData` để set macro/category):
  ```json
  { "pendingId": 2, "decision": "approve", "action": "new_food", "canonicalName": "trà sữa matcha", "foodData": { "category": "drink", "calories_per_100g": 60, "carbs_per_100g": 12, "sugar_per_100g": 10 } }
  ```

## Quy ước lỗi
```json
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "patientId is required" } }
```

## Ghi chú
- Pipeline vẫn chạy local extraction; DeepSeek chỉ bật khi có key và độ tin cậy thấp.  
- Nếu input có cụm “không đường / no sugar / unsweetened” trong cùng segment món, hệ thống sẽ ép `sugar = 0` cho món đó (và lưu cờ `noSugar` trong food object).  
- Khi DeepSeek được dùng và thành công, hệ thống sẽ lưu vào `pending_foods`; admin duyệt xong mới merge vào database tra cứu.  
- Nutrition dữ liệu/ước lượng nằm trong `vietnamese_foods_extended.py`.  
- Mọi response dùng camelCase theo spec.
