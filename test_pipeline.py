#!/usr/bin/env python3
"""
Test script for Nutrition Pipeline
"""
import sys
import os

# Thêm thư mục hiện tại vào path để import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import từ module local
try:
    from nutrition_pipeline_advanced import NutritionPipelineAdvanced
    from vietnamese_foods_extended import (
        VIETNAMESE_FOODS_NUTRITION,
        UNIT_CONVERSION,
        FoodNameMatcher,
        QuantityParser,
        FoodExtractor,
        estimate_weight,
        calculate_nutrition
    )
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the 'datn' directory")
    IMPORT_SUCCESS = False

def test_pipeline():
    if not IMPORT_SUCCESS:
        print("❌ Cannot import required modules. Please check the directory structure.")
        return
    
    print("🧪 TESTING NUTRITION PIPELINE")
    print("=" * 60)
    
    pipeline = NutritionPipelineAdvanced()
    
    test_cases = [
        ("2 bat com trang", "Chính tả sai"),
        ("1 to pho bo", "Không dấu"),
        ("hôm nay ăn một tô phở bò", "Có từ thừa"),
        ("150g thịt bò", "Định lượng chính xác"),
        ("một bát cơm", "Số bằng chữ"),
        ("2 ly cafe sữa", "Đơn vị tương đối"),
        ("1 tô phở và 1 ly nước cam", "Nhiều món"),
        ("sáng ăn 2 trứng, trưa ăn 1 bát cơm với thịt", "Nhiều món với thời gian"),
    ]
    
    for i, (input_text, description) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {description}")
        print(f"Input: '{input_text}'")
        
        try:
            result = pipeline.process_input(input_text)
            
            print(f"✓ Nhận diện: {len(result['foods'])} món")
            
            for food in result['foods']:
                food_name = food.get('food_name', 'Unknown')
                quantity = food.get('quantity_info', {}).get('amount', 0)
                unit = food.get('quantity_info', {}).get('unit', '')
                print(f"  - {food_name}: {quantity} {unit}")
            
            print(f"✓ Calories: {result['meal_summary']['calories']:.0f} kcal")
            
            if i == 3:  # Sau 3 lần test
                stats = pipeline.get_statistics()
                print(f"\n📊 Thống kê 3 hội thoại gần nhất:")
                print(f"  Total calories: {stats['memory_summary']['total_nutrition']['calories']:.0f}")
                print(f"  Số món khác nhau: {len(stats['memory_summary']['food_counts'])}")
                
        except Exception as e:
            print(f"✗ Lỗi: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ TEST HOÀN TẤT")

if __name__ == "__main__":
    test_pipeline()