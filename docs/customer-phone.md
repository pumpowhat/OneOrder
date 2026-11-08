# Số điện thoại khách hàng

Mỗi đơn có thêm một trường `customer_phone`. Không thêm người liên hệ hoặc bảng khách hàng.

## Luồng sử dụng

1. Ảnh/email/Excel có số liên hệ thì hệ thống đọc và điền vào đơn nháp.
2. Không có số hoặc số đọc không rõ: giữ trống/giữ kết quả đọc để nhân viên sửa. Không tự tạo số.
3. Màn hình Review luôn hiển thị ô số điện thoại, kể cả khi AI đã điền.
4. Duyệt đơn chỉ thành công khi tên khách hàng, số điện thoại và các dòng vật liệu đều đạt yêu cầu.
5. Số điện thoại được lưu cùng đơn, hiển thị ở chi tiết đơn. Sửa số khi duyệt được ghi audit.

## Quy tắc dữ liệu

- Field API: `customer_phone: string | null` trên draft, order detail và order summary.
- `POST /api/orders/{id}/approve` nhận `customer_phone` tùy chọn trong request: bỏ field nghĩa là dùng số đã đọc; gửi null/rỗng nghĩa là không có số và bị chặn, không fallback âm thầm.
- Thiếu/sai số: trả HTTP 409, đơn vẫn draft và các sửa đổi trong request không được commit.
- Kiểm tra cú pháp: 7–15 chữ số ASCII; cho phép `+` hoặc tiền tố `00`, khoảng trắng, dấu chấm, ngoặc và gạch nối. Tiền tố `00` đổi thành `+`, bỏ dấu phân cách khi lưu số hợp lệ.
- Số trong nước vẫn giữ số 0 đầu; không suy ra mã nước từ công trường. Khuyến khích nhập kèm mã nước.
- Đây là kiểm tra định dạng, không xác thực chủ sở hữu hay số có gọi được. Không có OTP.
- Không đặt UNIQUE cho số điện thoại; nhiều đơn/khách hàng có thể dùng cùng số. Không tự gộp hồ sơ khách hàng.
- DB cho phép null để tiếp nhận draft thiếu số và tương thích đơn cũ. Khi khởi động, migration thêm cột `orders.customer_phone`; không gán số giả cho dữ liệu cũ. Đơn đã duyệt/xác nhận trước thay đổi được giữ nguyên.

## Nhận dữ liệu

- Gemini và Claude dùng schema/prompt chung, yêu cầu trả số thực tế hoặc null và không đoán mã quốc gia.
- Demo email nhận nhãn Phone/Telephone/Tel./Telefon/Telefonnummer/Tlf/Mobil. Nhiều số khác nhau thì để trống để nhân viên chọn.
- Excel nhận cột số điện thoại; demo hỗ trợ các nhãn trên. Cột được kiểm tra trên toàn bộ dòng, không chỉ 5 dòng mẫu gửi AI. Số khác nhau hoặc cột rỗng thì để trống và cảnh báo. Lưu ô số điện thoại dưới dạng text để giữ số 0 đầu.
- Email/Excel mẫu có số hư cấu chỉ để minh họa cú pháp. Không dùng làm thông tin liên lạc thật.
- Ảnh viết tay hiện có không chứa số: fixture trả null để minh họa nhập bổ sung. Không thay ảnh hay bịa số trong fixture.

## Kiểm tra

```bash
AI_MODE=demo .venv/bin/python -m pytest -q tests/test_customer_phone.py tests/test_intake.py tests/test_claude_client.py tests/test_gemini_client.py
./run-oneorder.sh test
./run-oneorder.sh smoke
```

Bộ test `test_customer_phone.py` kiểm tra intake, dữ liệu mẫu, duyệt trên SQLite thật, rollback/audit, cho phép số trùng giữa các đơn và migration DB cũ. Các hàm nghiệp vụ được gọi trực tiếp để kiểm tra độc lập với HTTP/TestClient; các test API hiện có vẫn kiểm tra luồng qua HTTP.

## Giao diện chọn mã quốc gia

- Review hiển thị hai ô cùng hàng: mã quốc gia bên trái, phần số còn lại bên phải.
- Dropdown có cờ, tên quốc gia và mã gọi; tìm được theo tên tiếng Việt/Anh, mã ISO hoặc đầu số. DK, SE, NO và VN được ưu tiên đầu danh sách.
- Dữ liệu 245 quốc gia/vùng lãnh thổ lấy từ countryCodeToRegionCodeMap của [Google libphonenumber](https://github.com/google/libphonenumber/blob/master/javascript/i18n/phonenumbers/metadata.js), lưu local; giấy phép Apache-2.0 nằm trong `frontend/third-party/`. Không cần truy cập mạng khi dùng menu.
- Dán số bắt đầu bằng + hoặc 00 sẽ tự tách mã đã biết. Không đoán mã nước cho số nội địa; không tự xóa số 0 đầu. Khi dùng dạng quốc tế, người nhập cần kiểm tra phần số còn lại theo đúng số liên hệ.
- Mã dùng chung (ví dụ +1 hoặc +44) hiển thị biểu tượng quốc tế khi chưa chọn rõ quốc gia, tránh gán cờ sai. Chọn quốc gia không làm mất phần số đang nhập.
- Hỗ trợ phím mũi tên/Enter để chọn, Escape để đóng; trường `customer_phone` gửi backend vẫn là một chuỗi.
