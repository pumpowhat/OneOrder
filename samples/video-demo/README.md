# Bộ test cho video demo

Bốn tệp đầu vào, mỗi tệp làm lộ ra một nhóm case khác nhau ở màn hình Review. Chạy app với
`INBOX_DIR=samples/video-demo` thì Sample inbox chỉ hiện bốn tệp này.

Tạo lại bằng `python -m scripts.generate_video_samples`. PDF có fixture riêng, ghi bằng Gemini thật
(`python -m scripts.record_fixture samples/video-demo/pdf/dk-nordhavn-materialeliste.pdf`). Ảnh và email
được chép nguyên từ `samples/`, nên fixture cũ vẫn khớp (fixture tra theo SHA-256).

| Tệp | Loại | Case bao phủ |
|---|---|---|
| `pdf/dk-nordhavn-materialeliste.pdf` | PDF có lớp văn bản, tiếng Đan Mạch | **Đơn chính của video.** Ô *Kunde / firma* để trống nên **thiếu tên khách**. Có số điện thoại, địa chỉ Nordhavn (khớp `SITE-DK-01`) và ngày giao 2026-11-12. Dòng 5 *Skruer til gips* bị match **sai** sang tấm gips `GYP-13-2400`, phải chọn lại `SCR-GIP-40`. Dòng 4 dầm HEA 200 cần xác nhận. Gỗ thông Thụy Điển và dầm HEA 200 **chỉ có ở SE**, nên plan đi **cross-border** và dầm cần **xe cẩu**. |
| `excel/se-goteborg-materiallista.xlsx` | Excel tiếng Thụy Điển | **Thiếu tên khách**, thiếu địa chỉ và ngày giao (phải chọn công trường khi plan). Có cột *Telefon*, nên số điện thoại được tự điền. Dòng 3 **thiếu số lượng** (cảnh báo, confidence 0.40). `"12,5"` đọc thành 12.5. *Ljuddämpande golvmatta* không có trong catalog và bị match sai sang tấm gips. |
| `photos/se-handwritten-1.jpg` | Ảnh viết tay tiếng Thụy Điển | **Thiếu số điện thoại.** 2 dòng **confidence thấp** (0.72 và 0.70) cần kiểm tra. Chữ viết vội, có gạch xóa. |
| `emails/en_order.txt` | Email tiếng Anh | Đủ tên khách và số điện thoại. Cả 5 dòng đều cần xác nhận, vì email đọc bằng rule không bao giờ vượt ngưỡng tin cậy ở chế độ demo. |

## Kết quả kiểm thử (chạy ngày 9/11/2026, chế độ demo, DB tạm)

Đơn PDF, sau khi nhập khách *Lars Byg ApS*, sửa dòng 5 và xác nhận dòng 4:

| Shipment | Kho | Hàng | Xe | ETA P50 / P90 |
|---|---|---|---|---|
| 1 | DK-BR-01 København Sydhavn (9.5 km) | Gips 40, Rockwool 30 m2, vít 10 pk | small_truck | 9/11 / 9/11 |
| 2 | SE-DC-01 Jönköping (324.5 km), cross-border | Dầm HEA 200 × 4 | crane_truck | 10/11 / 12/11 |
| 3 | SE-DC-01 Jönköping, cross-border | Gỗ thông 60 m | small_truck | 10/11 / 12/11 |

- ETA cả đơn: P50 10/11, P90 12/11, kết luận **on_time** so với ngày yêu cầu 12/11.
- Tắt *Allow cross-border delivery* rồi plan lại: dầm HEA 200 và gỗ thông thành **shortage**. Bật lại thì plan trở về như cũ.
- Sau Confirm: SE-DC-01 gỗ thông reserved 45 → 105, available 3455 → 3395. Dầm HEA 200 reserved 45 → 49.

ETA tính theo ngày chạy. Nếu quay sau 9/11, ngày có thể dịch và đơn có thể chuyển sang `at_risk` hoặc `late`.
