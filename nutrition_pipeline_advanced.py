import re
import json
import time
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
        # Gọi DeepSeek khi độ tin cậy dưới ngưỡng (mặc định 0.6 nếu không cấu hình)
        try:
            self.confidence_threshold = float(getattr(Config, "MIN_CONFIDENCE_FOR_API", 0.6) or 0.6)
        except Exception:
            self.confidence_threshold = 0.6
        # Cache ngắn để đảm bảo mỗi input chỉ gọi DeepSeek 1 lần trong cửa sổ TTL
        self.deepseek_cache_ttl = getattr(Config, "DEEPSEEK_CACHE_TTL_SECONDS", 5)
        self._deepseek_cache: Dict[str, Any] = {"key": None, "ts": 0.0, "result": None}
    
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

        # Dùng độ tin cậy match (không nhân với quantity để tránh tụt quá thấp)
        confidences: List[float] = []
        for food in analyzed_foods:
            try:
                conf = float(food.get('match_confidence', food.get('confidence', 0)) or 0)
            except Exception:
                conf = 0.0
            confidences.append(conf)

        if confidences and min(confidences) < self.confidence_threshold:
            return True, "low_confidence"

        return False, "confidence_ok"

    def _analyze_with_deepseek(self, user_input: str) -> Dict[str, Any]:
        """Gọi DeepSeek và chuẩn hóa kết quả về cấu trúc nội bộ."""
        cache_key = f"{self.deepseek_client.model}:{user_input.strip()}"
        now = time.time()
        if (
            self._deepseek_cache.get("key") == cache_key
            and now - float(self._deepseek_cache.get("ts", 0)) <= float(self.deepseek_cache_ttl or 0)
            and self._deepseek_cache.get("result") is not None
        ):
            cached = self._deepseek_cache["result"]
            return dict(cached)

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
        # Cache kết quả (kể cả lỗi) để tránh double-call
        self._deepseek_cache = {"key": cache_key, "ts": now, "result": dict(result)}
        return result

    def _normalize_deepseek_foods(self, deepseek_foods: List[Dict[str, Any]]) -> List[Dict]:
        """Chuẩn hóa output DeepSeek thành format pipeline."""
        normalized = []
        for raw in deepseek_foods or []:
            canonical_name = (
                raw.get('canonicalName')
                or raw.get('canonical_name')
                or raw.get('food_name')
                or raw.get('name')
                or raw.get('item')
            )
            alias_value = (
                raw.get('alias')
                or raw.get('raw_name')
                or raw.get('rawFoodName')
                or raw.get('raw_food_name')
            )
            raw_original = raw.get('original_text')

            base_label = canonical_name or alias_value or raw_original
            if not base_label:
                continue

            raw_label = str(base_label).strip()
            canonical_name = str(canonical_name).strip() if canonical_name else raw_label
            alias_value = str(alias_value).strip() if alias_value else raw_label
            surface_text = str(raw_original).strip() if raw_original else alias_value

            no_sugar = self._detect_no_sugar(surface_text)
            match_target = self._strip_no_sugar(canonical_name if canonical_name else surface_text) if no_sugar else (canonical_name or surface_text)

            try:
                raw_confidence = float(raw.get('confidence', 0.6) or 0.6)
            except Exception:
                raw_confidence = 0.6

            # Tên ưu tiên: luôn giữ canonical DeepSeek trả về để tránh đổi sang món khác.
            matched_name = str(match_target).strip()
            match_confidence = raw_confidence
            matcher_name, matcher_confidence = self.extractor.matcher.find_food(str(match_target))
            if not matcher_name:
                matcher_confidence = 0.0

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

            nutrition_hint = (
                raw.get('nutrition_hint')
                or raw.get('nutritionHint')
                or raw.get('nutrition_data')
                or raw.get('nutritionData')
                or raw.get('nutrition_guess')
                or raw.get('nutritionGuess')
                or raw.get('nutrition')
            )
            nutrition_hint = nutrition_hint if isinstance(nutrition_hint, dict) else None

            category = raw.get('category') or VIETNAMESE_FOODS_NUTRITION.get(matched_name, {}).get('category') or "custom"
            weight = estimate_weight(quantity_info, category)
            nutrition = {}
            if matched_name in VIETNAMESE_FOODS_NUTRITION:
                nutrition = calculate_nutrition(matched_name, weight) or {}
            elif nutrition_hint:
                nutrition = self._derive_nutrition_from_hint(nutrition_hint, weight)

            if no_sugar and isinstance(nutrition, dict):
                nutrition['sugar'] = 0.0

            aliases = raw.get('aliases')
            if not isinstance(aliases, list):
                aliases = []

            normalized.append({
                'food_name': matched_name,
                'canonical_name': canonical_name,
                'alias': alias_value,
                'aliases': aliases,
                'original_text': surface_text or raw_label,
                'quantity_info': quantity_info,
                'estimated_weight_g': weight,
                'nutrition': nutrition,
                'category': category,
                'confidence': combined_confidence,
                'match_confidence': match_confidence,
                'raw_food_name': surface_text,
                'no_sugar': no_sugar,
                'pending_nutrition': nutrition_hint
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

    def _derive_nutrition_from_hint(self, nutrition_hint: Dict[str, Any], weight: float) -> Dict[str, float]:
        """
        Convert per-100g/100ml nutrition hints from DeepSeek into absolute values using estimated weight.
        """
        if not isinstance(nutrition_hint, dict):
            return {}

        def pick_float(keys):
            for key in keys:
                if key in nutrition_hint:
                    try:
                        return float(nutrition_hint.get(key))
                    except Exception:
                        continue
            return None

        per_100g_keys = {
            "calories": pick_float(["calories_per_100g", "caloriesPer100g"]),
            "carbs": pick_float(["carbs_per_100g", "carbohydrates_per_100g", "carbsPer100g"]),
            "sugar": pick_float(["sugar_per_100g", "sugars_per_100g", "sugarPer100g"]),
            "protein": pick_float(["protein_per_100g", "proteinPer100g"]),
            "fat": pick_float(["fat_per_100g", "fatPer100g"]),
            "fiber": pick_float(["fiber_per_100g", "fiberPer100g"]),
        }
        per_100ml_keys = {
            "calories": pick_float(["calories_per_100ml", "caloriesPer100ml"]),
            "carbs": pick_float(["carbs_per_100ml", "carbohydrates_per_100ml", "carbsPer100ml"]),
            "sugar": pick_float(["sugar_per_100ml", "sugars_per_100ml", "sugarPer100ml"]),
            "protein": pick_float(["protein_per_100ml", "proteinPer100ml"]),
            "fat": pick_float(["fat_per_100ml", "fatPer100ml"]),
            "fiber": pick_float(["fiber_per_100ml", "fiberPer100ml"]),
        }

        has_g = any(v is not None for v in per_100g_keys.values())
        has_ml = any(v is not None for v in per_100ml_keys.values())
        base = per_100g_keys if has_g or not has_ml else per_100ml_keys

        try:
            weight_value = float(weight or 0)
        except Exception:
            weight_value = 0.0
        scale = weight_value / 100.0 if weight_value > 0 else 0.0

        result = {}
        for key, per_100_val in base.items():
            if per_100_val is None:
                continue
            result[key] = per_100_val * scale
        return result

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

        new_food_seen: set = set()

        for food in foods:
            canonical = (
                food.get('canonical_name')
                or food.get('food_name')
                or ""
            )
            canonical = str(canonical).strip()
            if not canonical:
                continue

            alias_candidates: List[str] = []
            raw_aliases = food.get('aliases') if isinstance(food.get('aliases'), list) else []
            for candidate in [
                food.get('alias'),
                food.get('raw_food_name'),
                *raw_aliases,
                canonical,
            ]:
                if not candidate:
                    continue
                candidate_str = str(candidate).strip()
                if candidate_str and candidate_str not in alias_candidates:
                    alias_candidates.append(candidate_str)

            try:
                match_confidence = float(food.get("match_confidence", 0) or 0)
            except Exception:
                match_confidence = 0.0

            nutrition_data = food.get("pending_nutrition")
            if not isinstance(nutrition_data, dict):
                nutrition_data = food.get("nutrition")

            canonical_in_db = canonical in VIETNAMESE_FOODS_NUTRITION
            existing_aliases: List[str] = []
            if canonical_in_db:
                aliases = VIETNAMESE_FOODS_NUTRITION.get(canonical, {}).get("aliases", [])
                if isinstance(aliases, list):
                    existing_aliases = [str(a).strip() for a in aliases if a]

            # Nếu là món mới (chưa có trong DB), chỉ thêm 1 bản ghi pending cho canonical để tránh duplicate.
            if not canonical_in_db:
                if canonical in new_food_seen:
                    continue
                primary_alias = canonical or (alias_candidates[0] if alias_candidates else None)
                if not primary_alias:
                    continue
                merged_nutrition = nutrition_data if isinstance(nutrition_data, dict) else {}
                if alias_candidates:
                    # Lưu gợi ý alias vào nutrition_data để admin tham khảo
                    merged_nutrition = dict(merged_nutrition)
                    merged_nutrition.setdefault("aliases", alias_candidates)

                self.learning_db.upsert_pending_food(
                    raw_name=primary_alias,
                    canonical_name=canonical,
                    suggested_action="new_food",
                    confidence=food.get("confidence", match_confidence),
                    example_input=user_input,
                    nutrition_data=merged_nutrition,
                    source="deepseek",
                )
                new_food_seen.add(canonical)
                continue

            for alias in alias_candidates:
                alias_clean = self._strip_no_sugar(alias) if alias else ""
                alias_clean = alias_clean.strip() if alias_clean else alias.strip()
                if not alias_clean:
                    continue

                if canonical_in_db:
                    if alias_clean == canonical:
                        continue
                    if alias_clean in existing_aliases:
                        continue
                    suggested_action = "alias"
                else:
                    suggested_action = "new_food"

                self.learning_db.upsert_pending_food(
                    raw_name=alias_clean,
                    canonical_name=canonical,
                    suggested_action=suggested_action,
                    confidence=food.get("confidence", match_confidence),
                    example_input=user_input,
                    nutrition_data=nutrition_data,
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
