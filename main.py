from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from nutrition_pipeline_advanced import NutritionPipelineAdvanced

app = FastAPI(title="Nutrition Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo pipeline
pipeline = NutritionPipelineAdvanced()

# Models
class FoodInput(BaseModel):
    text: str
    user_id: Optional[str] = "default"

class UpdateQuantity(BaseModel):
    food_name: str
    new_quantity: int
    new_unit: Optional[str] = None

# Routes
@app.get("/")
def read_root():
    return {"message": "Nutrition Chatbot API", "status": "running"}

@app.post("/analyze")
async def analyze_food(input: FoodInput):
    """Phân tích món ăn từ text"""
    try:
        result = pipeline.process_input(input.text)
        
        return {
            "success": True,
            "analysis": result["response"],
            "data": {
                "foods": result["foods"],
                "meal_summary": result["meal_summary"],
                "memory_summary": result["memory_summary"],
                "daily_totals": result["daily_totals"],
                "processing_method": result.get("processing_method"),
                "deepseek_used": result.get("deepseek_used"),
                "deepseek_success": result.get("deepseek_success"),
                "deepseek_error": result.get("deepseek_error"),
                "deepseek_suggestions": result.get("deepseek_suggestions", [])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """Lấy thống kê hiện tại"""
    return {
        "success": True,
        "statistics": pipeline.get_statistics()
    }

@app.post("/reset-daily")
async def reset_daily():
    """Reset tổng ngày"""
    pipeline.reset_daily()
    return {"success": True, "message": "Đã reset tổng ngày"}

@app.post("/reset-memory")
async def reset_memory():
    """Reset bộ nhớ"""
    pipeline.clear_memory()
    return {"success": True, "message": "Đã xóa bộ nhớ"}

@app.post("/update-quantity")
async def update_quantity(update: UpdateQuantity):
    """Cập nhật số lượng món ăn"""
    # Tìm trong memory và cập nhật
    success = pipeline.memory.update_food_quantity(
        update.food_name,
        update.new_quantity,
        update.new_unit
    )
    
    if success:
        return {"success": True, "message": "Đã cập nhật số lượng"}
    else:
        return {"success": False, "message": "Không tìm thấy món ăn để cập nhật"}

# Test endpoints
@app.get("/test-samples")
async def test_samples():
    """Test với các mẫu input"""
    test_cases = [
        "2 bat com trang va 1 dia suon nuong",
        "hôm nay ăn 1 tô phở bò và 1 ly cafe sữa",
        "200g thit bo va 150g com",
        "3 trung chien va 1 banh mi",
        "1 to bun bo hue",
        "ăn sáng 2 quả trứng luộc",
        "uống 500ml nước cam ép"
    ]
    
    results = []
    for test in test_cases:
        try:
            result = pipeline.process_input(test)
            results.append({
                "input": test,
                "foods_found": len(result["foods"]),
                "calories": result["meal_summary"]["calories"]
            })
        except Exception as e:
            results.append({
                "input": test,
                "error": str(e)
            })
    
    return {"test_results": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
