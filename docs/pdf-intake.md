# Tải lên và OCR PDF

OneOrder nhận `.pdf` qua cùng `POST /api/intake` (multipart `file`) như ảnh, Excel và email.
PDF văn bản, PDF scan và tài liệu có cả hai loại trang đều được gửi nguyên tệp đến AI; không
chỉ trích lớp văn bản nên không bỏ qua trang ảnh. AI đọc các trang theo thứ tự và trả về một
đơn nháp gồm thông tin khách hàng, công trường, ngày yêu cầu, dòng hàng và độ tin cậy.
Luồng đối khớp SKU, duyệt, lập kế hoạch và xác nhận sử dụng logic hiện có.

- Giới hạn: 10 MB và tối đa 20 trang mỗi tệp; tách tài liệu lớn trước khi tải.
- `pypdf` kiểm tra chữ ký, cấu trúc, mã hóa và số trang trước khi gọi AI.
- PDF lỗi, không có trang hoặc có mã hóa/mật khẩu trả 422; quá 10 MB trả 413.
- Đơn được lưu với `source_type: "pdf"`. `/api/orders/{id}/source` trả `kind: "pdf"`;
  `/source/file` trả nguyên bytes với `Content-Type: application/pdf`, kể cả khi trình duyệt
  gửi MIME thiếu hoặc sai. Không cần thay đổi schema database.
- Màn hình duyệt dùng trình xem PDF của trình duyệt và liên kết tải tệp gốc.

## AI và chế độ demo

Trong `AI_MODE=live`, Gemini dùng `Part.from_bytes(..., mime_type="application/pdf")`;
Claude dùng khối `document` với `source.type: "base64"`. Cả hai dùng schema JSON đơn hàng hiện có,
và lời nhắc đọc toàn bộ trang, thực hiện OCR ảnh/bảng, bỏ tiêu đề lặp lại.
Nguồn: [Gemini document understanding](https://ai.google.dev/gemini-api/docs/document-processing),
[Claude PDF support](https://platform.claude.com/docs/en/build-with-claude/pdf-support).

Trong `AI_MODE=demo`, PDF cần fixture đã ghi nhận, giống ảnh. Có thể thử ngay
`samples/pdf/dk-scan.pdf` qua tải lên hoặc hộp thư mẫu. Tệp này chỉ chứa ảnh đơn Đan Mạch
hiện có (5 dòng hàng), dùng cùng kết quả đã duyệt của ảnh; không gọi OCR live trong demo.
Tái tạo bằng `python -m scripts.generate_pdf_sample`.

Để ghi fixture cho tài liệu khác bằng provider đã cấu hình:

```bash
python -m scripts.record_fixture path/to/order.pdf
```

Lệnh này gọi AI thực; kiểm tra JSON được tạo trước khi dùng làm dữ liệu demo.

## Kiểm thử

```bash
AI_MODE=demo .venv/bin/python -m pytest -q
cd frontend
npm run lint
npm run build
```

Các test kiểm tra PDF văn bản và scan nhiều trang, giới hạn 20 trang/10 MB, PDF lỗi/mã hóa/rỗng,
payload gửi đến Gemini/Claude bằng client giả, fixture demo, đối khớp SKU và lưu/trả tệp gốc.
Test mặc định không gọi API AI bên ngoài. Độ chính xác OCR thực tế phụ thuộc model và chất lượng scan;
các dòng có độ tin cậy thấp tiếp tục yêu cầu người dùng kiểm tra.
