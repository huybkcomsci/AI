import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
from config import Config
from deepseek_client import DeepSeekClient
from dbs import FoodLearningDB

# Import các class và functions từ chính module này
try:
    from vietnamese_foods_extended import (
        VIETNAMESE_FOODS_NUTRITION,
        UNIT_CONVERSION,
        FoodNameMatcher,
        QuantityParser,
        FoodExtractor,
        estimate_weight,
        calculate_nutrition
    )
except ImportError:
    # Fallback nếu import trực tiếp không được
    # Tạo minimal version
    VIETNAMESE_FOODS_NUTRITION = {}
    UNIT_CONVERSION = {}


class ConversationMemory:
    """Quản lý bộ nhớ hội thoại (3 lần gần nhất)"""
    
    def __init__(self, max_messages=3):
        self.max_messages = max_messages
        self.messages = deque(maxlen=max_messages)
        self.food_log = {}  # Theo dõi món ăn qua thời gian
        
    def add_message(self, user_input: str, analysis_result: Dict):
        """Thêm tin nhắn vào bộ nhớ"""
        timestamp = datetime.now().isoformat()
        
        message = {
            'timestamp': timestamp,
            'user_input': user_input,
            'analysis': analysis_result,
            'foods': analysis_result.get('foods', [])
        }
        
        self.messages.append(message)
        
        # Cập nhật food log với timestamp
        for food in analysis_result.get('foods', []):
            food_name = food.get('food_name')
            if food_name:
                if food_name not in self.food_log:
                    self.food_log[food_name] = []
                self.food_log[food_name].append({
                    'timestamp': timestamp,
                    'quantity': food.get('quantity_info', {}).get('amount', 1),
                    'unit': food.get('quantity_info', {}).get('unit', 'phần'),
                    'nutrition': food.get('nutrition', {})
                })
    
    def get_recent_foods(self, limit=10) -> List[Dict]:
        """Lấy các món ăn gần đây nhất"""
        recent_foods = []
        
        for message in list(self.messages):
            for food in message.get('foods', []):
                recent_foods.append({
                    'timestamp': message['timestamp'],
                    **food
                })
        
        # Sắp xếp theo thời gian mới nhất
        recent_foods.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return recent_foods[:limit]
    
    def update_food_quantity(self, food_name: str, new_quantity: int, new_unit: str = None):
        """Cập nhật số lượng cho món ăn trong lần nhập gần nhất"""
        if not self.messages:
            return False
        
        # Tìm trong tin nhắn gần nhất
        latest_message = self.messages[-1]
        
        for food in latest_message.get('foods', []):
            if food.get('food_name') == food_name:
                # Cập nhật số lượng
                food['quantity_info']['amount'] = new_quantity
                if new_unit:
                    food['quantity_info']['unit'] = new_unit
                
                # Tính lại dinh dưỡng
                weight = estimate_weight(
                    food['quantity_info'], 
                    VIETNAMESE_FOODS_NUTRITION.get(food_name, {}).get('category')
                )
                food['nutrition'] = calculate_nutrition(food_name, weight)
                
                return True
        
        return False
    
    def get_summary(self) -> Dict:
        """Lấy tổng kết từ 3 hội thoại gần nhất"""
        total_nutrition = {
            'calories': 0,
            'carbs': 0,
            'sugar': 0,
            'protein': 0,
            'fat': 0,
            'fiber': 0
        }
        
        food_counts = {}
        
        for message in list(self.messages):
            for food in message.get('foods', []):
                nutrition = food.get('nutrition', {})
                for key in total_nutrition:
                    total_nutrition[key] += nutrition.get(key, 0)
                
                # Đếm số lần xuất hiện
                food_name = food.get('food_name')
                if food_name:
                    if food_name not in food_counts:
                        food_counts[food_name] = 0
                    food_counts[food_name] += 1
        
        return {
            'total_nutrition': total_nutrition,
            'food_counts': food_counts,
            'message_count': len(self.messages)
        }
    
    def clear(self):
        """Xóa bộ nhớ"""
        self.messages.clear()
        self.food_log.clear()

class NutritionPipelineAdvanced:
    """Pipeline xử lý dinh dưỡng nâng cao"""
    
    def __init__(self):
        self.extractor = FoodExtractor()
        self.deepseek_client = DeepSeekClient()
        self.learning_db = FoodLearningDB()
        self.memory = ConversationMemory(max_messages=3)
        self.daily_totals = {
            'calories': 0,
            'carbs': 0,
            'sugar': 0,
            'protein': 0,
            'fat': 0,
            'fiber': 0
        }
        self.confidence_threshold = getattr(Config, "MIN_CONFIDENCE_FOR_API", 0.7)
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Xử lý input chính"""
        extracted_foods = self.extractor.extract(user_input)

        analyzed_foods = []
        for food_info in extracted_foods:
            analysis = self._analyze_food(food_info)
            if analysis:
                analyzed_foods.append(analysis)

        use_deepseek, trigger_reason = self._should_use_deepseek(
            extracted_foods, analyzed_foods
        )
        deepseek_result = {
            'deepseek_used': use_deepseek,
            'deepseek_available': self.deepseek_client.is_available(),
            'deepseek_success': False,
            'deepseek_trigger': trigger_reason,
            'deepseek_error': None,
            'deepseek_analysis': None,
            'deepseek_suggestions': []
        }
        processing_method = "local"

        if use_deepseek:
            ds_output = self._analyze_with_deepseek(user_input)
            deepseek_result.update({
                'deepseek_success': ds_output.get('success', False),
                'deepseek_error': ds_output.get('error'),
                'deepseek_analysis': ds_output.get('analysis'),
                'deepseek_suggestions': ds_output.get('suggestions', []),
                'deepseek_raw': ds_output.get('raw_content', "")
            })

            if ds_output.get('success'):
                analyzed_foods = ds_output.get('foods', analyzed_foods)
                processing_method = "deepseek"

        is_update = self._check_if_update(analyzed_foods)
        meal_summary = self._calculate_meal_summary(analyzed_foods)

        result = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'foods': analyzed_foods,
            'meal_summary': meal_summary,
            'is_update': is_update,
            'extracted_count': len(extracted_foods),
            'analyzed_count': len(analyzed_foods),
            'processing_method': processing_method,
            **deepseek_result
        }

        self.memory.add_message(user_input, result)
        
        self._update_daily_totals(meal_summary)
        
        result['memory_summary'] = self.memory.get_summary()
        result['daily_totals'] = self.daily_totals.copy()
        
        response = self._generate_response(result)
        
        result['response'] = response
        
        return result
    
    def _analyze_food(self, food_info: Dict) -> Optional[Dict]:
        """Phân tích chi tiết một món ăn"""
        food_name = food_info['food_name']
        quantity_info = food_info['quantity_info']
        no_sugar = bool(food_info.get('no_sugar') or food_info.get('noSugar'))
        match_confidence = float(food_info.get('match_confidence', 1.0) or 0.0)
        quantity_confidence = float(quantity_info.get('confidence', 0.7) or 0.0)
        combined_confidence = max(0.0, min(1.0, round(match_confidence * quantity_confidence, 2)))
        
        # Lấy thông tin món ăn
        food_data = VIETNAMESE_FOODS_NUTRITION.get(food_name)
        if not food_data:
            return None
        
        # Ước lượng trọng lượng
        weight = estimate_weight(quantity_info, food_data.get('category'))
        
        # Tính dinh dưỡng
        nutrition = calculate_nutrition(food_name, weight) or {}
        if no_sugar and isinstance(nutrition, dict):
            nutrition['sugar'] = 0.0
        
        return {
            'food_name': food_name,
            'original_text': food_info['original_text'],
            'quantity_info': quantity_info,
            'estimated_weight_g': weight,
            'nutrition': nutrition,
            'category': food_data.get('category'),
            'confidence': combined_confidence,
            'match_confidence': match_confidence,
            'no_sugar': no_sugar
        }

    def _should_use_deepseek(
        self,
        extracted_foods: List[Dict],
        analyzed_foods: List[Dict]
    ) -> Tuple[bool, str]:
        """Quyết định có cần gọi DeepSeek khi độ tin cậy thấp."""
        if not self.deepseek_client.is_available():
            return False, "deepseek_not_configured"

        if not extracted_foods or not analyzed_foods:
            return True, "no_foods_detected"

        confidences = [food.get('confidence', 0) for food in analyzed_foods]
        if confidences and min(confidences) < self.confidence_threshold:
            return True, "low_confidence"

        return False, "confidence_ok"

    def _analyze_with_deepseek(self, user_input: str) -> Dict[str, Any]:
        """Gọi DeepSeek và chuẩn hóa kết quả về cấu trúc nội bộ."""
        try:
            ds_raw = self.deepseek_client.analyze(user_input)
            foods = self._normalize_deepseek_foods(ds_raw.get("foods", []))

            success = ds_raw.get("success", False) and bool(foods)
            error = ds_raw.get("error")
            if ds_raw.get("success") and not foods:
                error = "DeepSeek did not return recognizable foods"

            if success:
                self._persist_deepseek_pending(user_input, foods)

            return {
                "success": success,
                "foods": foods,
                "analysis": ds_raw.get("analysis", ""),
                "suggestions": ds_raw.get("suggestions", []),
                "raw_content": ds_raw.get("raw_content", ""),
                "error": error
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            return {
                "success": False,
                "foods": [],
                "analysis": "",
                "suggestions": [],
                "raw_content": "",
                "error": str(exc)
            }

    def _normalize_deepseek_foods(self, deepseek_foods: List[Dict[str, Any]]) -> List[Dict]:
        """Chuẩn hóa output DeepSeek thành format pipeline."""
        normalized = []
        for raw in deepseek_foods or []:
            raw_name = raw.get('food_name') or raw.get('name') or raw.get('item')
            if not raw_name:
                continue

            raw_name = str(raw_name).strip()
            no_sugar = self._detect_no_sugar(raw_name)
            match_name = self._strip_no_sugar(raw_name) if no_sugar else raw_name
            
            matched_name, match_confidence = self.extractor.matcher.find_food(str(match_name))
            if not matched_name:
                matched_name = str(match_name).strip()
                match_confidence = 0.5

            qty_data = raw.get('quantity') or raw.get('quantity_info') or {}
            amount = qty_data.get('amount') or qty_data.get('value') or 1
            unit = qty_data.get('unit') or 'phần'
            base_confidence = raw.get('confidence', qty_data.get('confidence', 0.6))

            try:
                amount = float(amount)
            except Exception:
                amount = 1
            
            try:
                base_confidence = float(base_confidence)
            except Exception:
                base_confidence = 0.6

            quantity_confidence = qty_data.get('confidence', base_confidence)
            try:
                quantity_confidence = float(quantity_confidence)
            except Exception:
                quantity_confidence = base_confidence

            quantity_info = {
                'amount': amount,
                'unit': unit,
                'type': 'relative',
                'confidence': quantity_confidence
            }
            
            combined_confidence = max(
                0.0,
                min(1.0, round(match_confidence * quantity_confidence, 2))
            )

            category = VIETNAMESE_FOODS_NUTRITION.get(matched_name, {}).get('category')
            weight = estimate_weight(quantity_info, category)
            nutrition = (
                (calculate_nutrition(matched_name, weight) or {})
                if matched_name in VIETNAMESE_FOODS_NUTRITION
                else {}
            )
            if no_sugar and isinstance(nutrition, dict):
                nutrition['sugar'] = 0.0

            normalized.append({
                'food_name': matched_name,
                'original_text': raw.get('original_text', raw_name),
                'quantity_info': quantity_info,
                'estimated_weight_g': weight,
                'nutrition': nutrition,
                'category': category,
                'confidence': combined_confidence,
                'match_confidence': match_confidence,
                'raw_food_name': raw_name,
                'no_sugar': no_sugar
            })

        return normalized

    def _detect_no_sugar(self, text: str) -> bool:
        """Detect 'không đường' / 'no sugar' markers in a food label."""
        if not text:
            return False
        normalized = self.extractor.matcher.normalize_text(text)
        if not normalized:
            return False
        if re.search(r"\b(khong|ko|k0)\s*(co\s*)?duong\b", normalized):
            return True
        if "no sugar" in normalized or "sugar free" in normalized or "unsweetened" in normalized:
            return True
        return False

    def _strip_no_sugar(self, text: str) -> str:
        """Remove 'không đường' markers for better food name matching."""
        if not text:
            return text
        result = re.sub(
            r"(không|khong|ko|k0)\s*(có\s*)?đường",
            " ",
            text,
            flags=re.IGNORECASE,
        )
        result = re.sub(
            r"(khong|ko|k0)\s*(co\s*)?duong",
            " ",
            result,
            flags=re.IGNORECASE,
        )
        result = re.sub(r"\bno\s*sugar\b", " ", result, flags=re.IGNORECASE)
        result = re.sub(r"\bsugar\s*free\b", " ", result, flags=re.IGNORECASE)
        result = re.sub(r"\bunsweetened\b", " ", result, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", result).strip()

    def _persist_deepseek_pending(self, user_input: str, foods: List[Dict[str, Any]]) -> None:
        """
        Persist DeepSeek foods into a pending table for admin approval.
        """
        if not foods:
            return

        for food in foods:
            canonical = (food.get('food_name') or "").strip()
            if not canonical:
                continue

            raw_name = (food.get('raw_food_name') or "").strip()
            alias = self._strip_no_sugar(raw_name) if raw_name else ""
            if not alias:
                alias = canonical

            # Only add to pending when the food is unknown (or matched with very low confidence),
            # to avoid noise when DeepSeek returns a mix of known + unknown foods.
            try:
                match_confidence = float(food.get("match_confidence", 0) or 0)
            except Exception:
                match_confidence = 0.0

            canonical_in_db = canonical in VIETNAMESE_FOODS_NUTRITION
            if canonical_in_db and match_confidence >= 0.6:
                continue

            suggested_action = "new_food"
            candidate_name = alias.strip()
            if not candidate_name:
                continue

            self.learning_db.upsert_pending_food(
                raw_name=candidate_name,
                canonical_name=candidate_name,
                suggested_action=suggested_action,
                confidence=food.get("confidence"),
                example_input=user_input,
                nutrition_data=food.get("nutrition"),
                source="deepseek",
            )
    
    def _check_if_update(self, analyzed_foods: List[Dict]) -> bool:
        """Kiểm tra xem có phải là cập nhật số lượng không"""
        if not analyzed_foods or len(self.memory.messages) < 2:
            return False
        
        # Lấy tin nhắn gần thứ 2 (trước tin nhắn mới nhất)
        if len(self.memory.messages) >= 2:
            previous_foods = list(self.memory.messages)[-2].get('foods', [])
            
            # So sánh tên món ăn
            current_names = {f['food_name'] for f in analyzed_foods}
            previous_names = {f['food_name'] for f in previous_foods}
            
            # Nếu có ít nhất 1 món trùng và số món ít
            if len(current_names & previous_names) > 0 and len(analyzed_foods) <= 2:
                return True
        
        return False
    
    def _calculate_meal_summary(self, foods: List[Dict]) -> Dict:
        """Tính tổng cho bữa ăn"""
        summary = {
            'calories': 0,
            'carbs': 0,
            'sugar': 0,
            'protein': 0,
            'fat': 0,
            'fiber': 0,
            'food_count': len(foods)
        }
        
        for food in foods:
            nutrition = food.get('nutrition', {})
            for key in summary:
                if key in nutrition:
                    summary[key] += nutrition[key]
        
        return summary
    
    def _update_daily_totals(self, meal_summary: Dict):
        """Cập nhật tổng ngày"""
        for key in self.daily_totals:
            self.daily_totals[key] += meal_summary.get(key, 0)
    
    def _generate_response(self, result: Dict) -> str:
        """Tạo phản hồi thông minh"""
        foods = result['foods']
        meal_summary = result['meal_summary']
        memory_summary = result['memory_summary']
        
        if not foods:
            base_msg = "🤔 Tôi không nhận diện được món ăn nào. Bạn có thể thử nhập:\n- '2 bát cơm với thịt kho'\n- '1 tô phở bò'\n- '200g cá chiên và canh rau'"
            if result.get('deepseek_used'):
                ds_error = result.get('deepseek_error') or "DeepSeek không trả về kết quả"
                base_msg += f"\n(Đã thử DeepSeek: {ds_error})"
            elif result.get('deepseek_trigger') == "deepseek_not_configured":
                base_msg += "\n(DeepSeek chưa được cấu hình. Thêm DEEPSEEK_API_KEY để bật tự động fallback.)"
            return base_msg
        
        # Xây dựng phản hồi
        lines = []
        
        if result['is_update']:
            lines.append("🔄 **ĐÃ CẬP NHẬT SỐ LƯỢNG**")
        else:
            lines.append("🍽️ **PHÂN TÍCH BỮA ĂN**")

        if result.get('processing_method') == "deepseek":
            lines.append("🤖 Đã dùng DeepSeek do độ tin cậy thấp/không nhận diện được món.")
            if result.get('deepseek_analysis'):
                lines.append(result['deepseek_analysis'])

        lines.append("")
        
        # Liệt kê món ăn
        lines.append("**Các món đã nhận diện:**")
        for i, food in enumerate(foods, 1):
            quantity = food['quantity_info']
            weight = food['estimated_weight_g']
            
            line = f"{i}. {food['food_name'].capitalize()}: "
            if quantity['type'] == 'exact':
                line += f"{quantity['amount']:.0f}{quantity['unit']}"
            else:
                line += f"{quantity['amount']} {quantity['unit']} (≈{weight:.0f}g)"
            
            lines.append(line)
        
        lines.append("")
        
        # Thông tin dinh dưỡng bữa ăn
        lines.append("📊 **DINH DƯỠNG BỮA NÀY:**")
        lines.append(f"• Calories: {meal_summary['calories']:.0f} kcal")
        lines.append(f"• Tinh bột: {meal_summary['carbs']:.1f}g")
        lines.append(f"• Đường: {meal_summary['sugar']:.1f}g")
        lines.append(f"• Protein: {meal_summary['protein']:.1f}g")
        lines.append(f"• Chất béo: {meal_summary['fat']:.1f}g")
        
        lines.append("")
        
        # Thông tin từ 3 hội thoại gần nhất
        mem_total = memory_summary['total_nutrition']
        lines.append("📈 **TỔNG 3 BỮA GẦN NHẤT:**")
        lines.append(f"• Calories: {mem_total['calories']:.0f} kcal")
        lines.append(f"• Protein: {mem_total['protein']:.1f}g")
        
        lines.append("")
        
        # Tổng ngày
        lines.append(f"📅 **TỔNG HÔM NAY:** {self.daily_totals['calories']:.0f} kcal")

        if result.get('deepseek_suggestions'):
            suggestion = result['deepseek_suggestions'][0]
            lines.append("")
            lines.append(f"💡 Gợi ý từ DeepSeek: {suggestion}")
        
        lines.append("")
        
        # Ghi chú về sai số
        lines.append("💡 *Ghi chú: Kết quả có sai số nhất định.*")
        lines.append("*Để chính xác hơn, hãy nhập định lượng cụ thể (ví dụ: 150g thịt).*")
        
        return "\n".join(lines)
    
    def reset_daily(self):
        """Reset tổng ngày"""
        self.daily_totals = {k: 0 for k in self.daily_totals}
    
    def clear_memory(self):
        """Xóa bộ nhớ"""
        self.memory.clear()
    
    def get_statistics(self) -> Dict:
        """Lấy thống kê"""
        return {
            'daily_totals': self.daily_totals,
            'memory_summary': self.memory.get_summary(),
            'recent_foods': self.memory.get_recent_foods(5)
        }
