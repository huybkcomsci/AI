#!/usr/bin/env python3
"""
Test script for Hybrid Nutrition Pipeline
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nutrition_pipeline_hybrid import NutritionPipelineHybrid
from test_cases_extended import EXTENDED_TEST_CASES

def test_hybrid_pipeline():
    print("🧪 TESTING HYBRID PIPELINE (Local + DeepSeek)")
    print("=" * 60)
    
    pipeline = NutritionPipelineHybrid()
    
    # Chọn các test cases phức tạp
    complex_cases = [
        ("ăn nhậu với 3 chai bia, lẩu thái, gà nướng", "Nhậu nhiều món"),
        ("tiệc sinh nhật có bánh kem, nước ngọt, snack", "Tiệc phức tạp"),
        ("hôm nay ăn kiêng: ức gà 150g, salad, khoai lang", "Ăn kiêng"),
        ("đi tập gym: 5 quả trứng, 200g ức gà, 1 quả chuối", "Thể hình"),
        ("bệnh nhân tiểu đường: cơm gạo lứt, rau luộc, cá hấp", "Bệnh lý"),
        ("trẻ em: sữa, cháo thịt bằm, trái cây nghiền", "Trẻ em"),
        ("ăn vặt: 1 gói bim bim, 1 chai coca, 2 cái kẹo", "Ăn vặt"),
        ("buffet: sushi, hải sản, thịt nướng, tráng miệng", "Buffet"),
        ("combo 1: phở bò + trà đá + nem rán", "Combo"),
        ("ăn linh tinh vài món không biết tên", "Mơ hồ")
    ]
    
    print("\n🔍 Testing complex cases that should trigger DeepSeek:")
    print("=" * 60)
    
    deepseek_count = 0
    total_cases = len(complex_cases)
    
    for i, (input_text, description) in enumerate(complex_cases, 1):
        print(f"\nTest {i}: {description}")
        print(f"Input: '{input_text}'")
        
        result = pipeline.process_input(input_text)
        
        processing_method = result.get("processing_method", "unknown")
        deepseek_used = result.get("deepseek_used", False)
        foods = result.get("foods", [])
        
        print(f"  Processing: {processing_method}")
        print(f"  DeepSeek used: {'✅' if deepseek_used else '❌'}")
        print(f"  Foods detected: {len(foods)}")
        
        for food in foods:
            name = food.get('food_name', 'Unknown')
            quantity = food.get('quantity_info', {}).get('amount', 0)
            unit = food.get('quantity_info', {}).get('unit', '')
            calories = food.get('nutrition', {}).get('calories', 0)
            print(f"    - {name}: {quantity} {unit} ({calories:.0f} kcal)")
        
        if deepseek_used:
            deepseek_count += 1
            
            if result.get("deepseek_success"):
                analysis = result.get("deepseek_analysis", "")
                if analysis and len(analysis) < 200:
                    print(f"  DeepSeek analysis: {analysis[:200]}...")
                
                suggestions = result.get("deepseek_suggestions", [])
                if suggestions:
                    print(f"  Suggestions: {suggestions[:2]}")
            else:
                print(f"  DeepSeek error: {result.get('deepseek_error', 'Unknown')}")
    
    print(f"\n📊 Summary: DeepSeek triggered in {deepseek_count}/{total_cases} cases ({deepseek_count/total_cases*100:.0f}%)")
    
    # Test thêm với các cases đơn giản
    print("\n\n🔍 Testing simple cases (should use local processing):")
    print("=" * 60)
    
    simple_cases = [
        ("2 bat com", "Cơm đơn giản"),
        ("1 to pho bo", "Phở đơn giản"),
        ("200g thit bo", "Thịt đơn giản"),
        ("3 qua trung", "Trứng đơn giản"),
        ("1 ly nuoc cam", "Nước cam đơn giản")
    ]
    
    for i, (input_text, description) in enumerate(simple_cases, 1):
        print(f"\nTest {i}: {description}")
        print(f"Input: '{input_text}'")
        
        result = pipeline.process_input(input_text)
        deepseek_used = result.get("deepseek_used", False)
        
        print(f"  DeepSeek used: {'⚠️ (unexpected)' if deepseek_used else '✅ (expected local)'}")
        print(f"  Foods: {len(result.get('foods', []))}")
        print(f"  Calories: {result.get('meal_summary', {}).get('calories', 0):.0f} kcal")
    
    # Get final statistics
    stats = pipeline.get_statistics()
    print(f"\n📈 Final statistics:")
    print(f"  Daily calories: {stats['daily_totals']['calories']:.0f} kcal")
    print(f"  Total foods today: {len(stats.get('memory_summary', {}).get('food_counts', {}))}")
    print(f"  DeepSeek available: {stats.get('deepseek_available', False)}")

if __name__ == "__main__":
    test_hybrid_pipeline()