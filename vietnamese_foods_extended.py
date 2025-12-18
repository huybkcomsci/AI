import re
import json
from typing import Dict, List, Tuple, Optional, Any
import random

# Database món ăn với nhiều biến thể chính tả
VIETNAMESE_FOODS_NUTRITION = {
    # === CƠM VÀ MÓN CHÍNH ===
    "cơm trắng": {
        "calories_per_100g": 130,
        "carbs_per_100g": 28.2,
        "sugar_per_100g": 0.1,
        "protein_per_100g": 2.7,
        "fat_per_100g": 0.3,
        "fiber_per_100g": 0.4,
        "aliases": ["com trang", "cơm", "com", "rice", "cơm tẻ", "com te"],
        "category": "rice"
    },
    
    "cơm sườn": {
        "calories_per_100g": 180,
        "carbs_per_100g": 25,
        "sugar_per_100g": 1,
        "protein_per_100g": 8,
        "fat_per_100g": 6,
        "fiber_per_100g": 0.5,
        "aliases": ["com suon", "cơm sườn nướng", "com suon nuong", "rice with pork chop"],
        "category": "combo",
        "components": {"cơm trắng": 200, "sườn nướng": 120, "đồ chua": 30}
    },
    
    "sườn nướng": {
        "calories_per_100g": 250,
        "carbs_per_100g": 5,
        "sugar_per_100g": 2,
        "protein_per_100g": 25,
        "fat_per_100g": 15,
        "fiber_per_100g": 0,
        "aliases": ["suon nuong", "sườn", "suon", "pork chop", "sườn heo nướng"],
        "category": "meat"
    },
    
    "thịt bò": {
        "calories_per_100g": 250,
        "carbs_per_100g": 0,
        "sugar_per_100g": 0,
        "protein_per_100g": 26,
        "fat_per_100g": 15,
        "fiber_per_100g": 0,
        "aliases": ["thit bo", "bò", "bo", "beef", "thịt", "thit"],
        "category": "meat"
    },
    
    "trứng chiên": {
        "calories_per_100g": 196,
        "carbs_per_100g": 1.1,
        "sugar_per_100g": 0.3,
        "protein_per_100g": 13.6,
        "fat_per_100g": 15,
        "fiber_per_100g": 0,
        "aliases": ["trung chien", "trứng", "trung", "egg", "trứng rán", "trung ran", "trứng ốp la"],
        "category": "egg"
    },
    
    "trứng luộc": {
        "calories_per_100g": 155,
        "carbs_per_100g": 1.1,
        "sugar_per_100g": 0.3,
        "protein_per_100g": 13,
        "fat_per_100g": 11,
        "fiber_per_100g": 0,
        "aliases": ["trung luoc", "trứng chín", "trung chin", "boiled egg"],
        "category": "egg"
    },
    
    # === PHỞ/BÚN/MÌ ===
    "phở bò": {
        "calories_per_100g": 85,
        "carbs_per_100g": 12,
        "sugar_per_100g": 1,
        "protein_per_100g": 6,
        "fat_per_100g": 2,
        "fiber_per_100g": 0.5,
        "aliases": ["pho bo", "phở", "pho", "beef noodle soup", "phở tái", "pho tai"],
        "category": "noodle"
    },
    
    "bún chả": {
        "calories_per_100g": 110,
        "carbs_per_100g": 18,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 2,
        "fiber_per_100g": 1,
        "aliases": ["bun cha", "bún", "bun", "vermicelli with grilled pork"],
        "category": "noodle"
    },
    
    "bún đậu mắm tôm": {
        "calories_per_100g": 190,
        "carbs_per_100g": 25,
        "sugar_per_100g": 3,
        "protein_per_100g": 10,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["bun dau mam tom", "bun dau", "bún đậu"],
        "category": "combo"
    },
    
    # === BÁNH ===
    "bánh mì": {
        "calories_per_100g": 250,
        "carbs_per_100g": 40,
        "sugar_per_100g": 2,
        "protein_per_100g": 8,
        "fat_per_100g": 6,
        "fiber_per_100g": 2,
        "aliases": ["banh mi", "bánh", "banh", "bread", "bánh mì sandwich"],
        "category": "bread"
    },
    
    # === ĐỒ UỐNG ===
    "cà phê sữa": {
        "calories_per_100ml": 120,
        "carbs_per_100ml": 20,
        "sugar_per_100ml": 18,
        "protein_per_100ml": 2,
        "fat_per_100ml": 3,
        "fiber_per_100ml": 0,
        "aliases": ["ca phe sua", "cafe sữa", "cafe sua", "coffee with milk"],
        "category": "drink"
    },
    "cà phê đen": {
    "calories_per_100ml": 1,
    "carbs_per_100ml": 0,
    "sugar_per_100ml": 0,
    "protein_per_100ml": 0.2,
    "fat_per_100ml": 0,
    "fiber_per_100ml": 0,
    "aliases": ["ca phe den", "cafe den", "black coffee", "cà phê đá", "ca phe da", "espresso", "americano", "đen đá", "den da", "den da khong duong", "đen đá có đường", "cafe", "coffee"],
    "category": "drink"
},
    
    "nước cam": {
        "calories_per_100ml": 45,
        "carbs_per_100ml": 10,
        "sugar_per_100ml": 8,
        "protein_per_100ml": 0.7,
        "fat_per_100ml": 0.2,
        "fiber_per_100ml": 0.2,
        "aliases": ["nuoc cam", "nước cam ép", "nuoc cam ep", "orange juice"],
        "category": "drink"
    },
    
    "nước mía": {
        "calories_per_100ml": 65,
        "carbs_per_100ml": 16,
        "sugar_per_100ml": 15,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["nuoc mia", "nước mía", "sugarcane juice"],
        "category": "drink"
    },
    
    "thịt kho": {
        "calories_per_100g": 220,
        "carbs_per_100g": 5,
        "sugar_per_100g": 3,
        "protein_per_100g": 20,
        "fat_per_100g": 12,
        "fiber_per_100g": 0,
        "aliases": ["thit kho", "thịt kho tàu", "thit kho tau", "braised pork"],
        "category": "meat"
    },
    
    "cá chiên": {
        "calories_per_100g": 180,
        "carbs_per_100g": 2,
        "sugar_per_100g": 0,
        "protein_per_100g": 22,
        "fat_per_100g": 9,
        "fiber_per_100g": 0,
        "aliases": ["ca chien", "cá rán", "ca ran", "fried fish"],
        "category": "fish"
    },
    
    "bún bò huế": {
        "calories_per_100g": 95,
        "carbs_per_100g": 14,
        "sugar_per_100g": 1,
        "protein_per_100g": 7,
        "fat_per_100g": 2,
        "fiber_per_100g": 0.5,
        "aliases": ["bun bo hue", "bún bò", "bun bo", "hue beef noodle"],
        "category": "noodle"
    },
    "bún bò huế": {
        "calories_per_100g": 95,
        "carbs_per_100g": 14,
        "sugar_per_100g": 1,
        "protein_per_100g": 7,
        "fat_per_100g": 2,
        "fiber_per_100g": 0.5,
        "aliases": ["bun bo hue", "bún bò", "bun bo"],
        "category": "noodle"
    },
    
    "cơm tấm": {
        "calories_per_100g": 160,
        "carbs_per_100g": 26,
        "sugar_per_100g": 1,
        "protein_per_100g": 9,
        "fat_per_100g": 4,
        "fiber_per_100g": 0.6,
        "aliases": ["com tam", "cơm tấm sườn", "com tam suon"],
        "category": "rice"
    },
    
    "bánh xèo": {
        "calories_per_100g": 180,
        "carbs_per_100g": 25,
        "sugar_per_100g": 1,
        "protein_per_100g": 6,
        "fat_per_100g": 8,
        "fiber_per_100g": 1,
        "aliases": ["banh xeo", "bánh xèo tôm thịt"],
        "category": "cake"
    },
    
    "gỏi cuốn": {
        "calories_per_100g": 80,
        "carbs_per_100g": 12,
        "sugar_per_100g": 1,
        "protein_per_100g": 5,
        "fat_per_100g": 1,
        "fiber_per_100g": 1,
        "aliases": ["goi cuon", "spring roll", "chả giò"],
        "category": "roll"
    },
    
    "chả giò": {
        "calories_per_100g": 220,
        "carbs_per_100g": 20,
        "sugar_per_100g": 1,
        "protein_per_100g": 8,
        "fat_per_100g": 12,
        "fiber_per_100g": 1,
        "aliases": ["cha gio", "nem rán", "nem ran"],
        "category": "fried"
    },
    
    "bò lúc lắc": {
        "calories_per_100g": 180,
        "carbs_per_100g": 8,
        "sugar_per_100g": 2,
        "protein_per_100g": 20,
        "fat_per_100g": 8,
        "fiber_per_100g": 0.5,
        "aliases": ["bo luc lac", "thịt bò lúc lắc", "thit bo luc lac"],
        "category": "meat"
    },
    
    "cá kho tộ": {
        "calories_per_100g": 150,
        "carbs_per_100g": 5,
        "sugar_per_100g": 3,
        "protein_per_100g": 18,
        "fat_per_100g": 6,
        "fiber_per_100g": 0.5,
        "aliases": ["ca kho to", "cá kho", "ca kho"],
        "category": "fish"
    },
    
    # Đồ uống thêm
    "trà đá": {
        "calories_per_100ml": 1,
        "carbs_per_100ml": 0,
        "sugar_per_100ml": 0,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["tra da", "trà", "tra"],
        "category": "drink"
    },
    
    "nước chanh": {
        "calories_per_100ml": 25,
        "carbs_per_100ml": 6,
        "sugar_per_100ml": 5,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["nuoc chanh", "lemonade"],
        "category": "drink"
    },
    
    "sinh tố xoài": {
        "calories_per_100ml": 60,
        "carbs_per_100ml": 14,
        "sugar_per_100ml": 10,
        "protein_per_100ml": 1,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 1,
        "aliases": ["sinh to xoai", "mango smoothie"],
        "category": "drink"
    },
    
    # Đồ ăn vặt
    "bánh bao": {
        "calories_per_100g": 220,
        "carbs_per_100g": 40,
        "sugar_per_100g": 5,
        "protein_per_100g": 8,
        "fat_per_100g": 4,
        "fiber_per_100g": 2,
        "aliases": ["banh bao", "bánh bao nhân thịt"],
        "category": "snack"
    },
    
    "mì tôm": {
        "calories_per_100g": 380,
        "carbs_per_100g": 60,
        "sugar_per_100g": 2,
        "protein_per_100g": 10,
        "fat_per_100g": 12,
        "fiber_per_100g": 2,
        "aliases": ["mi tom", "mì gói", "mi goi", "instant noodle"],
        "category": "snack"
    },
    
    # Thức ăn kiêng/thể hình
    "ức gà": {
        "calories_per_100g": 165,
        "carbs_per_100g": 0,
        "sugar_per_100g": 0,
        "protein_per_100g": 31,
        "fat_per_100g": 3.6,
        "fiber_per_100g": 0,
        "aliases": ["uc ga", "thịt ức gà", "thit uc ga", "chicken breast"],
        "category": "meat"
    },
    
    "khoai lang": {
        "calories_per_100g": 86,
        "carbs_per_100g": 20,
        "sugar_per_100g": 4,
        "protein_per_100g": 1.6,
        "fat_per_100g": 0.1,
        "fiber_per_100g": 3,
        "aliases": ["khoai lang", "sweet potato"],
        "category": "vegetable"
    },
    
    "cơm gạo lứt": {
        "calories_per_100g": 110,
        "carbs_per_100g": 23,
        "sugar_per_100g": 0.5,
        "protein_per_100g": 2.6,
        "fat_per_100g": 0.9,
        "fiber_per_100g": 1.8,
        "aliases": ["gao lut", "com gao lut", "brown rice"],
        "category": "rice"
    },
    
    "rau luộc": {
        "calories_per_100g": 25,
        "carbs_per_100g": 4,
        "sugar_per_100g": 1,
        "protein_per_100g": 2,
        "fat_per_100g": 0.2,
        "fiber_per_100g": 2.5,
        "aliases": ["rau xanh", "rau luoc", "luoc rau"],
        "category": "vegetable"
    },
    
    "canh rau": {
        "calories_per_100g": 35,
        "carbs_per_100g": 6,
        "sugar_per_100g": 1.5,
        "protein_per_100g": 2,
        "fat_per_100g": 0.5,
        "fiber_per_100g": 1.5,
        "aliases": ["canh rau xanh", "canh", "sup rau", "canh cai"],
        "category": "soup"
    },
    
    "canh chua cá lóc": {
        "calories_per_100g": 70,
        "carbs_per_100g": 5,
        "sugar_per_100g": 2,
        "protein_per_100g": 8,
        "fat_per_100g": 2,
        "fiber_per_100g": 1,
        "aliases": ["canh chua", "canh chua ca loc", "canh chua ca"],
        "category": "soup"
    },
    
    "chuối": {
        "calories_per_100g": 89,
        "carbs_per_100g": 23,
        "sugar_per_100g": 12,
        "protein_per_100g": 1.1,
        "fat_per_100g": 0.3,
        "fiber_per_100g": 2.6,
        "aliases": ["chuoi", "banana"],
        "category": "fruit"
    },
    
    "cháo": {
        "calories_per_100g": 70,
        "carbs_per_100g": 15,
        "sugar_per_100g": 0.5,
        "protein_per_100g": 2,
        "fat_per_100g": 0.5,
        "fiber_per_100g": 0.5,
        "aliases": ["chao", "porridge", "cháo trắng"],
        "category": "carb"
    },
    
    "trái cây nghiền": {
        "calories_per_100g": 60,
        "carbs_per_100g": 15,
        "sugar_per_100g": 12,
        "protein_per_100g": 0.5,
        "fat_per_100g": 0.2,
        "fiber_per_100g": 1.5,
        "aliases": ["trai cay nghien", "fruit puree", "puree"],
        "category": "fruit"
    },
    
    "gà nướng": {
        "calories_per_100g": 215,
        "carbs_per_100g": 0,
        "sugar_per_100g": 0,
        "protein_per_100g": 27,
        "fat_per_100g": 11,
        "fiber_per_100g": 0,
        "aliases": ["ga nuong", "grilled chicken", "gà quay"],
        "category": "meat"
    },
    
    "lẩu": {
        "calories_per_100g": 120,
        "carbs_per_100g": 10,
        "sugar_per_100g": 2,
        "protein_per_100g": 12,
        "fat_per_100g": 4,
        "fiber_per_100g": 1,
        "aliases": ["lau", "lau thai", "lau hai san"],
        "category": "combo"
    },
    
    "bánh kem": {
        "calories_per_100g": 290,
        "carbs_per_100g": 38,
        "sugar_per_100g": 30,
        "protein_per_100g": 3,
        "fat_per_100g": 12,
        "fiber_per_100g": 0.5,
        "aliases": ["banh kem", "cake", "bánh sinh nhật"],
        "category": "dessert"
    },
    
    "bim bim": {
        "calories_per_100g": 550,
        "carbs_per_100g": 53,
        "sugar_per_100g": 3,
        "protein_per_100g": 6,
        "fat_per_100g": 35,
        "fiber_per_100g": 3,
        "aliases": ["bim bim", "snack", "chips", "bim bim khoai"],
        "category": "snack"
    },
    
    "kẹo": {
        "calories_per_100g": 400,
        "carbs_per_100g": 90,
        "sugar_per_100g": 75,
        "protein_per_100g": 0,
        "fat_per_100g": 5,
        "fiber_per_100g": 0,
        "aliases": ["keo", "candy", "kẹo ngọt"],
        "category": "snack"
    },
    
    "nước ngọt": {
        "calories_per_100ml": 42,
        "carbs_per_100ml": 11,
        "sugar_per_100ml": 11,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["nuoc ngot", "coca", "pepsi", "soda", "soft drink"],
        "category": "drink"
    },
    
    "nước dừa": {
        "calories_per_100ml": 19,
        "carbs_per_100ml": 4,
        "sugar_per_100ml": 3,
        "protein_per_100ml": 0.7,
        "fat_per_100ml": 0.2,
        "fiber_per_100ml": 0.2,
        "aliases": ["nuoc dua", "coconut water", "dua tuoi"],
        "category": "drink"
    },
    
    "sữa đậu nành": {
        "calories_per_100ml": 54,
        "carbs_per_100ml": 6,
        "sugar_per_100ml": 3,
        "protein_per_100ml": 3.5,
        "fat_per_100ml": 1.8,
        "fiber_per_100ml": 0.6,
        "aliases": ["sua dau nanh", "soy milk", "sữa đậu"],
        "category": "drink"
    },
    
    "nước ép cà rốt": {
        "calories_per_100ml": 40,
        "carbs_per_100ml": 9,
        "sugar_per_100ml": 5,
        "protein_per_100ml": 1,
        "fat_per_100ml": 0.2,
        "fiber_per_100ml": 0.8,
        "aliases": ["nuoc ep ca rot", "carrot juice"],
        "category": "drink"
    },
    
    "bia": {
        "calories_per_100ml": 43,
        "carbs_per_100ml": 3.6,
        "sugar_per_100ml": 0,
        "protein_per_100ml": 0.5,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["beer", "bia lon", "bia chai"],
        "category": "drink"
    },
    
    "rượu vang": {
        "calories_per_100ml": 85,
        "carbs_per_100ml": 2.6,
        "sugar_per_100ml": 0.9,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["ruou vang", "wine", "ruou do", "ruou trang"],
        "category": "drink"
    },
    
    "sữa": {
        "calories_per_100ml": 60,
        "carbs_per_100ml": 5,
        "sugar_per_100ml": 5,
        "protein_per_100ml": 3,
        "fat_per_100ml": 3,
        "fiber_per_100ml": 0,
        "aliases": ["sua", "milk", "sữa tươi"],
        "category": "drink"
    },
    
    "nước mắm": {
        "calories_per_100ml": 60,
        "carbs_per_100ml": 3,
        "sugar_per_100ml": 3,
        "protein_per_100ml": 5,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["nuoc mam", "mam", "fish sauce", "nuoc mam ngon"],
        "category": "drink"
    },
    
    "nước lọc": {
        "calories_per_100ml": 0,
        "carbs_per_100ml": 0,
        "sugar_per_100ml": 0,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["nuoc loc", "nuoc suoi", "water", "nước suối", "nuoc tinh khiet"],
        "category": "drink"
    },
    
    # === MÓN MIỀN NAM BỔ SUNG ===
    "hủ tiếu": {
        "calories_per_100g": 120,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 6,
        "fat_per_100g": 2,
        "fiber_per_100g": 1,
        "aliases": ["hu tieu", "hủ tiếu nam vang", "hu tieu nam vang", "hu tieu go"],
        "category": "noodle"
    },
    
    "bánh canh cua": {
        "calories_per_100g": 95,
        "carbs_per_100g": 14,
        "sugar_per_100g": 1.5,
        "protein_per_100g": 6,
        "fat_per_100g": 2,
        "fiber_per_100g": 1,
        "aliases": ["banh canh cua", "bánh canh", "bánh canh ghẹ"],
        "category": "noodle"
    },
    
    "bún mắm": {
        "calories_per_100g": 130,
        "carbs_per_100g": 18,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 4,
        "fiber_per_100g": 2,
        "aliases": ["bun mam", "bún mắm miền tây"],
        "category": "noodle"
    },
    
    "bánh tằm bì": {
        "calories_per_100g": 190,
        "carbs_per_100g": 32,
        "sugar_per_100g": 4,
        "protein_per_100g": 8,
        "fat_per_100g": 5,
        "fiber_per_100g": 2,
        "aliases": ["banh tam bi", "bánh tằm", "banh tam"],
        "category": "combo"
    },
    
    "bánh tráng trộn": {
        "calories_per_100g": 250,
        "carbs_per_100g": 35,
        "sugar_per_100g": 8,
        "protein_per_100g": 6,
        "fat_per_100g": 8,
        "fiber_per_100g": 4,
        "aliases": ["banh trang tron", "bánh tráng tây ninh"],
        "category": "snack"
    },
    
    "cơm tấm sườn bì chả": {
        "calories_per_100g": 190,
        "carbs_per_100g": 26,
        "sugar_per_100g": 3,
        "protein_per_100g": 10,
        "fat_per_100g": 6,
        "fiber_per_100g": 1,
        "aliases": ["com tam suon bi cha", "cơm tấm đặc biệt", "cơm tấm sườn bì"],
        "category": "combo"
    },
    
    "bò kho": {
        "calories_per_100g": 150,
        "carbs_per_100g": 7,
        "sugar_per_100g": 2,
        "protein_per_100g": 18,
        "fat_per_100g": 6,
        "fiber_per_100g": 1,
        "aliases": ["bo kho", "beef stew", "bo kho banh mi"],
        "category": "soup"
    },
    
    "gỏi gà bắp cải": {
        "calories_per_100g": 120,
        "carbs_per_100g": 7,
        "sugar_per_100g": 3,
        "protein_per_100g": 10,
        "fat_per_100g": 5,
        "fiber_per_100g": 2,
        "aliases": ["goi ga", "goi ga bap cai", "chicken salad"],
        "category": "salad"
    },
    
    "lẩu mắm": {
        "calories_per_100g": 100,
        "carbs_per_100g": 6,
        "sugar_per_100g": 1,
        "protein_per_100g": 12,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["lau mam", "lẩu mắm miền tây"],
        "category": "combo"
    },
    
    "bánh pía": {
        "calories_per_100g": 410,
        "carbs_per_100g": 60,
        "sugar_per_100g": 25,
        "protein_per_100g": 7,
        "fat_per_100g": 14,
        "fiber_per_100g": 2,
        "aliases": ["banh pia", "pia", "bánh pía sầu riêng"],
        "category": "dessert"
    },
    
    "chè ba màu": {
        "calories_per_100g": 120,
        "carbs_per_100g": 27,
        "sugar_per_100g": 18,
        "protein_per_100g": 3,
        "fat_per_100g": 2,
        "fiber_per_100g": 2,
        "aliases": ["che ba mau", "chè 3 màu"],
        "category": "dessert"
    },
    
    "chè đậu xanh": {
        "calories_per_100g": 110,
        "carbs_per_100g": 24,
        "sugar_per_100g": 15,
        "protein_per_100g": 4,
        "fat_per_100g": 1,
        "fiber_per_100g": 2,
        "aliases": ["che dau xanh", "chè đậu", "che dau"],
        "category": "dessert"
    },
    
    "sâm bổ lượng": {
        "calories_per_100g": 95,
        "carbs_per_100g": 22,
        "sugar_per_100g": 15,
        "protein_per_100g": 1,
        "fat_per_100g": 0.5,
        "fiber_per_100g": 1,
        "aliases": ["sam bo luong", "chè sâm bổ lượng"],
        "category": "dessert"
    },
    
    "hủ tiếu mỹ tho": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["hu tieu my tho", "hu tieu mytho"],
        "category": "noodle"
    },

    "hủ tiếu nam vang": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["hu tieu nam vang", "hu tieu namvang"],
        "category": "noodle"
    },

    "hủ tiếu sa đéc": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["hu tieu sa dec", "hu tieu sadec"],
        "category": "noodle"
    },

    "hủ tiếu gõ": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["hu tieu go"],
        "category": "noodle"
    },

    "hủ tiếu bò kho": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["hu tieu bo kho"],
        "category": "noodle"
    },

    "bánh canh ghẹ": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["banh canh ghe"],
        "category": "noodle"
    },

    "bánh canh cá lóc": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["banh canh ca loc"],
        "category": "noodle"
    },

    "bánh canh chả cá": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["banh canh cha ca"],
        "category": "noodle"
    },

    "bún nước lèo": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun nuoc leo"],
        "category": "noodle"
    },

    "bún cá châu đốc": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun ca chau doc", "bun ca chaudoc"],
        "category": "noodle"
    },

    "bún kèn": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun ken"],
        "category": "noodle"
    },

    "bún mắm sóc trăng": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun mam soc trang", "bun mam soctrang"],
        "category": "noodle"
    },

    "bún gỏi dà": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun goi da"],
        "category": "noodle"
    },

    "bún bò cay bạc liêu": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun bo cay bac lieu", "bun bo cay baclieu"],
        "category": "noodle"
    },

    "bún quậy phú quốc": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun quay phu quoc", "bun quay phuquoc"],
        "category": "noodle"
    },

    "bánh tằm bì nước cốt dừa": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh tam bi nuoc cot dua", "banh tam bi nuoc dua"],
        "category": "combo"
    },

    "bánh cống": {
        "calories_per_100g": 260,
        "carbs_per_100g": 35,
        "sugar_per_100g": 10,
        "protein_per_100g": 6,
        "fat_per_100g": 9,
        "fiber_per_100g": 2,
        "aliases": ["banh cong"],
        "category": "snack"
    },

    "bánh tráng trộn tây ninh": {
        "calories_per_100g": 260,
        "carbs_per_100g": 35,
        "sugar_per_100g": 10,
        "protein_per_100g": 6,
        "fat_per_100g": 9,
        "fiber_per_100g": 2,
        "aliases": ["banh trang tron tay ninh", "banh trang tron"],
        "category": "snack"
    },

    "bánh tráng phơi sương": {
        "calories_per_100g": 260,
        "carbs_per_100g": 35,
        "sugar_per_100g": 10,
        "protein_per_100g": 6,
        "fat_per_100g": 9,
        "fiber_per_100g": 2,
        "aliases": ["banh trang phoi suong"],
        "category": "snack"
    },

    "bánh phồng tôm sa giang": {
        "calories_per_100g": 260,
        "carbs_per_100g": 35,
        "sugar_per_100g": 10,
        "protein_per_100g": 6,
        "fat_per_100g": 9,
        "fiber_per_100g": 2,
        "aliases": ["banh phong tom sa giang", "banh phong tom"],
        "category": "snack"
    },

    "bánh tét trà cuôn": {
        "calories_per_100g": 190,
        "carbs_per_100g": 38,
        "sugar_per_100g": 3,
        "protein_per_100g": 4,
        "fat_per_100g": 3,
        "fiber_per_100g": 1.5,
        "aliases": ["banh tet tra cuon", "banh tet"],
        "category": "carb"
    },

    "bánh da lợn": {
        "calories_per_100g": 230,
        "carbs_per_100g": 40,
        "sugar_per_100g": 25,
        "protein_per_100g": 4,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh da lon"],
        "category": "dessert"
    },

    "bánh bò thốt nốt": {
        "calories_per_100g": 230,
        "carbs_per_100g": 40,
        "sugar_per_100g": 25,
        "protein_per_100g": 4,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh bo thot not"],
        "category": "dessert"
    },

    "bánh chuối nướng": {
        "calories_per_100g": 230,
        "carbs_per_100g": 40,
        "sugar_per_100g": 25,
        "protein_per_100g": 4,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh chuoi nuong"],
        "category": "dessert"
    },

    "bánh chuối hấp": {
        "calories_per_100g": 230,
        "carbs_per_100g": 40,
        "sugar_per_100g": 25,
        "protein_per_100g": 4,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh chuoi hap"],
        "category": "dessert"
    },

    "bánh khoai mì nướng": {
        "calories_per_100g": 230,
        "carbs_per_100g": 40,
        "sugar_per_100g": 25,
        "protein_per_100g": 4,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh khoai mi nuong"],
        "category": "dessert"
    },

    "bánh khoai mì hấp": {
        "calories_per_100g": 230,
        "carbs_per_100g": 40,
        "sugar_per_100g": 25,
        "protein_per_100g": 4,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh khoai mi hap"],
        "category": "dessert"
    },

    "bánh cam": {
        "calories_per_100g": 230,
        "carbs_per_100g": 40,
        "sugar_per_100g": 25,
        "protein_per_100g": 4,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh cam"],
        "category": "dessert"
    },

    "bánh tiêu": {
        "calories_per_100g": 260,
        "carbs_per_100g": 35,
        "sugar_per_100g": 10,
        "protein_per_100g": 6,
        "fat_per_100g": 9,
        "fiber_per_100g": 2,
        "aliases": ["banh tieu"],
        "category": "snack"
    },

    "bánh mì phá lấu": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh mi pha lau", "pha lau banh mi"],
        "category": "combo"
    },

    "bánh mì thịt nướng": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh mi thit nuong"],
        "category": "combo"
    },

    "cơm cháy chà bông": {
        "calories_per_100g": 190,
        "carbs_per_100g": 38,
        "sugar_per_100g": 3,
        "protein_per_100g": 4,
        "fat_per_100g": 3,
        "fiber_per_100g": 1.5,
        "aliases": ["com chay cha bong"],
        "category": "carb"
    },

    "cơm gà xối mỡ": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["com ga xoi mo"],
        "category": "combo"
    },

    "cơm cháy kho quẹt": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["com chay kho quet"],
        "category": "combo"
    },

    "cơm hấp lá sen": {
        "calories_per_100g": 125,
        "carbs_per_100g": 26,
        "sugar_per_100g": 0.5,
        "protein_per_100g": 2.8,
        "fat_per_100g": 1.2,
        "fiber_per_100g": 1.5,
        "aliases": ["com hap la sen", "com la sen"],
        "category": "rice"
    },

    "cá lóc nướng trui": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca loc nuong trui"],
        "category": "fish"
    },

    "cá kèo kho tộ": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca keo kho to"],
        "category": "fish"
    },

    "cá linh kho mía": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca linh kho mia"],
        "category": "fish"
    },

    "cá basa kho tộ": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca basa kho to"],
        "category": "fish"
    },

    "cá bống kho tiêu": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca bong kho tieu"],
        "category": "fish"
    },

    "cá trê nướng muối ớt": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca tre nuong muoi ot"],
        "category": "fish"
    },

    "cá rô kho tộ": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca ro kho to"],
        "category": "fish"
    },

    "cá lóc hấp bầu": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca loc hap bau"],
        "category": "fish"
    },

    "cá diêu hồng hấp xì dầu": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca dieu hong hap xi dau"],
        "category": "fish"
    },

    "cá lóc chiên xù": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca loc chien xu"],
        "category": "fish"
    },

    "cá hú kho tộ": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca hu kho to"],
        "category": "fish"
    },

    "cá bống mú hấp gừng": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca bong mu hap gung"],
        "category": "fish"
    },

    "cá tra kho tiêu": {
        "calories_per_100g": 155,
        "carbs_per_100g": 3,
        "sugar_per_100g": 1,
        "protein_per_100g": 22,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["ca tra kho tieu"],
        "category": "fish"
    },

    "cá lóc nấu canh chua": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["ca loc nau canh chua"],
        "category": "soup"
    },

    "canh chua cá basa": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["canh chua ca basa"],
        "category": "soup"
    },

    "canh chua cá hú": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["canh chua ca hu"],
        "category": "soup"
    },

    "canh chua cá kèo": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["canh chua ca keo"],
        "category": "soup"
    },

    "canh chua cá lóc bông súng": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["canh chua ca loc bong sung"],
        "category": "soup"
    },

    "canh chua bông điên điển": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["canh chua bong dien dien"],
        "category": "soup"
    },

    "canh rau đắng cá rô": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["canh rau dang ca ro"],
        "category": "soup"
    },

    "canh khổ qua dồn thịt": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["canh kho qua don thit"],
        "category": "soup"
    },

    "khổ qua xào trứng": {
        "calories_per_100g": 80,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 3,
        "fat_per_100g": 3,
        "fiber_per_100g": 3,
        "aliases": ["kho qua xao trung"],
        "category": "vegetable"
    },

    "lẩu cá linh bông điên điển": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["lau ca linh bong dien dien"],
        "category": "combo"
    },

    "lẩu cá kèo": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["lau ca keo"],
        "category": "combo"
    },

    "lẩu cá bông lau": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["lau ca bong lau"],
        "category": "combo"
    },

    "lẩu cua đồng miền tây": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["lau cua dong mien tay"],
        "category": "combo"
    },

    "lẩu ốc len": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["lau oc len"],
        "category": "combo"
    },

    "lẩu gà lá giang": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["lau ga la giang"],
        "category": "combo"
    },

    "lẩu bò thố đá": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["lau bo tho da"],
        "category": "combo"
    },

    "lẩu dê sữa": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["lau de sua"],
        "category": "combo"
    },

    "bò kho bánh mì": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["bo kho banh mi"],
        "category": "combo"
    },

    "bò nhúng giấm": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["bo nhung giam"],
        "category": "combo"
    },

    "bò xào lá cách": {
        "calories_per_100g": 220,
        "carbs_per_100g": 5,
        "sugar_per_100g": 3,
        "protein_per_100g": 20,
        "fat_per_100g": 12,
        "fiber_per_100g": 0,
        "aliases": ["bo xao la cach"],
        "category": "meat"
    },

    "vịt nấu chao": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["vit nau chao"],
        "category": "combo"
    },

    "vịt quay mật ong": {
        "calories_per_100g": 220,
        "carbs_per_100g": 5,
        "sugar_per_100g": 3,
        "protein_per_100g": 20,
        "fat_per_100g": 12,
        "fiber_per_100g": 0,
        "aliases": ["vit quay mat ong"],
        "category": "meat"
    },

    "gà hấp rượu dừa": {
        "calories_per_100g": 220,
        "carbs_per_100g": 5,
        "sugar_per_100g": 3,
        "protein_per_100g": 20,
        "fat_per_100g": 12,
        "fiber_per_100g": 0,
        "aliases": ["ga hap ruou dua"],
        "category": "meat"
    },

    "gà tiềm ớt hiểm": {
        "calories_per_100g": 220,
        "carbs_per_100g": 5,
        "sugar_per_100g": 3,
        "protein_per_100g": 20,
        "fat_per_100g": 12,
        "fiber_per_100g": 0,
        "aliases": ["ga tiem ot hiem"],
        "category": "meat"
    },

    "heo quay bánh hỏi": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["heo quay banh hoi"],
        "category": "combo"
    },

    "phá lấu heo": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["pha lau heo"],
        "category": "combo"
    },

    "phá lấu bò": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["pha lau bo"],
        "category": "combo"
    },

    "kho quẹt": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["kho quet"],
        "category": "combo"
    },

    "mắm thái trộn": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["mam thai tron"],
        "category": "combo"
    },

    "mắm ruốc xào sả": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["mam ruoc xao sa"],
        "category": "combo"
    },

    "gỏi sầu đâu tôm thịt": {
        "calories_per_100g": 140,
        "carbs_per_100g": 12,
        "sugar_per_100g": 6,
        "protein_per_100g": 10,
        "fat_per_100g": 6,
        "fiber_per_100g": 3,
        "aliases": ["goi sau dau tom thit"],
        "category": "salad"
    },

    "gỏi ngó sen tôm thịt": {
        "calories_per_100g": 140,
        "carbs_per_100g": 12,
        "sugar_per_100g": 6,
        "protein_per_100g": 10,
        "fat_per_100g": 6,
        "fiber_per_100g": 3,
        "aliases": ["goi ngo sen tom thit"],
        "category": "salad"
    },

    "gỏi đu đủ tôm thịt": {
        "calories_per_100g": 140,
        "carbs_per_100g": 12,
        "sugar_per_100g": 6,
        "protein_per_100g": 10,
        "fat_per_100g": 6,
        "fiber_per_100g": 3,
        "aliases": ["goi du du tom thit"],
        "category": "salad"
    },

    "gỏi xoài khô cá sặc": {
        "calories_per_100g": 140,
        "carbs_per_100g": 12,
        "sugar_per_100g": 6,
        "protein_per_100g": 10,
        "fat_per_100g": 6,
        "fiber_per_100g": 3,
        "aliases": ["goi xoai kho ca sac"],
        "category": "salad"
    },

    "gỏi khô bò miếng": {
        "calories_per_100g": 140,
        "carbs_per_100g": 12,
        "sugar_per_100g": 6,
        "protein_per_100g": 10,
        "fat_per_100g": 6,
        "fiber_per_100g": 3,
        "aliases": ["goi kho bo mieng"],
        "category": "salad"
    },

    "gỏi tôm thịt bông điên điển": {
        "calories_per_100g": 140,
        "carbs_per_100g": 12,
        "sugar_per_100g": 6,
        "protein_per_100g": 10,
        "fat_per_100g": 6,
        "fiber_per_100g": 3,
        "aliases": ["goi tom thit bong dien dien"],
        "category": "salad"
    },

    "gỏi cá trích phú quốc": {
        "calories_per_100g": 140,
        "carbs_per_100g": 12,
        "sugar_per_100g": 6,
        "protein_per_100g": 10,
        "fat_per_100g": 6,
        "fiber_per_100g": 3,
        "aliases": ["goi ca trich phu quoc"],
        "category": "salad"
    },

    "gỏi cuốn tôm đất": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["goi cuon tom dat"],
        "category": "combo"
    },

    "cháo cá lóc": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["chao ca loc"],
        "category": "soup"
    },

    "cháo lòng miền tây": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["chao long mien tay"],
        "category": "soup"
    },

    "cháo cua đồng": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["chao cua dong"],
        "category": "soup"
    },

    "cháo vịt": {
        "calories_per_100g": 95,
        "carbs_per_100g": 10,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["chao vit"],
        "category": "soup"
    },

    "bún măng vịt": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun mang vit"],
        "category": "noodle"
    },

    "bún thịt nướng chả giò miền tây": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun thit nuong cha gio mien tay"],
        "category": "noodle"
    },

    "bún ốc rau đắng": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun oc rau dang"],
        "category": "noodle"
    },

    "bún cua đồng": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun cua dong"],
        "category": "noodle"
    },

    "bún giò heo nước lèo": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun gio heo nuoc leo"],
        "category": "noodle"
    },

    "bún riêu cua đồng miền tây": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun rieu cua dong mien tay"],
        "category": "noodle"
    },

    "bún tôm khô": {
        "calories_per_100g": 130,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun tom kho"],
        "category": "noodle"
    },

    "bánh hỏi thịt nướng": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh hoi thit nuong"],
        "category": "combo"
    },

    "bánh hỏi lòng heo": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh hoi long heo"],
        "category": "combo"
    },

    "bánh ướt lòng gà": {
        "calories_per_100g": 185,
        "carbs_per_100g": 25,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 7,
        "fiber_per_100g": 2,
        "aliases": ["banh uot long ga"],
        "category": "combo"
    },

    "thịt giả cầy": {
        "calories_per_100g": 230,
        "carbs_per_100g": 4,
        "sugar_per_100g": 2,
        "protein_per_100g": 22,
        "fat_per_100g": 15,
        "fiber_per_100g": 0.5,
        "aliases": ["thit gia cay", "gia cay"],
        "category": "meat"
    },

    "thịt chó": {
        "calories_per_100g": 260,
        "carbs_per_100g": 0,
        "sugar_per_100g": 0,
        "protein_per_100g": 24,
        "fat_per_100g": 18,
        "fiber_per_100g": 0,
        "aliases": ["thit cho"],
        "category": "meat"
    },

    "mì cay hàn quốc": {
        "calories_per_100g": 170,
        "carbs_per_100g": 28,
        "sugar_per_100g": 4,
        "protein_per_100g": 6,
        "fat_per_100g": 5,
        "fiber_per_100g": 2,
        "aliases": ["mi cay han quoc", "mì cay", "spicy korean noodle"],
        "category": "noodle"
    },

    "cơm xèo": {
        "calories_per_100g": 210,
        "carbs_per_100g": 35,
        "sugar_per_100g": 2,
        "protein_per_100g": 6,
        "fat_per_100g": 5,
        "fiber_per_100g": 2,
        "aliases": ["com xeo"],
        "category": "rice"
    },

    "trà sữa trân châu": {
        "calories_per_100ml": 90,
        "carbs_per_100ml": 16,
        "sugar_per_100ml": 14,
        "protein_per_100ml": 1,
        "fat_per_100ml": 2,
        "fiber_per_100ml": 0.5,
        "aliases": ["tra sua tran chau", "bubble milk tea", "boba tea", "tra sua"],
        "category": "drink"
    },

    "matcha": {
        "calories_per_100ml": 60,
        "carbs_per_100ml": 10,
        "sugar_per_100ml": 6,
        "protein_per_100ml": 2,
        "fat_per_100ml": 1,
        "fiber_per_100ml": 0.5,
        "aliases": ["tra xanh matcha", "matcha latte", "matcha da xay"],
        "category": "drink"
    },

    "latte": {
        "calories_per_100ml": 60,
        "carbs_per_100ml": 6,
        "sugar_per_100ml": 5,
        "protein_per_100ml": 3,
        "fat_per_100ml": 3,
        "fiber_per_100ml": 0,
        "aliases": ["cafe latte", "latte sua"],
        "category": "drink"
    },

    "rượu soju": {
        "calories_per_100ml": 130,
        "carbs_per_100ml": 0,
        "sugar_per_100ml": 0,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["ruou soju", "soju"],
        "category": "drink"
    },

    "rượu sake": {
        "calories_per_100ml": 134,
        "carbs_per_100ml": 5,
        "sugar_per_100ml": 2,
        "protein_per_100ml": 0.5,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["ruou sake", "sake"],
        "category": "drink"
    },

    "rượu vodka": {
        "calories_per_100ml": 231,
        "carbs_per_100ml": 0,
        "sugar_per_100ml": 0,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["ruou vodka", "vodka"],
        "category": "drink"
    },

    "rượu whiskey": {
        "calories_per_100ml": 250,
        "carbs_per_100ml": 0,
        "sugar_per_100ml": 0,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["ruou whiskey", "whiskey", "whisky"],
        "category": "drink"
    },

    "rượu gin": {
        "calories_per_100ml": 263,
        "carbs_per_100ml": 0,
        "sugar_per_100ml": 0,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["ruou gin", "gin"],
        "category": "drink"
    },

    "rượu rum": {
        "calories_per_100ml": 231,
        "carbs_per_100ml": 0,
        "sugar_per_100ml": 0,
        "protein_per_100ml": 0,
        "fat_per_100ml": 0,
        "fiber_per_100ml": 0,
        "aliases": ["ruou rum", "rum"],
        "category": "drink"
    },

    "lẩu cá cải chua": {
        "calories_per_100g": 110,
        "carbs_per_100g": 8,
        "sugar_per_100g": 2,
        "protein_per_100g": 12,
        "fat_per_100g": 4,
        "fiber_per_100g": 1,
        "aliases": ["lau ca cai chua", "lau ca cai"],
        "category": "combo"
    },
    
    "thịt cầy": {
        "calories_per_100g": 260,
        "carbs_per_100g": 0,
        "sugar_per_100g": 0,
        "protein_per_100g": 24,
        "fat_per_100g": 18,
        "fiber_per_100g": 0,
        "aliases": ["thit cay", "thit cho", "cầy tơ"],
        "category": "meat"
    },
    
    "thịt mèo": {
        "calories_per_100g": 230,
        "carbs_per_100g": 0,
        "sugar_per_100g": 0,
        "protein_per_100g": 23,
        "fat_per_100g": 15,
        "fiber_per_100g": 0,
        "aliases": ["thit meo", "mèo"],
        "category": "meat"
    },
    
    "thịt dê": {
        "calories_per_100g": 240,
        "carbs_per_100g": 0,
        "sugar_per_100g": 0,
        "protein_per_100g": 25,
        "fat_per_100g": 15,
        "fiber_per_100g": 0,
        "aliases": ["thit de", "dê", "de"],
        "category": "meat"
    },
    
    "thịt cừu": {
        "calories_per_100g": 250,
        "carbs_per_100g": 0,
        "sugar_per_100g": 0,
        "protein_per_100g": 24,
        "fat_per_100g": 17,
        "fiber_per_100g": 0,
        "aliases": ["thit cuu", "cừu nướng", "cuu"],
        "category": "meat"
    },
    
    "thịt nhím": {
        "calories_per_100g": 210,
        "carbs_per_100g": 0,
        "sugar_per_100g": 0,
        "protein_per_100g": 22,
        "fat_per_100g": 12,
        "fiber_per_100g": 0,
        "aliases": ["thit nhim", "nhím"],
        "category": "meat"
    },
    
    "mì ý": {
        "calories_per_100g": 158,
        "carbs_per_100g": 30,
        "sugar_per_100g": 2,
        "protein_per_100g": 6,
        "fat_per_100g": 3,
        "fiber_per_100g": 2,
        "aliases": ["mi y", "spaghetti", "pasta"],
        "category": "pasta"
    },
    
    "lạp xưởng nướng đá": {
        "calories_per_100g": 320,
        "carbs_per_100g": 10,
        "sugar_per_100g": 5,
        "protein_per_100g": 20,
        "fat_per_100g": 22,
        "fiber_per_100g": 0,
        "aliases": ["lap xuong nuong da", "lạp xưởng", "lap xuong"],
        "category": "meat"
    },
    
    "bánh đồng xu": {
        "calories_per_100g": 270,
        "carbs_per_100g": 40,
        "sugar_per_100g": 18,
        "protein_per_100g": 6,
        "fat_per_100g": 9,
        "fiber_per_100g": 2,
        "aliases": ["banh dong xu", "pancake coin", "banh xu"],
        "category": "dessert"
    },
    
    "lẩu chay": {
        "calories_per_100g": 120,
        "carbs_per_100g": 18,
        "sugar_per_100g": 4,
        "protein_per_100g": 6,
        "fat_per_100g": 4,
        "fiber_per_100g": 2,
        "aliases": ["lau chay", "lẩu rau củ"],
        "category": "combo"
    },
    
    "cơm chay": {
        "calories_per_100g": 140,
        "carbs_per_100g": 30,
        "sugar_per_100g": 1,
        "protein_per_100g": 4,
        "fat_per_100g": 3,
        "fiber_per_100g": 2,
        "aliases": ["com chay", "cơm rau củ"],
        "category": "rice"
    },
    
    "gà rán": {
        "calories_per_100g": 260,
        "carbs_per_100g": 5,
        "sugar_per_100g": 1,
        "protein_per_100g": 23,
        "fat_per_100g": 16,
        "fiber_per_100g": 0,
        "aliases": ["ga ran", "fried chicken", "gà chiên"],
        "category": "meat"
    },
    
    "cơm cháy tỏi": {
        "calories_per_100g": 220,
        "carbs_per_100g": 40,
        "sugar_per_100g": 2,
        "protein_per_100g": 5,
        "fat_per_100g": 5,
        "fiber_per_100g": 1.5,
        "aliases": ["com chay toi", "cơm cháy"],
        "category": "carb"
    },
    
    "kho quẹt": {
        "calories_per_100g": 200,
        "carbs_per_100g": 20,
        "sugar_per_100g": 6,
        "protein_per_100g": 10,
        "fat_per_100g": 8,
        "fiber_per_100g": 1,
        "aliases": ["kho quet", "khoquet"],
        "category": "combo"
    },
    
    "cơm xá xíu": {
        "calories_per_100g": 210,
        "carbs_per_100g": 30,
        "sugar_per_100g": 5,
        "protein_per_100g": 12,
        "fat_per_100g": 6,
        "fiber_per_100g": 1.5,
        "aliases": ["com xa xiu", "cơm thịt xá xíu"],
        "category": "combo"
    },
    
    "bánh canh": {
        "calories_per_100g": 120,
        "carbs_per_100g": 22,
        "sugar_per_100g": 2,
        "protein_per_100g": 6,
        "fat_per_100g": 2,
        "fiber_per_100g": 1,
        "aliases": ["banh canh"],
        "category": "noodle"
    },
    
    "bún riêu": {
        "calories_per_100g": 110,
        "carbs_per_100g": 18,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1.5,
        "aliases": ["bun rieu", "bún riêu cua"],
        "category": "noodle"
    },
    
    "bún đỏ": {
        "calories_per_100g": 120,
        "carbs_per_100g": 20,
        "sugar_per_100g": 3,
        "protein_per_100g": 7,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun do", "bún đỏ buôn mê thuột"],
        "category": "noodle"
    },
    
    "bún cua": {
        "calories_per_100g": 115,
        "carbs_per_100g": 19,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 3,
        "fiber_per_100g": 1,
        "aliases": ["bun cua"],
        "category": "noodle"
    },
    
    "cua rang me": {
        "calories_per_100g": 180,
        "carbs_per_100g": 10,
        "sugar_per_100g": 6,
        "protein_per_100g": 20,
        "fat_per_100g": 6,
        "fiber_per_100g": 0,
        "aliases": ["cua rang me", "cua xao me"],
        "category": "seafood"
    },
    
    "mì cay": {
        "calories_per_100g": 155,
        "carbs_per_100g": 25,
        "sugar_per_100g": 3,
        "protein_per_100g": 7,
        "fat_per_100g": 4,
        "fiber_per_100g": 2,
        "aliases": ["mi cay", "mỳ cay"],
        "category": "noodle"
    },
    
    "mì cay hải sản": {
        "calories_per_100g": 160,
        "carbs_per_100g": 26,
        "sugar_per_100g": 3,
        "protein_per_100g": 8,
        "fat_per_100g": 4,
        "fiber_per_100g": 2,
        "aliases": ["mi cay hai san", "mỳ cay hải sản"],
        "category": "noodle"
    },
}

# Bổ sung nhanh >100 món ăn Việt phổ biến để tăng độ phủ
VIETNAMESE_DEFAULT_MACROS = {
    "rice": (165, 34, 1.5, 4, 2, 1.5),
    "noodle": (135, 24, 2, 7, 3, 1),
    "combo": (195, 26, 6, 12, 7, 2),
    "soup": (85, 10, 2, 6, 3, 1),
    "snack": (260, 32, 10, 6, 12, 2),
    "dessert": (230, 38, 24, 4, 8, 2),
    "cake": (210, 34, 18, 5, 8, 2),
    "meat": (235, 3, 1, 24, 15, 0),
    "seafood": (150, 4, 1, 22, 6, 0),
    "salad": (95, 12, 4, 5, 4, 3),
    "sandwich": (220, 30, 6, 10, 8, 2),
    "drink": (45, 11, 10, 0.5, 0, 0),
    "roll": (155, 24, 4, 8, 5, 2),
    "egg": (155, 1, 0.3, 13, 11, 0),
    "fried": (240, 20, 4, 13, 13, 1)
}

VIETNAMESE_ADDITIONAL_FOODS = [
    ("xôi", "rice", ["xoi", "xoi trang"]),
    ("xôi gấc", "rice", ["xoi gac"]),
    ("xôi bắp", "rice", ["xoi bap", "xoi ngo"]),
    ("xôi đậu xanh", "rice", ["xoi dau xanh", "xoi dau"]),
    ("xôi đậu phộng", "rice", ["xoi dau phong", "xoi lac", "xoi dau phong rang"]),
    ("xôi xéo", "rice", ["xoi xeo"]),
    ("xôi gà", "combo", ["xoi ga"]),
    ("xôi mặn", "combo", ["xoi man"]),
    ("xôi dừa", "rice", ["xoi dua"]),
    ("xôi lá cẩm", "rice", ["xoi la cam"]),
    ("xôi khúc", "combo", ["xoi khuc", "xoi thit"]),
    ("xôi vò", "rice", ["xoi vo"]),
    ("súp cua", "soup", ["sup cua"]),
    ("súp gà", "soup", ["sup ga"]),
    ("súp bắp", "soup", ["sup bap", "sup ngo"]),
    ("súp hải sản", "soup", ["sup hai san"]),
    ("súp nấm", "soup", ["sup nam"]),
    ("bún thịt nướng", "noodle", ["bun thit nuong"]),
    ("bún chả cá", "noodle", ["bun cha ca"]),
    ("bún đậu mắm tôm", "noodle", ["bun dau mam tom", "bun dau"]),
    ("bún mọc", "noodle", ["bun moc"]),
    ("bún dọc mùng", "noodle", ["bun doc mung"]),
    ("bún bung", "noodle", ["bun bung"]),
    ("bún thang", "noodle", ["bun thang"]),
    ("bún thái", "noodle", ["bun thai"]),
    ("bún ốc", "noodle", ["bun oc"]),
    ("bún sứa", "noodle", ["bun sua"]),
    ("bún gà", "noodle", ["bun ga"]),
    ("bún tôm", "noodle", ["bun tom"]),
    ("bún riêu cua đồng", "noodle", ["bun rieu cua dong"]),
    ("bún măng bò", "noodle", ["bun mang bo"]),
    ("miến gà", "noodle", ["mien ga"]),
    ("miến lươn", "noodle", ["mien luon"]),
    ("miến măng vịt", "noodle", ["mien mang vit"]),
    ("miến trộn", "noodle", ["mien tron"]),
    ("miến xào cua", "noodle", ["mien xao cua"]),
    ("miến xào bò", "noodle", ["mien xao bo"]),
    ("miến xào hải sản", "noodle", ["mien xao hai san"]),
    ("phở gà", "noodle", ["pho ga"]),
    ("phở cuốn", "combo", ["pho cuon"]),
    ("phở trộn", "noodle", ["pho tron"]),
    ("phở xào bò", "noodle", ["pho xao bo"]),
    ("mì quảng", "noodle", ["mi quang"]),
    ("mì hoành thánh", "noodle", ["mi hoanh thanh", "mi wonton"]),
    ("mì vịt tiềm", "noodle", ["mi vit tiem"]),
    ("mì gà tần", "noodle", ["mi ga tan"]),
    ("mì xào giòn", "noodle", ["mi xao gion"]),
    ("mì xào hải sản", "noodle", ["mi xao hai san"]),
    ("mì xào bò", "noodle", ["mi xao bo"]),
    ("hủ tiếu xào", "noodle", ["hu tieu xao"]),
    ("hủ tiếu hồ", "noodle", ["hu tieu ho"]),
    ("cơm chiên dương châu", "combo", ["com chien duong chau", "duong chau fried rice"]),
    ("cơm gà hội an", "combo", ["com ga hoi an"]),
    ("cơm gà xé", "combo", ["com ga xe"]),
    ("cơm lam", "rice", ["com lam"]),
    ("cơm niêu", "rice", ["com nieu"]),
    ("cơm heo quay", "combo", ["com heo quay"]),
    ("cơm gà nướng", "combo", ["com ga nuong"]),
    ("cơm sườn bì", "combo", ["com suon bi"]),
    ("cơm bò lúc lắc", "combo", ["com bo luc lac"]),
    ("cơm rang thập cẩm", "combo", ["com rang thap cam"]),
    ("cơm chay thập cẩm", "combo", ["com chay thap cam"]),
    ("cơm trộn bibimbap", "combo", ["com tron han", "bibimbap viet"]),
    ("cơm gà xối mỡ da giòn", "combo", ["com ga xoi mo da gion"]),
    ("bánh cuốn", "combo", ["banh cuon"]),
    ("bánh ướt thịt nướng", "combo", ["banh uot thit nuong"]),
    ("bánh bèo", "cake", ["banh beo"]),
    ("bánh bột lọc", "cake", ["banh bot loc"]),
    ("bánh nậm", "cake", ["banh nam"]),
    ("bánh ít trần", "cake", ["banh it tran"]),
    ("bánh ít lá gai", "dessert", ["banh it la gai"]),
    ("bánh gối", "fried", ["banh goi", "pillow dumpling"]),
    ("bánh giò", "cake", ["banh gio"]),
    ("bánh khọt", "cake", ["banh khot"]),
    ("bánh đúc", "cake", ["banh duc"]),
    ("bánh căn", "cake", ["banh can"]),
    ("bánh tráng nướng", "snack", ["banh trang nuong", "banh trang pizza"]),
    ("bánh tráng cuốn thịt heo", "combo", ["banh trang cuon thit heo"]),
    ("bánh tráng me", "snack", ["banh trang me"]),
    ("bánh hỏi heo quay", "combo", ["banh hoi heo quay"]),
    ("bánh mì thổ nhĩ kỳ", "sandwich", ["banh mi tho nhi ky", "doner viet", "banh mi doner"]),
    ("bánh mì chảo", "combo", ["banh mi chao"]),
    ("bánh mì pate", "sandwich", ["banh mi pate"]),
    ("bánh mì ốp la", "sandwich", ["banh mi op la"]),
    ("bánh mì xíu mại", "sandwich", ["banh mi xiu mai"]),
    ("bánh flan", "dessert", ["flan", "caramen"]),
    ("bánh phu thê", "dessert", ["banh phu the"]),
    ("bánh pía sầu riêng", "dessert", ["banh pia sau rieng"]),
    ("bánh gai", "dessert", ["banh gai"]),
    ("bánh tro", "dessert", ["banh tro"]),
    ("bánh thuẫn", "dessert", ["banh thuan"]),
    ("bánh in đậu xanh", "dessert", ["banh in dau xanh"]),
    ("bánh đậu xanh hải dương", "dessert", ["banh dau xanh hai duong"]),
    ("ram lụi", "roll", ["ram lui", "nem lui", "ram nem lui"]),
    ("ram bắp", "roll", ["ram bap"]),
    ("ram tôm thịt", "roll", ["ram tom thit"]),
    ("nem nướng nha trang", "roll", ["nem nuong nha trang"]),
    ("nem chua rán", "snack", ["nem chua ran"]),
    ("nem hải sản", "roll", ["nem hai san"]),
    ("nem phùng", "roll", ["nem phung"]),
    ("chả ram bắp", "roll", ["cha ram bap"]),
    ("chả ốc", "roll", ["cha oc"]),
    ("cá viên chiên", "snack", ["ca vien chien"]),
    ("mực viên chiên", "snack", ["muc vien chien"]),
    ("bò viên chiên", "snack", ["bo vien chien"]),
    ("xúc xích nướng", "snack", ["xuc xich nuong"]),
    ("bắp xào", "snack", ["bap xao"]),
    ("bắp rang bơ", "snack", ["bap rang bo", "popcorn"]),
    ("kem xôi", "dessert", ["kem xoi"]),
    ("sữa chua nếp cẩm", "dessert", ["sua chua nep cam", "yaourt nep cam"]),
    ("yaourt đá", "drink", ["yaourt da", "sua chua da"]),
    ("sâm bí đao", "drink", ["sam bi dao"]),
    ("sâm dứa", "drink", ["sam dua"]),
    ("nước sâm", "drink", ["nuoc sam"]),
    ("nước mát", "drink", ["nuoc mat"]),
    ("rau má đậu xanh", "drink", ["rau ma dau xanh", "nuoc rau ma dau xanh"]),
    ("nước mía sầu riêng", "drink", ["nuoc mia sau rieng"]),
    ("trà tắc", "drink", ["tra tac"]),
    ("nước nha đam", "drink", ["nuoc nha dam", "nuoc aloe"]),
    ("dừa tắc", "drink", ["dua tac"]),
    ("sữa bắp", "drink", ["sua bap", "nuoc bap"]),
    ("sữa gạo rang", "drink", ["sua gao rang"]),
    ("sương sáo", "drink", ["suong sao", "thach suong sao"]),
    ("ốc nhồi thịt", "seafood", ["oc nhoi thit", "oc hap thit"]),
    ("ốc len xào dừa", "seafood", ["oc len xao dua"]),
    ("ốc hương nướng", "seafood", ["oc huong nuong"]),
    ("nghêu hấp sả", "seafood", ["ngheu hap sa"]),
    ("sò điệp nướng mỡ hành", "seafood", ["so diep nuong mo hanh"]),
    ("hàu nướng phô mai", "seafood", ["hau nuong pho mai"]),
    ("tôm nướng muối ớt", "seafood", ["tom nuong muoi ot"]),
    ("tôm sú hấp", "seafood", ["tom su hap"]),
    ("tôm rim mặn", "seafood", ["tom rim man"]),
    ("mực nhồi thịt", "seafood", ["muc nhoi thit"]),
    ("hàu né", "seafood", ["hau ne"]),
    ("bò xào hành", "meat", ["bo xao hanh"]),
    ("bò lá lốt", "meat", ["bo la lot", "bo nuong la lot"]),
    ("bò né", "meat", ["bo ne"]),
    ("bò kho tiêu xanh", "meat", ["bo kho tieu xanh"]),
    ("bê thui", "meat", ["be thui"]),
    ("dê tái chanh", "meat", ["de tai chanh"]),
    ("gà luộc", "meat", ["ga luoc"]),
    ("gà kho gừng", "meat", ["ga kho gung"]),
    ("gà rang muối", "meat", ["ga rang muoi"]),
    ("gà xào sả ớt", "meat", ["ga xao sa ot"]),
    ("gà tiềm thuốc bắc", "meat", ["ga tiem thuoc bac"]),
    ("gà hấp muối", "meat", ["ga hap muoi"]),
    ("vịt quay bắc kinh", "meat", ["vit quay bac kinh"]),
    ("vịt om sấu", "meat", ["vit om sau"]),
    ("thịt chiên", "meat", ["thit chien", "thit heo chien"]),
    ("thịt kho trứng", "combo", ["thit kho trung", "thit kho tau trung"]),
    ("thịt rim mắm", "meat", ["thit rim mam"]),
    ("thịt băm rang", "meat", ["thit bam rang"]),
    ("thịt quay giòn bì", "meat", ["thit quay gion bi"]),
    ("chả trứng hấp", "combo", ["cha trung hap"]),
    ("thịt kho tàu trứng cút", "combo", ["thit kho tau trung cut"]),
    ("chim cút quay", "meat", ["chim cut quay"]),
    ("chim bồ câu hầm", "meat", ["chim bo cau ham", "chim cu ham", "chim cu"]),
    ("chim câu quay", "meat", ["chim cau quay", "chim cu quay"]),
    ("hột vịt lộn", "egg", ["hot vit lon", "trung vit lon"]),
    ("tiết canh", "combo", ["tiet canh"]),
    ("lươn um", "combo", ["luon um", "luon um rau ngo"]),
    ("cháo lươn", "soup", ["chao luon"]),
    ("lươn xào sả ớt", "meat", ["luon xao sa ot"]),
    ("cháo gà", "soup", ["chao ga"]),
    ("cháo trai", "soup", ["chao trai"]),
    ("canh bầu nấu tôm", "soup", ["canh bau nau tom"]),
    ("canh khổ qua nhồi thịt", "soup", ["canh kho qua nhoi thit"]),
    ("canh rau ngót thịt băm", "soup", ["canh rau ngot thit bam"]),
    ("canh cua mồng tơi", "soup", ["canh cua mong toi"]),
    ("canh bí đỏ nấu tôm", "soup", ["canh bi do nau tom"]),
    ("canh cải nấu thịt", "soup", ["canh cai nau thit"]),
    ("nộm đu đủ bò khô", "salad", ["nom du du bo kho"]),
    ("nộm tai heo", "salad", ["nom tai heo", "goi tai heo"]),
    ("gỏi bò bóp thấu", "salad", ["goi bo bop thau"]),
    ("gỏi bưởi tôm", "salad", ["goi buoi tom"]),
    ("gỏi xoài cá cơm", "salad", ["goi xoai ca com"]),
    ("chè thập cẩm", "dessert", ["che thap cam"]),
    ("chè khúc bạch", "dessert", ["che khuc bach"]),
    ("chè thái sầu riêng", "dessert", ["che thai", "che thai sau rieng"]),
    ("chè trôi nước", "dessert", ["che troi nuoc"]),
    ("chè hạt sen long nhãn", "dessert", ["che hat sen long nhan"]),
    ("chè mè đen", "dessert", ["che me den"]),
    ("chè khoai môn", "dessert", ["che khoai mon"]),
    ("chè hột lựu", "dessert", ["che hot luu", "che hat luu"]),
    ("chè đậu đen", "dessert", ["che dau den"]),
    ("chè đậu đỏ", "dessert", ["che dau do"]),
    ("chè bắp", "dessert", ["che bap"]),
    ("chè sen", "dessert", ["che sen"]),
    ("chè chuối", "dessert", ["che chuoi"]),
    ("chè dừa non", "dessert", ["che dua non"]),
    ("chè đậu xanh đánh", "dessert", ["che dau xanh danh"]),
    ("mứt dừa", "dessert", ["mut dua"]),
    ("mứt gừng", "dessert", ["mut gung"])
]

for name, category, aliases in VIETNAMESE_ADDITIONAL_FOODS:
    defaults = VIETNAMESE_DEFAULT_MACROS.get(category, VIETNAMESE_DEFAULT_MACROS["combo"])
    if name in VIETNAMESE_FOODS_NUTRITION:
        existing_aliases = set(VIETNAMESE_FOODS_NUTRITION[name].get("aliases", []))
        for alias in aliases:
            existing_aliases.add(alias)
        VIETNAMESE_FOODS_NUTRITION[name]["aliases"] = list(existing_aliases)
        continue
    
    if category == "drink":
        calories, carbs, sugar, protein, fat, fiber = defaults
        VIETNAMESE_FOODS_NUTRITION[name] = {
            "calories_per_100ml": calories,
            "carbs_per_100ml": carbs,
            "sugar_per_100ml": sugar,
            "protein_per_100ml": protein,
            "fat_per_100ml": fat,
            "fiber_per_100ml": fiber,
            "aliases": aliases,
            "category": category
        }
    else:
        calories, carbs, sugar, protein, fat, fiber = defaults
        VIETNAMESE_FOODS_NUTRITION[name] = {
            "calories_per_100g": calories,
            "carbs_per_100g": carbs,
            "sugar_per_100g": sugar,
            "protein_per_100g": protein,
            "fat_per_100g": fat,
            "fiber_per_100g": fiber,
            "aliases": aliases,
            "category": category
        }

# Bổ sung danh sách món phổ biến quốc tế
GLOBAL_DEFAULT_MACROS = {
    "pasta": (165, 30, 3, 6, 4, 2),
    "noodle": (130, 22, 2, 7, 3, 1),
    "rice": (140, 30, 1, 3, 2, 1),
    "bread": (250, 45, 10, 8, 4, 2),
    "dessert": (250, 40, 25, 4, 9, 2),
    "snack": (280, 35, 10, 6, 12, 2),
    "meat": (240, 2, 1, 24, 16, 0),
    "seafood": (150, 3, 1, 22, 6, 0),
    "salad": (90, 10, 4, 4, 4, 3),
    "combo": (190, 25, 6, 12, 7, 2),
    "soup": (90, 10, 3, 6, 3, 1),
    "drink": (45, 11, 10, 0.5, 0, 0),
    "sandwich": (220, 30, 6, 10, 8, 2)
}

GLOBAL_POPULAR_FOODS = [
    ("pizza pepperoni", "bread", ["pepperoni pizza"]),
    ("pizza margherita", "bread", ["margherita pizza"]),
    ("hamburger", "sandwich", ["burger"]),
    ("cheeseburger", "sandwich", ["cheese burger"]),
    ("fried chicken", "meat", ["ga ran kfc", "gà rán kfc"]),
    ("hotdog", "sandwich", ["hot dog"]),
    ("fish and chips", "combo", ["fish & chips"]),
    ("steak bò", "meat", ["steak", "beef steak"]),
    ("thịt cừu nướng", "meat", ["lamb chops"]),
    ("roast beef", "meat", ["bo nuong lo"]),
    ("roast chicken", "meat", ["ga quay"]),
    ("cơm chiên trứng", "rice", ["fried rice", "com chien trung"]),
    ("cơm chiên hải sản", "combo", ["seafood fried rice"]),
    ("spaghetti bolognese", "pasta", ["mì ý bolognese"]),
    ("pasta carbonara", "pasta", ["carbonara"]),
    ("lasagna", "pasta", ["lasagne"]),
    ("fettuccine alfredo", "pasta", ["alfredo pasta"]),
    ("mac and cheese", "pasta", ["mac n cheese"]),
    ("risotto", "rice", ["risotto y"]),
    ("gnocchi", "pasta", ["khoai tay gnocchi"]),
    ("caesar salad", "salad", ["salad caesar"]),
    ("greek salad", "salad", ["salad hy lap"]),
    ("cobb salad", "salad", ["salad cobb"]),
    ("tacos", "sandwich", ["taco"]),
    ("burrito", "sandwich", ["burito"]),
    ("quesadilla", "sandwich", ["quesadillas"]),
    ("nachos", "snack", ["nacho"]),
    ("enchilada", "sandwich", ["enchiladas"]),
    ("paella", "combo", ["paella tay ban nha"]),
    ("gazpacho", "soup", ["sup gazpacho"]),
    ("ratatouille", "combo", ["rau cu kho ratatouille"]),
    ("croissant", "bread", ["bánh sừng trâu"]),
    ("baguette", "bread", ["bánh mì pháp"]),
    ("pancakes", "dessert", ["banh pancake"]),
    ("waffles", "dessert", ["banh waffle"]),
    ("crepe", "dessert", ["crepes"]),
    ("apple pie", "dessert", ["banh tao"]),
    ("brownie", "dessert", ["banh brownie"]),
    ("cheesecake", "dessert", ["banh pho mai"]),
    ("chocolate cake", "dessert", ["banh socola"]),
    ("ice cream", "dessert", ["kem", "kem que"]),
    ("donut", "dessert", ["doughnut", "banh donut"]),
    ("cinnamon roll", "dessert", ["banh quế cuộn"]),
    ("shawarma", "sandwich", ["shawarma gà", "shawarma bò"]),
    ("falafel", "snack", ["falafel chay"]),
    ("hummus pita", "sandwich", ["hummus va pita", "pita hummus"]),
    ("kebab", "sandwich", ["doner kebab"]),
    ("pita kebab", "sandwich", ["pita kebab"]),
    ("couscous", "rice", ["cous cous"]),
    ("tabbouleh", "salad", ["salad tabbouleh"]),
    ("sushi roll", "seafood", ["sushi", "roll sushi"]),
    ("sashimi", "seafood", ["sashimi ca hoi"]),
    ("tempura", "seafood", ["tempura tom"]),
    ("ramen", "noodle", ["mi ramen"]),
    ("udon", "noodle", ["mi udon"]),
    ("soba", "noodle", ["mi soba"]),
    ("okonomiyaki", "combo", ["banh xeo nhat"]),
    ("takoyaki", "snack", ["banh bong bot ca"]),
    ("bibimbap", "combo", ["cơm trộn hàn"]),
    ("kimchi stew", "soup", ["kimchi jjigae", "canh kimchi"]),
    ("japchae", "noodle", ["mien tron han"]),
    ("tom yum", "soup", ["canh tom yum"]),
    ("pad thai", "noodle", ["padthai"]),
    ("green curry", "combo", ["ca ri xanh thai"]),
    ("massaman curry", "combo", ["ca ri massaman"]),
    ("butter chicken", "combo", ["ca ri bo gap"]),
    ("chicken tikka masala", "combo", ["tikka masala"]),
    ("biryani", "rice", ["cơm biryani"]),
    ("naan", "bread", ["banh naan"]),
    ("kathi roll", "sandwich", ["kathi roll india"]),
    ("chili con carne", "combo", ["ớt hầm bò"]),
    ("clam chowder", "soup", ["soup chowder"]),
    ("lobster roll", "sandwich", ["banh mi tom hum"]),
    ("ceviche", "seafood", ["ceviche peru"]),
    ("poke bowl", "seafood", ["poke"]),
    ("dimsum", "snack", ["dim sum"]),
    ("mapo tofu", "combo", ["ma po doufu", "dau hu mapo"]),
    ("kung pao chicken", "combo", ["ga kung pao"]),
    ("sweet and sour pork", "combo", ["thit heo chua ngot"]),
    ("bbq pork ribs", "meat", ["suon heo bbq"]),
    ("bbq brisket", "meat", ["uc bo bbq"]),
    ("poutine", "combo", ["khoai tay poutine"]),
    ("coleslaw", "salad", ["salad bap cai"]),
    ("fried plantain", "snack", ["chuoi chien"]),
    ("arepa", "bread", ["arepas"]),
    ("empanada", "snack", ["empanadas"]),
    ("mochi", "dessert", ["mochi nhat"]),
    ("milkshake", "drink", ["sua lắc"]),
    ("cola", "drink", ["coca cola", "coca"]),
    ("sprite", "drink", ["seven up", "7up"]),
    ("lemon tea", "drink", ["tra chanh", "iced lemon tea"]),
    ("iced americano", "drink", ["americano da"]),
    ("espresso", "drink", ["cafe espresso"]),
    ("affogato", "dessert", ["kem affogato"]),
    ("smoothie bowl", "dessert", ["sinh to bowl"]),
    ("protein shake", "drink", ["sua protein"]),
    ("energy drink", "drink", ["nang luong drink"]),
    ("kombucha", "drink", ["tra len men"]),
    ("sparkling water", "drink", ["nuoc co gas", "nuoc khoang co gas"])
]

# Thêm GLOBAL_POPULAR_FOODS vào database
for name, category, aliases in GLOBAL_POPULAR_FOODS:
    if category == "drink":
        cal, carbs, sugar, protein, fat, fiber = GLOBAL_DEFAULT_MACROS["drink"]
        VIETNAMESE_FOODS_NUTRITION[name] = {
            "calories_per_100ml": cal,
            "carbs_per_100ml": carbs,
            "sugar_per_100ml": sugar,
            "protein_per_100ml": protein,
            "fat_per_100ml": fat,
            "fiber_per_100ml": fiber,
            "aliases": aliases,
            "category": "drink"
        }
    else:
        cal, carbs, sugar, protein, fat, fiber = GLOBAL_DEFAULT_MACROS.get(category, GLOBAL_DEFAULT_MACROS["combo"])
        VIETNAMESE_FOODS_NUTRITION[name] = {
            "calories_per_100g": cal,
            "carbs_per_100g": carbs,
            "sugar_per_100g": sugar,
            "protein_per_100g": protein,
            "fat_per_100g": fat,
            "fiber_per_100g": fiber,
            "aliases": aliases,
            "category": category
        }

# Đơn vị quy đổi với sai số chấp nhận được
BASE_UNIT_CONVERSION = {
    "bát": {"default": 180, "min": 150, "max": 210},
    "chén": {"default": 100, "min": 80, "max": 120},
    "đĩa": {"default": 250, "min": 200, "max": 300},
    "tô": {"default": 500, "min": 400, "max": 600},
    "ly": {"default": 250, "min": 200, "max": 300},
    "cốc": {"default": 250, "min": 200, "max": 300},
    "ổ": {"default": 120, "min": 80, "max": 150},
    "quả": {"default": 50, "min": 40, "max": 60},
    "trái": {"default": 50, "min": 40, "max": 60},
    "miếng": {"default": 100, "min": 80, "max": 120},
    "phần": {"default": 200, "min": 150, "max": 250},
    "suất": {"default": 250, "min": 200, "max": 300},
    "chai": {"default": 330, "min": 300, "max": 600},
    "lon": {"default": 330, "min": 320, "max": 350},
    "gói": {"default": 70, "min": 40, "max": 120},
    "hộp": {"default": 250, "min": 180, "max": 350},
}

# Aliases để hỗ trợ không dấu và tiếng Anh phổ biến
UNIT_ALIASES = {
    "bat": "bát",
    "chen": "chén",
    "dia": "đĩa",
    "to": "tô",
    "li": "ly",
    "glass": "ly",
    "coc": "cốc",
    "cup": "cốc",
    "tach": "cốc",
    "o": "ổ",
    "qua": "quả",
    "trai": "trái",
    "mieng": "miếng",
    "phan": "phần",
    "suat": "suất",
    "goi": "gói",
    "hop": "hộp",
    "bowl": "tô",
    "bottle": "chai",
    "can": "lon",
    "pack": "gói",
    "packet": "gói",
    "box": "hộp"
}

UNIT_CONVERSION = {**BASE_UNIT_CONVERSION}
for alias, target in UNIT_ALIASES.items():
    if target in BASE_UNIT_CONVERSION:
        UNIT_CONVERSION[alias] = BASE_UNIT_CONVERSION[target]

class FoodNameMatcher:
    """Xử lý chính tả và tìm kiếm món ăn"""
    
    def __init__(self):
        # Merge foods/aliases learned from DeepSeek (persisted in SQLite)
        # before building the search index.
        try:
            load_learned_foods()
        except Exception:
            # Defensive: learned foods are optional and should not break startup.
            pass
        self.build_index()
    
    def build_index(self):
        """Xây dựng index tìm kiếm"""
        self.food_map = {}
        self.alias_map = {}
        
        for food_name, data in VIETNAMESE_FOODS_NUTRITION.items():
            # Thêm tên chính
            normalized_name = self.normalize_text(food_name)
            self.food_map[normalized_name] = food_name
            
            # Thêm các alias
            if "aliases" in data:
                for alias in data["aliases"]:
                    normalized_alias = self.normalize_text(alias)
                    self.alias_map[normalized_alias] = food_name
    
    def normalize_text(self, text):
        """Chuẩn hóa text để tìm kiếm không dấu, lowercase"""
        if not text:
            return ""
        
        # Chuyển về lowercase
        text = text.lower()
        
        # Loại bỏ dấu tiếng Việt
        text = re.sub(r'[àáảãạăắằẳẵặâấầẩẫậ]', 'a', text)
        text = re.sub(r'[đ]', 'd', text)
        text = re.sub(r'[èéẻẽẹêếềểễệ]', 'e', text)
        text = re.sub(r'[ìíỉĩị]', 'i', text)
        text = re.sub(r'[òóỏõọôốồổỗộơớờởỡợ]', 'o', text)
        text = re.sub(r'[ùúủũụưứừửữự]', 'u', text)
        text = re.sub(r'[ỳýỷỹỵ]', 'y', text)
        
        # Loại bỏ khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def find_food(self, user_input):
        """Tìm món ăn phù hợp nhất với input của người dùng, trả về (food_name, confidence)"""
        normalized_input = self.normalize_text(user_input)
        if not normalized_input:
            return None, 0.0

        input_tokens = normalized_input.split()
        
        # Tìm exact match trong alias map
        if normalized_input in self.alias_map:
            return self.alias_map[normalized_input], 0.95
        
        # Tìm trong food map
        if normalized_input in self.food_map:
            return self.food_map[normalized_input], 0.95
        
        # Tìm kiếm fuzzy
        best_match = (None, 0.0)

        def compute_confidence(token_count: int) -> float:
            if not input_tokens or token_count == 0:
                return 0.0
            coverage = token_count / max(len(input_tokens), token_count, 1)
            length_bonus = 0.05 * min(token_count, 3)  # thưởng nhẹ cho cụm dài hơn 1 từ
            # Giới hạn để fuzzy match không quá tự tin
            return min(0.9, round(0.35 + 0.5 * coverage + length_bonus, 2))
        
        # Tìm trong alias map
        for alias, food_name in self.alias_map.items():
            alias_tokens = alias.split()
            if all(tok in input_tokens for tok in alias_tokens):
                confidence = compute_confidence(len(alias_tokens))
                if confidence > best_match[1]:
                    best_match = (food_name, confidence)
        
        # Tìm trong food names
        if not best_match[0]:
            for food_norm, food_name in self.food_map.items():
                food_tokens = food_norm.split()
                if all(tok in input_tokens for tok in food_tokens):
                    confidence = compute_confidence(len(food_tokens))
                    if confidence > best_match[1]:
                        best_match = (food_name, confidence)
        
        # Nếu vẫn chưa tìm thấy, thử tìm từ khóa
        if not best_match[0]:
            keywords = {
                "cơm": "cơm trắng",
                "com": "cơm trắng",
                "phở": "phở bò",
                "pho": "phở bò",
                "bún": "bún chả",
                "bun": "bún chả",
                "trứng": "trứng chiên",
                "trung": "trứng chiên",
                "sườn": "sườn nướng",
                "suon": "sườn nướng",
                "bánh mì": "bánh mì",
                "banh mi": "bánh mì",
                "cà phê": "cà phê sữa",
                "ca phe": "cà phê sữa",
                "nước cam": "nước cam",
                "nuoc cam": "nước cam",
                "thịt": "thịt bò",
                "thit": "thịt bò",
                "cá": "cá chiên",
                "ca": "cá chiên"
            }
            
            for keyword, food_name in keywords.items():
                if " " in keyword:
                    if keyword in normalized_input:
                        return food_name, 0.35
                else:
                    if keyword in input_tokens:
                        return food_name, 0.35
        
        return best_match

    def add_alias(self, alias: str, food_name: str) -> None:
        """Add an alias -> canonical mapping to the in-memory matcher."""
        alias = (alias or "").strip()
        food_name = (food_name or "").strip()
        if not alias or not food_name:
            return
        normalized_alias = self.normalize_text(alias)
        if not normalized_alias:
            return
        self.alias_map[normalized_alias] = food_name

    def add_food(self, food_name: str, food_data: dict) -> None:
        """
        Add/update a food in the global dataset and update this matcher's index.
        `food_data` should follow the same structure as `VIETNAMESE_FOODS_NUTRITION` values.
        """
        food_name = (food_name or "").strip()
        if not food_name:
            return

        if not isinstance(food_data, dict):
            food_data = {}

        # Ensure the food exists in the shared dataset.
        existing = VIETNAMESE_FOODS_NUTRITION.get(food_name)
        if existing and isinstance(existing, dict):
            for k, v in food_data.items():
                if k == "aliases":
                    continue
                if v is not None:
                    existing[k] = v
            aliases = existing.get("aliases")
            if not isinstance(aliases, list):
                aliases = []
            new_aliases = food_data.get("aliases", [])
            if isinstance(new_aliases, list):
                for alias in new_aliases:
                    if alias and alias not in aliases:
                        aliases.append(alias)
            if food_name not in aliases:
                aliases.append(food_name)
            existing["aliases"] = aliases
            VIETNAMESE_FOODS_NUTRITION[food_name] = existing
        else:
            data = dict(food_data)
            aliases = data.get("aliases")
            if not isinstance(aliases, list):
                aliases = []
            if food_name not in aliases:
                aliases.append(food_name)
            data["aliases"] = aliases
            data.setdefault("category", "custom")
            VIETNAMESE_FOODS_NUTRITION[food_name] = data

        # Update this matcher's searchable maps.
        normalized_name = self.normalize_text(food_name)
        if normalized_name:
            self.food_map[normalized_name] = food_name
        for alias in VIETNAMESE_FOODS_NUTRITION.get(food_name, {}).get("aliases", []) or []:
            normalized_alias = self.normalize_text(alias)
            if normalized_alias:
                self.alias_map[normalized_alias] = food_name

class QuantityParser:
    """Phân tích định lượng với sai số"""
    
    def __init__(self):
        self.number_words = {
            'một': 1, 'môt': 1, 'mot': 1, '1': 1,
            'hai': 2, '2': 2,
            'ba': 3, '3': 3,
            'bốn': 4, 'bôn': 4, 'bon': 4, '4': 4,
            'năm': 5, 'nam': 5, '5': 5,
            'sáu': 6, 'sau': 6, '6': 6,
            'bảy': 7, 'bây': 7, 'bay': 7, '7': 7,
            'tám': 8, 'tam': 8, '8': 8,
            'chín': 9, 'chin': 9, '9': 9,
            'mười': 10, 'muoi': 10, '10': 10,
            'mấy': 3,  # ước lượng
            'vài': 2,  # ước lượng
            'dăm': 5,  # ước lượng
            'chục': 10
        }
        unit_keys = sorted(UNIT_CONVERSION.keys(), key=len, reverse=True)
        self.unit_pattern = r'(' + '|'.join(map(re.escape, unit_keys)) + r')'
        
    def parse(self, text):
        """Phân tích định lượng từ text"""
        text = text.lower().strip()
        
        # Mẫu 1: Số chính xác với đơn vị (100g, 500ml)
        exact_match = re.search(
            r'(\d+(?:\.\d+)?)\s*(g|gr|gram|ml|lít|l|kg|kilogram)(?![a-zA-Z])',
            text
        )
        if exact_match:
            amount = float(exact_match.group(1))
            unit = exact_match.group(2)
            
            # Chuyển đổi về gram/ml
            if unit in ['kg', 'kilogram']:
                amount *= 1000
                unit = 'g'
            elif unit == 'lít' or unit == 'l':
                amount *= 1000
                unit = 'ml'
            
            return {
                'amount': amount,
                'unit': unit,
                'type': 'exact',
                'confidence': 1.0
            }
        
        # Mẫu 2: Số + đơn vị tương đối (2 bát, 3 ly)
        unit_match = re.search(rf'(\d+)\s*{self.unit_pattern}', text)
        if unit_match:
            amount = int(unit_match.group(1))
            unit = unit_match.group(2)
            
            return {
                'amount': amount,
                'unit': unit,
                'type': 'relative',
                'confidence': 0.9
            }
        
        # Mẫu 3: Số bằng chữ + đơn vị
        word_match = re.search(
            rf'(một|môt|mot|hai|ba|bốn|bôn|bon|năm|nam|sáu|sau|bảy|bây|bay|tám|tam|chín|chin|mười|muoi|mấy|vài|dăm)\s+{self.unit_pattern}',
            text
        )
        if word_match:
            word = word_match.group(1)
            unit = word_match.group(2)
            amount = self.number_words.get(word, 1)
            
            return {
                'amount': amount,
                'unit': unit,
                'type': 'relative',
                'confidence': 0.8
            }
        
        # Mẫu 4: Chỉ có số (mặc định là "phần")
        number_match = re.search(r'(\d+)', text)
        if number_match:
            amount = int(number_match.group(1))
            return {
                'amount': amount,
                'unit': 'phần',
                'type': 'relative',
                'confidence': 0.7
            }
        
        # Mẫu 5: Không có số, mặc định 1 phần
        return {
            'amount': 1,
            'unit': 'phần',
            'type': 'relative',
            'confidence': 0.5
        }

class FoodExtractor:
    """Trích xuất món ăn từ câu"""
    
    def __init__(self):
        self.matcher = FoodNameMatcher()
        self.parser = QuantityParser()

    def _has_no_sugar(self, text: str) -> bool:
        """Detect 'không đường' / 'no sugar' markers in the same food segment."""
        normalized = self.matcher.normalize_text(text)
        if not normalized:
            return False

        if re.search(r"\b(khong|ko|k0)\s*(co\s*)?duong\b", normalized):
            return True
        if "no sugar" in normalized or "sugar free" in normalized or "unsweetened" in normalized:
            return True
        return False

    def _remove_no_sugar_from_text(self, text: str) -> str:
        """Remove 'không đường' markers to avoid hurting food name matching."""
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
        
    def extract(self, text):
        """Trích xuất các món ăn từ text"""
        # Loại bỏ từ không cần thiết (chỉ tập trung vào món ăn)
        stop_words = [
            'tôi', 'mình', 'em', 'anh', 'chị', 'bạn', 'hôm nay',
            'sáng', 'trưa', 'tối', 'đã', 'ăn', 'uống', 'dùng', 'thì',
            'có', 'bữa', 'bữa ăn', 'hôm qua', 'ngày mai'
        ]
        # Các từ nối dùng để tách nhiều món trong cùng câu
        separators = r'[,\.;]|\+|\bvà\b|\brồi\b|\bsau đó\b|\btiếp theo\b|\bcùng\b|\bvới\b'
        
        # Tách câu trước rồi mới loại bỏ stop words để tránh dính các món lại với nhau
        parts = re.split(separators, text.lower())
        
        foods = []
        for part in parts:
            part = part.strip()
            if not part or len(part) < 2:
                continue
            
            # Loại bỏ stop words trong từng phần
            clean_part = part
            for word in stop_words:
                clean_part = re.sub(rf'\b{re.escape(word)}\b', ' ', clean_part)
            clean_part = re.sub(r'\s+', ' ', clean_part).strip()
            if not clean_part:
                continue

            no_sugar = self._has_no_sugar(clean_part)
            if no_sugar:
                clean_part = self._remove_no_sugar_from_text(clean_part)
            
            # Tìm định lượng
            quantity_info = self.parser.parse(clean_part)
            
            # Tìm tên món ăn (loại bỏ số và đơn vị đã tìm thấy)
            food_text = self._remove_quantity_from_text(clean_part, quantity_info)
            
            # Tìm món ăn phù hợp
            food_name, match_confidence = self.matcher.find_food(food_text)
            
            if food_name:
                foods.append({
                    'original_text': part.strip(),
                    'food_name': food_name,
                    'match_confidence': match_confidence,
                    'quantity_info': quantity_info,
                    'extracted_food_text': food_text,
                    'no_sugar': no_sugar
                })
        
        return foods
    
    def _remove_quantity_from_text(self, text, quantity_info):
        """Loại bỏ phần định lượng đã trích xuất khỏi text"""
        result = text.lower()
        
        # Loại bỏ số và đơn vị
        if quantity_info['type'] == 'exact':
            pattern = r'\d+(?:\.\d+)?\s*(?:g|gr|gram|ml|lít|l|kg|kilogram)'
            result = re.sub(pattern, '', result)
        else:
            unit_pattern = re.escape(quantity_info['unit'])
            # Loại bỏ số và đơn vị
            if quantity_info['amount'] > 1:
                pattern = f"{quantity_info['amount']}\\s*{unit_pattern}"
                result = re.sub(pattern, '', result)
            else:
                # Nếu amount = 1, có thể là "một" hoặc "1"
                pattern = f"(?:một|môt|mot|1)\\s*{unit_pattern}"
                result = re.sub(pattern, '', result)
        
        # Loại bỏ khoảng trắng thừa và từ thừa
        result = re.sub(r'\s+', ' ', result).strip()
        
        # Loại bỏ từ thừa
        unnecessary = ['cái', 'cục', 'miếng', 'phần', 'suất', 'của']
        for word in unnecessary:
            result = re.sub(f'\\b{word}\\b', '', result)
        
        return re.sub(r'\s+', ' ', result).strip()

def estimate_weight(quantity_info, food_category=None):
    """Ước lượng trọng lượng với sai số"""
    if quantity_info['type'] == 'exact':
        return quantity_info['amount']
    
    unit = quantity_info['unit']
    amount = quantity_info['amount']
    
    if unit in UNIT_CONVERSION:
        unit_info = UNIT_CONVERSION[unit]
        
        # Điều chỉnh theo loại thức ăn
        multiplier = 1.0
        if food_category == 'drink':
            multiplier = 1.0  # ml
        elif food_category == 'rice':
            multiplier = 0.9  # cơm đặc
        elif food_category == 'noodle':
            multiplier = 0.8  # có nước
        elif food_category == 'bread':
            multiplier = 1.2  # bánh mì nhẹ hơn
        
        base_weight = unit_info['default'] * multiplier
        
        # Thêm sai số ngẫu nhiên nhỏ (±10%)
        error_range = 0.1  # 10%
        weight = base_weight * (1 + random.uniform(-error_range, error_range))
        
        return weight * amount
    
    return 200 * amount  # Mặc định 200g/portion

def calculate_nutrition(food_name, weight):
    """Tính dinh dưỡng cho món ăn"""
    if food_name not in VIETNAMESE_FOODS_NUTRITION:
        return None
    
    data = VIETNAMESE_FOODS_NUTRITION[food_name]
    
    # Tính theo 100g/100ml
    factor = weight / 100
    
    # Nếu là combo, tính tổng các thành phần
    if 'components' in data:
        total = {
            'calories': 0,
            'carbs': 0,
            'sugar': 0,
            'protein': 0,
            'fat': 0,
            'fiber': 0
        }
        
        for component, comp_weight in data['components'].items():
            if component in VIETNAMESE_FOODS_NUTRITION:
                comp_data = VIETNAMESE_FOODS_NUTRITION[component]
                comp_factor = comp_weight / 100
                
                total['calories'] += comp_data.get('calories_per_100g', 0) * comp_factor
                total['carbs'] += comp_data.get('carbs_per_100g', 0) * comp_factor
                total['sugar'] += comp_data.get('sugar_per_100g', 0) * comp_factor
                total['protein'] += comp_data.get('protein_per_100g', 0) * comp_factor
                total['fat'] += comp_data.get('fat_per_100g', 0) * comp_factor
                total['fiber'] += comp_data.get('fiber_per_100g', 0) * comp_factor
        
        # Adjust total based on actual weight
        actual_factor = weight / sum(data['components'].values())
        for key in total:
            total[key] *= actual_factor
        
        return total
    
    # Tính thông thường
    return {
        'calories': data.get('calories_per_100g', data.get('calories_per_100ml', 0)) * factor,
        'carbs': data.get('carbs_per_100g', data.get('carbs_per_100ml', 0)) * factor,
        'sugar': data.get('sugar_per_100g', data.get('sugar_per_100ml', 0)) * factor,
        'protein': data.get('protein_per_100g', data.get('protein_per_100ml', 0)) * factor,
        'fat': data.get('fat_per_100g', data.get('fat_per_100ml', 0)) * factor,
        'fiber': data.get('fiber_per_100g', data.get('fiber_per_100ml', 0)) * factor
    }
