# Bộ test cho video demo

Bốn tệp đầu vào, xếp từ **dễ đến khó**. Chạy app với `INBOX_DIR=samples/video-demo` thì Sample inbox chỉ hiện bốn tệp này.

Tạo lại bằng `python -m scripts.generate_video_samples`. Email, ảnh và PDF dùng chế độ demo nên mỗi tệp cần một fixture (kết quả AI đã ghi, tra theo SHA-256 của nội dung):

- Ảnh dùng lại fixture sẵn có của `samples/photos/se-handwritten-1.jpg` (chép nguyên, không sửa byte nào).
- Email và PDF được ghi bằng AI thật: `python -m scripts.record_fixture samples/video-demo/emails/dk-odense-order.txt` và tương tự cho PDF. **Sửa nội dung hai tệp này thì phải ghi lại fixture.**
- Excel không cần fixture.

| # | Tệp | Loại | Case bao phủ |
|---|---|---|---|
| 1 | `emails/dk-odense-order.txt` | Email tiếng Anh | **Đơn lý tưởng.** Đủ tên khách (*Hoffmann Byg A/S*), số điện thoại, địa chỉ Odense (khớp `SITE-DK-04`) và ngày giao 2026-11-13. Cả 5 dòng khớp đúng tên sản phẩm, độ tin cậy 0.99, **không dòng nào cần review**. Duyệt ngay không sửa gì. |
| 2 | `photos/se-handwritten-1.jpg` | Ảnh viết tay tiếng Thụy Điển | **Thiếu số điện thoại.** 2 dòng **độ tin cậy thấp** (0.72 và 0.70) cần xác nhận. |
| 3 | `excel/se-goteborg-materiallista.xlsx` | Excel tiếng Thụy Điển | **Thiếu tên khách.** Dòng 3 **thiếu số lượng** (đọc thành 0, confidence 0.40, cảnh báo). Dòng 4 *Träskruv 5x80mm* mô tả mơ hồ, gợi ý đúng `SCR-WOOD-580` nhưng cần xác nhận. `"12,5"` đọc thành 12.5. **Không có địa chỉ giao hàng**, nên phải **chọn công trường tay** khi plan (không chọn thì API trả 422). Số điện thoại tự điền từ cột *Telefon*. |
| 4 | `pdf/dk-nordhavn-materialeliste.pdf` | PDF có lớp văn bản, tiếng Đan Mạch | **Thiếu tên khách** (ô *Kunde / firma* trống). Dòng 4 dầm HEA 200 và dòng 5 *Skruer til gips* cần xác nhận. Gỗ thông Thụy Điển và dầm HEA 200 **chỉ có ở SE**, nên plan đi **cross-border** và dầm cần **xe cẩu**. Đổi rules (tắt cross-border) thì hai dòng này thành shortage. |

## Kết quả kiểm thử

Chạy ngày 9/11/2026, chế độ demo, DB trống, đủ 4 đơn từ import đến Confirm. Cả 4 đơn đều thành `confirmed`.

| Đơn | Thao tác của người | Công trường | Shipment | ETA P50 / P90 |
|---|---|---|---|---|
| 1 Email | Chỉ bấm Approve | SITE-DK-04 (tự nhận) | DK-BR-02 (107.8 km, heavy_truck): gips, bông khoáng. DK-BR-03 (1.4 km, small_truck): xi măng, gỗ, keo. | 10/11 / 11/11 |
| 2 Ảnh | Nhập SĐT, xác nhận dòng 2 và 4 | SITE-SE-01 (tự nhận) | SE-BR-01 (8.4 km): gips chống cháy, bông thủy tinh. SE-DC-01 (369.2 km): gỗ, vít, xi măng. | 10/11 / 11/11 |
| 3 Excel | Nhập tên, sửa số lượng dòng 3 thành 25, xác nhận dòng 4, **chọn SITE-SE-02** | SITE-SE-02 (chọn tay) | SE-BR-02 (1.6 km): gips, vít gỗ, vít gips. SE-DC-01 (171.8 km): bông thủy tinh, gỗ. | 10/11 / 11/11 |
| 4 PDF | Nhập tên, xác nhận dòng 4 và 5 | SITE-DK-01 (tự nhận) | DK-BR-01 (9.5 km): gips, bông khoáng, vít. SE-DC-01 cross-border (324.5 km): dầm HEA 200 (**crane_truck**) và gỗ thông. | 10/11 / 12/11 |

- Đơn 4, tắt *Allow cross-border delivery* rồi plan lại: dầm HEA 200 và gỗ thông thành **shortage**, chỉ còn shipment DK-BR-01. Bật lại thì plan trở về như cũ.
- Đổi rules **không** làm thay đổi plan của đơn 2 (đã confirm).
- Đơn Excel chưa chọn công trường mà bấm plan: API trả 422 "Cannot resolve delivery site".

### Tồn kho sau khi Confirm cả 4 đơn (reserved và available, trước → sau)

| SKU | Kho | Reserved | Available | Từ đơn |
|---|---|---|---|---|
| GYP-13-2400 | DK-BR-02 | 5 → 65 | 67 → 7 | 1 |
| GYP-13-2400 | DK-BR-01 | 6 → 46 | 96 → 56 | 4 |
| GYP-15-FIRE | SE-BR-01 | 18 → 58 | 149 → 109 | 2 |
| SCR-WOOD-580 | SE-BR-02 | 15 → 35 | 135 → 115 | 3 |
| TIM-SE-PINE45 | SE-DC-01 | 45 → 105 | 3455 → 3395 | 4 |
| ARM-BEAM-HEA200 | SE-DC-01 | 45 → 49 | 805 → 801 | 4 |

ETA tính theo ngày chạy. Nếu quay sau 9/11, ngày có thể dịch và đơn có thể chuyển sang `at_risk` hoặc `late`.
