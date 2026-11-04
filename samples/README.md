# OneOrder Sample Inputs & Test Fixtures

Thư mục này chứa bộ tệp mẫu dùng để kiểm thử tự động, tích hợp và trình diễn luồng xử lý đơn hàng đầu vào (Intake Pipeline: Photos, Emails, Excel) và giao diện Review/Approve của OneOrder.

## Danh mục tệp mẫu

| Tên tệp | Định dạng | Ngôn ngữ | Số dòng thực tế | Mục đích trình diễn & Ghi chú |
|---|---|---|:---:|---|
| `photos/dk-handwritten-1.jpg` | Ảnh JPG | Đan Mạch (DK) | 5 | Đơn viết tay từ công trường Nordhavn; gồm 1 dòng confidence thấp (0.80) để minh họa cờ review. |
| `photos/se-handwritten-1.jpg` | Ảnh JPG | Thụy Điển (SE) | 5 | Chữ viết tay vội / khó đọc tại Stockholm; 2 dòng có confidence < 0.85 để kiểm tra màn hình Review. |
| `photos/no-handwritten-1.jpg` | Ảnh JPG | Na Uy (NO) | 5 | Đơn viết tay công trường Bjørvika Barcode (Dronning Eufemias gate 16, 0191 Oslo); vật tư chuẩn Na Uy; 1 dòng cần review. |
| `emails/dk_order.txt` | Văn bản (.txt) | Đan Mạch (DK) | 5 | Email đặt hàng tiêu chuẩn Đan Mạch; kết hợp cú pháp số lượng đứng trước (`40 stk...`) và đứng sau (`... - 10 pk`). |
| `emails/se_order.txt` | Văn bản (.txt) | Thụy Điển (SE) | 5 | Email đặt hàng từ Skanska Thụy Điển; sử dụng thuật ngữ bản địa (`Brandgipsskiva`, `Regel C24`, `Akrylfog`). |
| `emails/no_order.txt` | Văn bản (.txt) | Na Uy (NO) | 5 | Email có 1 dòng thiếu số lượng (`Våtromsplate 13mm`). Bộ phân tích email bỏ qua dòng này mà không lỗi, trả về 5 dòng hợp lệ. |
| `emails/en_order.txt` | Văn bản (.txt) | Anh (EN) | 5 | Email bằng tiếng Anh từ nhà thầu quốc tế tại København; kết hợp cú pháp số lượng linh hoạt. |
| `excel/dk_materials.xlsx` | Bảng tính (.xlsx) | Đan Mạch (DK) | 5 | File BOQ định dạng Đan Mạch với tiêu đề cột `Beskrivelse`, `Antal`, `Enhed`. |
| `excel/se_material.xlsx` | Bảng tính (.xlsx) | Thụy Điển (SE) | 5 | File vật tư định dạng Thụy Điển với tiêu đề cột `Artikel`, `Antal`, `Enhet`. |
| `excel/en_boq.xlsx` | Bảng tính (.xlsx) | Anh (EN) | 4 | File BOQ tiếng Anh với tiêu đề `Product`, `Qty`, `UOM`. Có 1 dòng trống (bỏ qua) và 1 dòng số lượng dạng chuỗi `"12,5"` (đọc thành `12.5`). |

## Cơ chế Demo & Fixtures cho Ảnh

- Ở chế độ `AI_MODE=demo` (mặc định trong kiểm thử và môi trường không kết nối API AI trực tiếp), `DemoClient` ánh xạ ảnh thông qua hàm băm SHA-256 của nội dung ảnh.
- Tương ứng với mỗi ảnh trong `samples/photos/`, có một tệp fixture định dạng JSON tại `samples/fixtures/<sha256>.json`:
  - `dk-handwritten-1.jpg` (SHA256: `1a9eb8549f5b9d761084bb2dcd609354cdafaecb6509ec170d51eabf8a59f8f4`)
  - `se-handwritten-1.jpg` (SHA256: `6e9d4d3e3106aeecba67bd306cf7a21b2df95f056c460286d88ca4102009e0f4`)
  - `no-handwritten-1.jpg` (SHA256: `f4fdbcbaffcb4bc6e1d345917477f11249f9b63a5b4edab9f3ca74aad68282a6`)
- **Lưu ý:** Không sửa đổi nội dung tệp ảnh nếu không tính lại giá trị băm SHA-256 và cập nhật lại tệp fixture tương ứng.

## Dữ liệu Kỳ vọng (`samples/expected/`)

Mỗi tệp đầu vào có một tệp tương ứng trong `samples/expected/<tên_tệp>.json` ghi lại:
- `line_count`: Số lượng dòng vật tư hợp lệ trích xuất được.
- `customer`, `delivery_site`, `requested_date`: Thông tin chung của đơn hàng.
- `lines`: Danh sách từng dòng kèm `matched_sku` và cờ `needs_review`.
