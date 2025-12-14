"""
Mở rộng test cases cho Nutrition Pipeline
"""

EXTENDED_TEST_CASES = [
    # ============ CHÍNH TẢ NẶNG ============
    ("com trang", "Không dấu hoàn toàn"),
    ("pho bo", "Không dấu phổ biến"),
    ("bun cha", "Không dấu"),
    ("trung chien", "Không dấu"),
    ("suon nuong", "Không dấu"),
    ("banh mi", "Không dấu"),
    ("ca phe sua", "Không dấu"),
    ("nuoc mia", "Không dấu"),
    
    # ============ SAI CHÍNH TẢ PHỔ BIẾN ============
    ("cơm trắng", "Chính tả đúng"),
    ("cơm trang", "Thiếu dấu"),
    ("cơm trăng", "Sai dấu"),
    ("com trắng", "Nửa dấu"),
    ("cơm tran", "Thiếu chữ"),
    ("cơm trắg", "Sai chữ cuối"),
    
    ("phở bò", "Chính tả đúng"),
    ("phở bò", "Có dấu"),
    ("pho bò", "Nửa dấu"),
    ("phở bo", "Nửa dấu"),
    ("phở bó", "Sai dấu"),
    ("phở bô", "Sai dấu"),
    
    # ============ ĐỊNH LƯỢNG CHÍNH XÁC ============
    ("100g cơm", "Định lượng gram đơn giản"),
    ("150g thịt bò", "Định lượng với tên món"),
    ("500ml nước cam", "Định lượng ml"),
    ("1.5 lít nước", "Định lượng thập phân"),
    ("0.5kg thịt", "Định lượng kg"),
    ("250g cá + 200g cơm", "Nhiều định lượng"),
    
    # ============ ĐỊNH LƯỢNG TƯƠNG ĐỐI ============
    ("1 bát cơm", "Đơn vị bát"),
    ("2 chén cơm", "Đơn vị chén"),
    ("1 đĩa thịt", "Đơn vị đĩa"),
    ("3 tô phở", "Đơn vị tô"),
    ("1 ly nước", "Đơn vị ly"),
    ("2 cốc cafe", "Đơn vị cốc"),
    ("1 ổ bánh mì", "Đơn vị ổ"),
    ("3 quả trứng", "Đơn vị quả"),
    ("2 miếng thịt", "Đơn vị miếng"),
    ("1 phần cơm sườn", "Đơn vị phần"),
    ("2 suất bún chả", "Đơn vị suất"),
    
    # ============ SỐ BẰNG CHỮ VIỆT ============
    ("một bát cơm", "Số một"),
    ("hai chén canh", "Số hai"),
    ("ba tô phở", "Số ba"),
    ("bốn ly nước", "Số bốn"),
    ("năm quả trứng", "Số năm"),
    ("sáu miếng thịt", "Số sáu"),
    ("bảy ổ bánh", "Số bảy"),
    ("tám phần cơm", "Số tám"),
    ("chín suất bún", "Số chín"),
    ("mười cốc cafe", "Số mười"),
    
    # ============ SỐ BẰNG CHỮ LỖI ============
    ("môt bát cơm", "Thiếu dấu một"),
    ("bốn bát phở", "Số bốn đúng"),
    ("bốn bát phở", "Số bốn đúng"),
    ("nam quả trứng", "Sai dấu năm"),
    ("sau miếng thịt", "Thiếu dấu sáu"),
    ("tam cốc nước", "Thiếu dấu tám"),
    ("chin suất cơm", "Thiếu dấu chín"),
    ("muoi ly sinh tố", "Không dấu mười"),
    
    # ============ ĐỊNH LƯỢNG MƠ HỒ ============
    ("ít cơm", "Định lượng mơ hồ - ít"),
    ("nhiều thịt", "Định lượng mơ hồ - nhiều"),
    ("vài miếng thịt", "Định lượng mơ hồ - vài"),
    ("dăm quả trứng", "Định lượng mơ hồ - dăm"),
    ("mấy bát cơm", "Định lượng mơ hồ - mấy"),
    ("khoảng 200g cá", "Định lượng xấp xỉ"),
    ("tầm 300ml nước", "Định lượng xấp xỉ"),
    ("chừng 1 bát phở", "Định lượng xấp xỉ"),
    
    # ============ NHIỀU MÓN PHỨC TẠP ============
    ("1 tô phở và 1 ly nước cam", "Hai món đơn giản"),
    ("2 bát cơm, 1 đĩa thịt kho, canh rau", "Ba món"),
    ("sáng: 1 tô phở, trưa: 2 bát cơm với thịt, tối: bún chả", "Theo bữa"),
    ("100g thịt bò + 150g cơm + 200ml nước cam", "Định lượng chính xác nhiều món"),
    ("cơm sườn 1 phần, trứng chiên 2 quả, canh rau", "Mix định lượng"),
    ("ăn sáng 2 quả trứng ốp la, 1 ổ bánh mì, 1 ly cafe sữa", "Bữa sáng đầy đủ"),
    ("trưa nay ăn 1 suất cơm tấm sườn bì chả với trứng", "Combo phức tạp"),
    
    # ============ TỪ THỪA VÀ CẤU TRÚC PHỨC TẠP ============
    ("hôm nay tôi đã ăn một tô phở bò rất ngon", "Nhiều từ thừa"),
    ("sáng nay em dùng 2 quả trứng chiên với 1 ly sữa", "Đại từ + từ thừa"),
    ("bữa trưa có cơm, thịt kho, canh rau và tráng miệng hoa quả", "Liệt kê không số"),
    ("tối qua ăn nhẹ 1 ổ bánh mì pate và 1 chai nước suối", "Món phụ"),
    ("đói quá nên ăn vội 3 cái bánh bao và uống nước", "Tình huống + món"),
    ("ăn vặt: 1 gói bim bim, 1 chai coca, 2 cái kẹo", "Đồ ăn vặt"),
    
    # ============ MÓN ĂN ĐẶC BIỆT ============
    ("bún bò huế", "Món đặc sản"),
    ("cơm tấm sườn", "Món miền Nam"),
    ("bánh xèo", "Món bánh"),
    ("gỏi cuốn", "Món cuốn"),
    ("chả giò", "Món chiên"),
    ("bò lúc lắc", "Món thịt bò"),
    ("cá kho tộ", "Món cá"),
    ("canh chua cá lóc", "Món canh"),
    
    # ============ ĐỒ UỐNG ĐA DẠNG ============
    ("trà đá", "Đồ uống đơn giản"),
    ("nước chanh", "Đồ uống"),
    ("sinh tố xoài", "Sinh tố"),
    ("nước ép cà rốt", "Nước ép"),
    ("sữa đậu nành", "Đồ uống từ đậu"),
    ("nước dừa", "Đồ uống tự nhiên"),
    ("bia", "Đồ uống có cồn"),
    ("rượu vang", "Đồ uống có cồn cao cấp"),
    ("nước lọc", "Nước lọc"),
    ("nước", "Từ khóa nước chung"),
    ("2 lít nước", "Nước nhiều"),
    ("1 lít nước lọc và 1 ly nước cam", "Hai loại nước"),
    ("orange juice and water", "Hai đồ uống Anh-Việt"),
    ("matcha latte", "Matcha latte"),
    ("latte", "Cà phê latte"),
    ("trà sữa trân châu", "Trà sữa trân châu"),
    ("rượu soju", "Rượu"),
    ("rượu sake", "Rượu"),
    ("rượu vodka", "Rượu mạnh"),
    ("rượu whiskey", "Rượu mạnh"),
    ("rượu gin", "Rượu mạnh"),
    ("rượu rum", "Rượu mạnh"),
    
    # ============ CẬP NHẬT SỐ LƯỢNG ============
    ("ăn 2 quả trứng", "Lần 1 - 2 trứng"),
    ("không, 3 quả trứng", "Lần 2 - sửa thành 3"),
    ("thêm 1 bát cơm nữa", "Thêm vào"),
    ("chỉ 1 ly nước thôi", "Giảm số lượng"),
    ("đổi thành 200g thịt", "Đổi định lượng"),
    
    # ============ TÌNH HUỐNG THỰC TẾ ============
    ("đi nhậu: 3 lon bia, lẩu, gà nướng", "Đi nhậu"),
    ("tiệc sinh nhật: bánh kem, nước ngọt, snack", "Tiệc"),
    ("ăn kiêng: ức gà 150g, rau luộc, khoai lang", "Ăn kiêng"),
    ("tập gym: 5 quả trứng, 200g ức gà, chuối", "Dinh dưỡng thể hình"),
    ("bệnh nhân tiểu đường: cơm gạo lứt, rau xanh", "Bệnh lý"),
    ("trẻ em: sữa, cháo, trái cây nghiền", "Trẻ em"),
    
    # ============ KẾT HỢP TIẾNG ANH ============
    ("1 bowl of rice", "Tiếng Anh"),
    ("2 eggs and coffee", "Mix Việt-Anh"),
    ("chicken phở", "Tiếng Anh + Việt"),
    ("bánh mì sandwich", "Việt-Anh"),
    ("trà sữa trân châu", "Món hiện đại"),
    
    # ============ BIÊN GIỚI VÀ LỖI ============
    ("", "Chuỗi rỗng"),
    ("ăn uống", "Quá chung chung"),
    ("đồ ăn", "Không cụ thể"),
    ("123456", "Chỉ số"),
    ("@@@###", "Ký tự đặc biệt"),
    ("cơm cơm cơm", "Lặp từ"),
    ("1 1 1 bát cơm", "Số lặp"),
    
    # ============ VĂN NÓI THỰC TẾ ============
    ("ăn sáng tầm 2 ổ bánh mì thịt", "Văn nói - tầm"),
    ("trưa làm cái cơm hộp với 1 hộp sữa", "Văn nói - cái"),
    ("tối về nấu nồi canh với làm đĩa thịt", "Văn nói - nồi, đĩa"),
    ("lỡ tay ăn hết 3 gói mì tôm", "Văn nói - lỡ tay"),
    ("đói bụng quá mua đại 1 suất cơm", "Văn nói - đại"),
    
    # ============ NHIỀU ĐỊNH LƯỢNG TRONG 1 MÓN ============
    ("1 bát cơm trắng 150g", "Vừa đơn vị vừa gram"),
    ("2 ly nước cam 500ml", "Đơn vị và ml"),
    ("1 phần cơm sườn khoảng 300g", "Đơn vị và ước lượng"),
    ("3 quả trứng gà ta", "Chi tiết loại"),
    ("1 tô phở bò tái chín", "Chi tiết thành phần"),
    
    # ============ MÓN KẾT HỢP ============
    ("cơm thịt kho trứng", "Món kết hợp"),
    ("bún thịt nướng chả giò", "Combo bún"),
    ("phở bò viên tái nạm", "Phở đầy đủ"),
    ("bánh mì thịt chả pate", "Bánh mì đầy đủ"),
    ("xôi gà đậu xanh", "Xôi kết hợp"),
    ("mì cay hàn quốc", "Mì cay"),
    ("cơm xèo", "Cơm xèo"),
    ("thịt giả cầy", "Thịt giả cầy"),
    ("thịt chó", "Thịt chó"),
    ("lẩu cá cải chua", "Lẩu cá cải chua"),
    ("thịt cầy", "Thịt cầy"),
    ("thịt mèo", "Thịt mèo"),
    ("thịt dê", "Thịt dê"),
    ("thịt cừu", "Thịt cừu"),
    ("thịt nhím", "Thịt nhím"),
    ("mì ý", "Mì Ý"),
    ("lạp xưởng nướng đá", "Lạp xưởng nướng đá"),
    ("bánh đồng xu", "Bánh đồng xu"),
    ("lẩu chay", "Lẩu chay"),
    ("cơm chay", "Cơm chay"),
    ("gà rán", "Gà rán"),
    ("cơm cháy tỏi", "Cơm cháy tỏi"),
    ("kho quẹt", "Kho quẹt"),
    ("cơm xá xíu", "Cơm xá xíu"),
    ("bánh canh", "Bánh canh"),
    ("bún riêu", "Bún riêu"),
    ("bún đỏ", "Bún đỏ"),
    ("bún cua", "Bún cua"),
    ("cua rang me", "Cua rang me"),
    
    # ============ ĐỊNH LƯỢNG LỚN ============
    ("10 quả trứng", "Số lượng lớn"),
    ("5 bát cơm", "Nhiều"),
    ("20 miếng thịt", "Rất nhiều"),
    ("1000ml nước", "Lượng lớn"),
    ("2kg thịt bò", "Khối lượng lớn"),

    # ============ MÓN MIỀN TÂY MỞ RỘNG ============
    ("hủ tiếu mỹ tho", "Đặc sản Mỹ Tho"),
    ("bún mắm sóc trăng", "Đặc sản Sóc Trăng"),
    ("lẩu mắm", "Đặc sản miền Tây"),
    ("cá lóc nướng trui", "Đặc sản đồng quê"),
    ("bánh pía", "Đặc sản Sóc Trăng"),
    ("chè ba màu", "Chè miền Nam"),
    ("gỏi cá trích phú quốc", "Đặc sản Phú Quốc"),
    ("bánh tráng trộn tây ninh", "Ăn vặt miền Nam"),
    ("bánh tằm bì nước cốt dừa", "Món nước miền Tây"),
    ("bánh phồng tôm sa giang", "Đặc sản Sa Giang"),
]

# Bổ sung thêm ~100 test cases đa dạng
ADDITIONAL_TEST_CASES = [
    ("phở gà xé", "Phở gà"),
    ("phở tái gầu gân", "Phở bò đầy đủ"),
    ("mì quảng gà", "Mì quảng"),
    ("mì quảng tôm thịt", "Mì quảng"),
    ("bánh cuốn nhân thịt", "Bánh cuốn"),
    ("bánh cuốn chả", "Bánh cuốn + chả"),
    ("bánh ướt chả lụa", "Bánh ướt"),
    ("bánh bèo chén", "Ăn vặt Huế"),
    ("bánh ít trần", "Ăn vặt Huế"),
    ("bánh bột lọc", "Ăn vặt Huế"),
    ("bún mọc", "Bún nước"),
    ("bún thang", "Bún Hà Nội"),
    ("bún ngan măng", "Bún ngan"),
    ("bún đậu mắm tôm", "Bún đậu"),
    ("bún cá rô đồng", "Bún cá"),
    ("bún chả cá", "Bún cá"),
    ("bún riêu cua", "Bún riêu"),
    ("bún riêu ốc", "Bún riêu ốc"),
    ("bún ốc nguội", "Bún ốc"),
    ("bún hải sản", "Bún hải sản"),
    ("mì vằn thắn", "Mì nước"),
    ("mì hoành thánh", "Hoành thánh"),
    ("hủ tiếu khô trộn", "Hủ tiếu trộn"),
    ("hủ tiếu satế", "Hủ tiếu sate"),
    ("cơm rang dưa bò", "Cơm rang"),
    ("cơm rang gà xé", "Cơm rang"),
    ("cơm rang hải sản", "Cơm rang"),
    ("cơm chiên trứng", "Cơm chiên"),
    ("cơm chiên hải sản", "Cơm chiên"),
    ("cơm chiên dương châu", "Cơm chiên"),
    ("cơm gà Hội An", "Cơm gà"),
    ("cơm gà Hải Nam", "Cơm gà"),
    ("xôi xéo", "Xôi"),
    ("xôi gà", "Xôi gà"),
    ("xôi chim", "Xôi chim"),
    ("xôi lạc", "Xôi lạc"),
    ("xôi đậu xanh", "Xôi đậu"),
    ("cháo gà", "Cháo gà"),
    ("cháo vịt", "Cháo vịt"),
    ("cháo trai", "Cháo trai"),
    ("cháo ếch", "Cháo ếch"),
    ("cháo sườn", "Cháo sườn"),
    ("cháo hải sản", "Cháo hải sản"),
    ("lẩu thái", "Lẩu chua cay"),
    ("lẩu bò", "Lẩu bò"),
    ("lẩu gà ớt hiểm", "Lẩu gà"),
    ("lẩu gà lá giang", "Lẩu gà"),
    ("lẩu dê", "Lẩu dê"),
    ("lẩu ếch", "Lẩu ếch"),
    ("lẩu riêu cua bắp bò", "Lẩu riêu cua"),
    ("bánh mì que", "Bánh mì"),
    ("bánh mì chả lụa", "Bánh mì"),
    ("bánh mì gà xé", "Bánh mì"),
    ("bánh mì ốp la", "Bánh mì trứng"),
    ("bánh mì bì", "Bánh mì bì"),
    ("bánh mì xíu mại", "Bánh mì"),
    ("bánh mì bơ đường", "Bánh mì ngọt"),
    ("bánh mì bơ tỏi", "Bánh mì ngọt"),
    ("pizza hải sản", "Pizza"),
    ("pizza xúc xích", "Pizza"),
    ("pizza phô mai", "Pizza"),
    ("pizza bò bằm", "Pizza"),
    ("hamburger bò", "Burger"),
    ("hamburger gà", "Burger"),
    ("hotdog", "Đồ nhanh"),
    ("mì tôm trứng", "Mì tôm"),
    ("mì tôm xúc xích", "Mì tôm"),
    ("mì tôm rau", "Mì tôm"),
    ("mì trộn sa tế", "Mì trộn"),
    ("salad rau củ", "Salad"),
    ("salad gà xé", "Salad"),
    ("salad bò", "Salad"),
    ("salad cá ngừ", "Salad"),
    ("salad trái cây", "Salad"),
    ("salad ức gà", "Salad"),
    ("sữa chua", "Tráng miệng"),
    ("sữa chua nếp cẩm", "Tráng miệng"),
    ("kem dừa", "Kem"),
    ("kem socola", "Kem"),
    ("kem vani", "Kem"),
    ("chè thập cẩm", "Chè"),
    ("chè bưởi", "Chè"),
    ("chè trôi nước", "Chè"),
    ("chè đậu đen", "Chè"),
    ("chè đậu đỏ", "Chè"),
    ("chè khúc bạch", "Chè"),
    ("trà sữa", "Đồ uống"),
    ("trà sữa matcha", "Đồ uống"),
    ("trà đào cam sả", "Đồ uống"),
    ("trà tắc", "Đồ uống"),
    ("trà chanh", "Đồ uống"),
    ("cafe đen", "Cafe"),
    ("cafe sữa đá", "Cafe"),
    ("cafe latte", "Cafe"),
    ("cafe cappuccino", "Cafe"),
    ("cafe mocha", "Cafe"),
    ("nước ép táo", "Nước ép"),
    ("nước ép dứa", "Nước ép"),
    ("nước ép ổi", "Nước ép"),
    ("nước ép cà chua", "Nước ép"),
    ("nước ép dưa hấu", "Nước ép"),
    ("sinh tố bơ", "Sinh tố"),
    ("sinh tố dâu", "Sinh tố"),
    ("sinh tố chuối", "Sinh tố"),
    ("sinh tố dưa hấu", "Sinh tố"),
    ("sinh tố mãng cầu", "Sinh tố"),
    ("bia tiger", "Bia"),
    ("bia 333", "Bia"),
    ("bia heineken", "Bia"),
    ("rượu soju", "Rượu"),
    ("rượu sake", "Rượu"),
    ("rượu vodka", "Rượu"),
    ("rượu whiskey", "Rượu"),
    ("cocktail mojito", "Cocktail"),
    ("cocktail margarita", "Cocktail"),
    ("cocktail martini", "Cocktail"),
    ("cocktail pina colada", "Cocktail"),
]

EXTENDED_TEST_CASES.extend(ADDITIONAL_TEST_CASES)

# Test cases theo nhóm để dễ quản lý
TEST_CASE_GROUPS = {
    "chinh_ta": [
        ("com trang", "Không dấu"),
        ("pho bo", "Không dấu"),
        ("cơm trang", "Thiếu dấu"),
        ("phở bo", "Nửa dấu"),
    ],
    
    "dinh_luong_chinh_xac": [
        ("100g cơm", "Gram đơn giản"),
        ("150g thịt bò", "Gram với món"),
        ("500ml nước", "Mililit"),
        ("1.5 lít nước", "Thập phân"),
    ],
    
    "dinh_luong_tuong_doi": [
        ("1 bát cơm", "Bát"),
        ("2 chén canh", "Chén"),
        ("1 đĩa thịt", "Đĩa"),
        ("3 tô phở", "Tô"),
        ("1 ly nước", "Ly"),
    ],
    
    "so_bang_chu": [
        ("một bát cơm", "Một"),
        ("hai tô phở", "Hai"),
        ("ba quả trứng", "Ba"),
        ("bốn ly nước", "Bốn"),
        ("năm miếng thịt", "Năm"),
    ],
    
    "nhieu_mon": [
        ("1 tô phở và 1 ly nước cam", "Hai món"),
        ("2 bát cơm, 1 đĩa thịt, canh rau", "Ba món"),
        ("sáng: phở, trưa: cơm, tối: bún", "Theo bữa"),
        ("1 lít nước lọc và 1 ly nước cam", "Hai đồ uống"),
        ("thịt giả cầy và bia", "Món + đồ uống"),
        ("mì cay hàn quốc và trà sữa trân châu", "Món cay + trà sữa"),
    ],
    
    "mon_dac_biet": [
        ("bún bò huế", "Đặc sản Huế"),
        ("cơm tấm sườn", "Miền Nam"),
        ("bánh xèo", "Bánh"),
        ("gỏi cuốn", "Cuốn"),
    ],
    
    "mien_tay": [
        ("hủ tiếu mỹ tho", "Đặc sản Mỹ Tho"),
        ("bún mắm sóc trăng", "Sóc Trăng"),
        ("lẩu mắm", "Lẩu miền Tây"),
        ("cá lóc nướng trui", "Nướng trui"),
        ("bánh pía", "Sóc Trăng"),
    ],
    
    "do_uong": [
        ("nước lọc", "Nước lọc"),
        ("nước", "Từ khóa chung"),
        ("2 lít nước", "Nhiều nước"),
        ("orange juice and water", "Nước cam và nước"),
        ("matcha latte", "Matcha latte"),
        ("latte", "Cà phê latte"),
        ("trà sữa trân châu", "Trà sữa trân châu"),
    ],
    
    "tinh_huong_thuc_te": [
        ("đi nhậu: bia, lẩu", "Nhậu"),
        ("tiệc: bánh kem, nước", "Tiệc"),
        ("ăn kiêng: ức gà, rau", "Ăn kiêng"),
        ("tập gym: trứng, ức gà", "Thể hình"),
    ],
    
    "cap_nhat_so_luong": [
        ("ăn 2 trứng", "Ban đầu"),
        ("3 trứng", "Cập nhật"),
        ("thêm 1 cơm", "Thêm"),
        ("chỉ 1 nước", "Giảm"),
    ],
}

EXPECTED_FOOD_COUNTS = {
    "1 tô phở và 1 ly nước cam": 2,
    "2 bát cơm, 1 đĩa thịt kho, canh rau": 3,
    "100g thịt bò + 150g cơm + 200ml nước cam": 3,
    "cơm sườn 1 phần, trứng chiên 2 quả, canh rau": 3,
    "ăn sáng 2 quả trứng ốp la, 1 ổ bánh mì, 1 ly cafe sữa": 3,
    "trưa nay ăn 1 suất cơm tấm sườn bì chả với trứng": 1,  # xem như combo
    "1 lít nước lọc và 1 ly nước cam": 2,
    "nước": 1,
    "nước lọc": 1,
    "2 lít nước": 1,
    "orange juice and water": 2,
    "hủ tiếu mỹ tho": 1,
    "bún mắm sóc trăng": 1,
    "bánh pía": 1,
    "lẩu mắm": 1,
    "cá lóc nướng trui": 1,
    "thịt giả cầy": 1,
    "thịt chó": 1,
    "mì cay hàn quốc": 1,
    "cơm xèo": 1,
    "lẩu cá cải chua": 1,
    "matcha latte": 1,
    "latte": 1,
    "trà sữa trân châu": 1,
    "thịt giả cầy và bia": 2,
    "mì cay hàn quốc và trà sữa trân châu": 2,
    "thịt cầy": 1,
    "thịt mèo": 1,
    "thịt dê": 1,
    "thịt cừu": 1,
    "thịt nhím": 1,
    "mì ý": 1,
    "lạp xưởng nướng đá": 1,
    "bánh đồng xu": 1,
    "lẩu chay": 1,
    "cơm chay": 1,
    "gà rán": 1,
    "cơm cháy tỏi": 1,
    "kho quẹt": 1,
    "cơm xá xíu": 1,
    "bánh canh": 1,
    "bún riêu": 1,
    "bún đỏ": 1,
    "bún cua": 1,
    "cua rang me": 1,
    "rượu soju": 1,
    "rượu sake": 1,
    "rượu vodka": 1,
    "rượu whiskey": 1,
    "rượu gin": 1,
    "rượu rum": 1,
}

def get_all_test_cases():
    """Trả về tất cả test cases"""
    return EXTENDED_TEST_CASES

def get_test_cases_by_group(group_name):
    """Trả về test cases theo nhóm"""
    return TEST_CASE_GROUPS.get(group_name, [])

def get_expected_count(test_input):
    """Trả về số món kỳ vọng (nếu có)"""
    return EXPECTED_FOOD_COUNTS.get(test_input)

def get_statistics():
    """Thống kê test cases"""
    total = len(EXTENDED_TEST_CASES)
    
    # Đếm theo loại
    categories = {
        "chinh_ta": 0,
        "dinh_luong_chinh_xac": 0,
        "dinh_luong_tuong_doi": 0,
        "nhieu_mon": 0,
        "tinh_huong_thuc_te": 0
    }
    
    # Phân loại đơn giản (có thể cải thiện)
    for test, desc in EXTENDED_TEST_CASES:
        if "com" in test or "pho" in test or "bun" in test:
            categories["chinh_ta"] += 1
        elif "g" in test or "ml" in test or "lít" in test:
            categories["dinh_luong_chinh_xac"] += 1
        elif "bát" in test or "chén" in test or "đĩa" in test:
            categories["dinh_luong_tuong_doi"] += 1
        elif "và" in test or "," in test or ":" in test:
            categories["nhieu_mon"] += 1
        elif "nhậu" in test or "tiệc" in test or "kiêng" in test:
            categories["tinh_huong_thuc_te"] += 1
    
    return {
        "total_test_cases": total,
        "categories": categories,
        "groups": len(TEST_CASE_GROUPS)
    }

if __name__ == "__main__":
    stats = get_statistics()
    print("📊 THỐNG KÊ TEST CASES")
    print("=" * 50)
    print(f"Tổng số test cases: {stats['total_test_cases']}")
    print(f"Số nhóm test: {stats['groups']}")
    print("\nPhân bổ theo loại (ước tính):")
    for cat, count in stats['categories'].items():
        print(f"  - {cat}: {count}")
    
    # Hiển thị một số ví dụ
    print("\n🎯 Một số test cases tiêu biểu:")
    for i, (test, desc) in enumerate(EXTENDED_TEST_CASES[:10]):
        print(f"{i+1:2d}. '{test}' - {desc}")
