#!/usr/bin/env python3
"""
Test runner nâng cao cho Nutrition Pipeline
"""
import sys
import os
import json
from datetime import datetime

# Thêm thư mục hiện tại vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from nutrition_pipeline_advanced import NutritionPipelineAdvanced
    from test_cases_extended import (
        get_all_test_cases,
        get_test_cases_by_group,
        get_statistics,
        get_expected_count
    )
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORT_SUCCESS = False

class AdvancedTestRunner:
    def __init__(self):
        self.pipeline = NutritionPipelineAdvanced()
        self.results = []
        self.summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total_calories": 0,
            "total_foods": 0
        }
    
    def run_single_test(self, test_input, description, expected_count=None):
        """Chạy test đơn lẻ"""
        try:
            result = self.pipeline.process_input(test_input)
            
            food_count = len(result.get('foods', []))
            calories = result.get('meal_summary', {}).get('calories', 0)
            expected = expected_count if expected_count is not None else get_expected_count(test_input)
            count_match = True if expected is None else (food_count == expected)
            
            test_result = {
                "input": test_input,
                "description": description,
                "success": count_match if expected is not None else food_count > 0,
                "food_count": food_count,
                "expected_count": expected,
                "count_match": count_match,
                "calories": calories,
                "foods": result.get('foods', []),
                "response": (
                    result.get('response', "")[:100] + "..."
                    if result.get('response') else ""
                ),
                "timestamp": datetime.now().isoformat()
            }
            
            if test_result["success"]:
                self.summary["passed"] += 1
                self.summary["total_calories"] += calories
                self.summary["total_foods"] += food_count
            else:
                self.summary["failed"] += 1
            
            self.summary["total"] += 1
            self.results.append(test_result)
            
            return test_result
            
        except Exception as e:
            error_result = {
                "input": test_input,
                "description": description,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.summary["failed"] += 1
            self.summary["total"] += 1
            self.results.append(error_result)
            return error_result
    
    def run_test_group(self, group_name):
        """Chạy test theo nhóm"""
        print(f"\n{'='*60}")
        print(f"Testing group: {group_name}")
        print(f"{'='*60}")
        
        test_cases = get_test_cases_by_group(group_name)
        
        for i, case in enumerate(test_cases):
            if len(case) == 3:
                test_input, description, expected = case
            else:
                test_input, description = case
                expected = get_expected_count(test_input)
            print(f"\nTest {i+1}/{len(test_cases)}: {description}")
            print(f"Input: '{test_input}'")
            
            result = self.run_single_test(test_input, description, expected)
            
            if result.get("success"):
                print(f"  ✅ Nhận diện: {result['food_count']} món", end="")
                if result.get("expected_count") is not None:
                    print(f" (kỳ vọng {result['expected_count']})")
                else:
                    print("")
                for food in result.get('foods', []):
                    food_name = food.get('food_name', 'Unknown')
                    quantity = food.get('quantity_info', {}).get('amount', 0)
                    unit = food.get('quantity_info', {}).get('unit', '')
                    print(f"     - {food_name}: {quantity} {unit}")
                print(f"  Calories: {result['calories']:.0f} kcal")
            else:
                expected_txt = ""
                if result.get("expected_count") is not None:
                    expected_txt = f" (kỳ vọng {result['expected_count']})"
                print(f"  ❌ Nhận diện: {result.get('food_count', 0)} món{expected_txt}")
                if "error" in result:
                    print(f"  Lỗi: {result['error']}")
    
    def run_all_tests(self, limit=None):
        """Chạy tất cả test cases"""
        print("🧪 RUNNING ALL TEST CASES")
        print("=" * 60)
        
        test_cases = get_all_test_cases()
        if limit:
            test_cases = test_cases[:limit]
        
        total = len(test_cases)
        
        for i, case in enumerate(test_cases):
            if len(case) == 3:
                test_input, description, expected = case
            else:
                test_input, description = case
                expected = get_expected_count(test_input)
            print(f"\n[{i+1}/{total}] {description}")
            print(f"Input: '{test_input}'")
            
            result = self.run_single_test(test_input, description, expected)
            
            if result.get("success"):
                expected_note = ""
                if result.get("expected_count") is not None:
                    expected_note = f" (kỳ vọng {result['expected_count']})"
                print(f"  ✅ Nhận diện {result['food_count']} món{expected_note}")
            else:
                expected_note = ""
                if result.get("expected_count") is not None:
                    expected_note = f" (kỳ vọng {result['expected_count']})"
                print(f"  ❌ Nhận diện {result.get('food_count', 0)} món{expected_note}")
        
        self.print_summary()
    
    def run_smart_test(self, sample_size=50):
        """Chạy test thông minh với mẫu đại diện"""
        print("🧠 RUNNING SMART TEST SAMPLE")
        print("=" * 60)
        
        all_cases = get_all_test_cases()
        
        # Lấy mẫu đa dạng
        samples = []
        
        # Đảm bảo có đủ từng loại
        categories = [
            ("chinh_ta", 10),
            ("dinh_luong_chinh_xac", 10),
            ("dinh_luong_tuong_doi", 10),
            ("nhieu_mon", 10),
            ("tinh_huong_thuc_te", 10)
        ]
        
        # Lấy ngẫu nhiên (đơn giản)
        import random
        random.seed(42)  # Để kết quả tái lập được
        
        if len(all_cases) > sample_size:
            samples = random.sample(all_cases, sample_size)
        else:
            samples = all_cases
        
        for i, (test_input, description) in enumerate(samples):
            print(f"\n[{i+1}/{len(samples)}] {description}")
            print(f"Input: '{test_input}'")
            
            result = self.run_single_test(test_input, description)
            
            if result.get("success"):
                print(f"  ✅ {result['food_count']} món, {result['calories']:.0f} kcal")
            else:
                print(f"  ❌ Không nhận diện")
        
        self.print_summary()
    
    def print_summary(self):
        """In tổng kết test"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = self.summary["passed"]
        total = self.summary["total"]
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"Total tests: {total}")
            print(f"Passed: {passed} ({success_rate:.1f}%)")
            print(f"Failed: {self.summary['failed']}")
            
            if passed > 0:
                avg_calories = self.summary["total_calories"] / passed
                avg_foods = self.summary["total_foods"] / passed
                print(f"Average calories per test: {avg_calories:.0f} kcal")
                print(f"Average foods per test: {avg_foods:.1f}")
            
            # Phân tích chi tiết
            print("\n📈 DETAILED ANALYSIS:")
            
            # Phân nhóm kết quả
            success_cases = [r for r in self.results if r.get("success")]
            failed_cases = [r for r in self.results if not r.get("success")]
            
            if success_cases:
                print("\n✅ SUCCESSFUL CASES (first 5):")
                for case in success_cases[:5]:
                    print(f"  - '{case['input']}' → {case['food_count']} món")
            
            if failed_cases:
                print("\n❌ FAILED CASES (first 5):")
                for case in failed_cases[:5]:
                    print(f"  - '{case['input']}'")
            
            # Thống kê món ăn phổ biến
            food_counter = {}
            for result in self.results:
                if result.get("success"):
                    for food in result.get("foods", []):
                        name = food.get("food_name")
                        if name:
                            food_counter[name] = food_counter.get(name, 0) + 1
            
            if food_counter:
                print("\n🍽️ MOST DETECTED FOODS:")
                sorted_foods = sorted(food_counter.items(), key=lambda x: x[1], reverse=True)
                for food, count in sorted_foods[:10]:
                    print(f"  - {food}: {count} lần")
        
        # Lưu kết quả ra file
        self.save_results()
    
    def save_results(self, filename="test_results.json"):
        """Lưu kết quả test ra file"""
        output = {
            "summary": self.summary,
            "results": self.results,
            "timestamp": datetime.now().isoformat(),
            "pipeline_version": "1.0.0"
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Results saved to {filename}")
    
    def load_and_compare(self, filename="test_results.json"):
        """Tải và so sánh kết quả test"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                old_results = json.load(f)
            
            old_pass = old_results["summary"]["passed"]
            old_total = old_results["summary"]["total"]
            old_rate = (old_pass / old_total * 100) if old_total > 0 else 0
            
            current_pass = self.summary["passed"]
            current_total = self.summary["total"]
            current_rate = (current_pass / current_total * 100) if current_total > 0 else 0
            
            print("\n📊 COMPARISON WITH PREVIOUS RUN:")
            print(f"Previous: {old_pass}/{old_total} ({old_rate:.1f}%)")
            print(f"Current:  {current_pass}/{current_total} ({current_rate:.1f}%)")
            
            if current_total > 0 and old_total > 0:
                improvement = current_rate - old_rate
                if improvement > 0:
                    print(f"✅ Improvement: +{improvement:.1f}%")
                elif improvement < 0:
                    print(f"⚠️ Regression: {improvement:.1f}%")
                else:
                    print(f"➡️ No change")
        
        except FileNotFoundError:
            print("No previous results found for comparison")

def main():
    if not IMPORT_SUCCESS:
        print("Cannot import required modules. Exiting.")
        return
    
    runner = AdvancedTestRunner()
    
    print("Select test mode:")
    print("1. Run all tests")
    print("2. Run smart sample (50 tests)")
    print("3. Run by group")
    print("4. Statistics only")
    print("5. Manual input (custom text)")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        limit = input("Enter limit (empty for all): ").strip()
        limit = int(limit) if limit else None
        runner.run_all_tests(limit)
    
    elif choice == "2":
        runner.run_smart_test()
    
    elif choice == "3":
        print("\nAvailable groups:")
        groups = [
            "chinh_ta", "dinh_luong_chinh_xac", "dinh_luong_tuong_doi",
            "so_bang_chu", "nhieu_mon", "mon_dac_biet", "mien_tay",
            "do_uong", "tinh_huong_thuc_te", "cap_nhat_so_luong"
        ]
        
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group}")
        
        group_choice = input("\nEnter group number: ").strip()
        try:
            group_idx = int(group_choice) - 1
            if 0 <= group_idx < len(groups):
                runner.run_test_group(groups[group_idx])
            else:
                print("Invalid group number")
        except ValueError:
            print("Invalid input")
    
    elif choice == "4":
        stats = get_statistics()
        print("\n📊 TEST CASE STATISTICS")
        print("=" * 50)
        print(f"Total test cases: {stats['total_test_cases']}")
        print(f"Number of groups: {stats['groups']}")
        
        print("\nCategories (estimated):")
        for cat, count in stats['categories'].items():
            print(f"  - {cat}: {count}")
    
    elif choice == "5":
        print("\nNhập câu cần test (để trống để hủy):")
        user_text = input("Text: ").strip()
        if not user_text:
            print("Hủy.")
            return
        
        desc = input("Mô tả (tùy chọn): ").strip() or "Custom input"
        expected_raw = input("Kỳ vọng số món (để trống nếu không chắc): ").strip()
        expected = None
        if expected_raw:
            try:
                expected = int(expected_raw)
            except ValueError:
                print("Kỳ vọng không hợp lệ, bỏ qua.")
                expected = None
        
        result = runner.run_single_test(user_text, desc, expected)
        print(f"\nKẾT QUẢ:")
        if result.get("success"):
            print(f"✅ Nhận diện {result['food_count']} món", end="")
            if result.get("expected_count") is not None:
                print(f" (kỳ vọng {result['expected_count']})")
            else:
                print("")
            for food in result.get("foods", []):
                name = food.get("food_name", "Unknown")
                qty = food.get("quantity_info", {}).get('amount', 0)
                unit = food.get("quantity_info", {}).get('unit', '')
                print(f"  - {name}: {qty} {unit}")
            print(f"Calories: {result['calories']:.0f} kcal")
        else:
            print(f"❌ Nhận diện {result.get('food_count', 0)} món")
            if result.get("expected_count") is not None:
                print(f"Kỳ vọng: {result['expected_count']}")
            if "error" in result:
                print(f"Lỗi: {result['error']}")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
