# Theo dõi bàn giao Round 3

Nhánh `round3/khang-data-tests`, PR vào `main`. Thời gian dưới đây theo Asia/Saigon.
Không nộp online; pitch **thứ Bảy 21/11/2026, 13:30–18:00**, Netcompany,
Opal Tower, 92 Nguyễn Hữu Cảnh; cả Nghĩa, Nhật, Khang cần có mặt.

## Phạm vi và mốc hạn

| Phần | Hạn | Bằng chứng / việc còn lại |
|---|---|---|
| A — test Confirm | 18/11 | PATCH ngày tương đối trong helper; xem kết quả pytest và CI trong PR |
| B — license | 18/11 | [Bảng giá](license-pricing.md), có phụ phí API và tỷ giá |
| C — dữ liệu Salesforce | **18/11 theo mục C và bảng đầu ra** | [CSV và hướng dẫn](../../samples/crm/README.md); chưa nạp, chưa có screenshot |
| D — CRM tests | 19/11 | Fixture và test chờ backend Nghĩa; skip không có nghĩa đã kiểm thử CRM |
| E — hình cho slide | 20/11 | [Assets và nguồn sửa được](assets/README.md); chờ Nhật đưa vào slide và Nghĩa xác nhận B3 |
| F3 — diễn tập | 20/11 | [Báo cáo kiểm tra](demo-rehearsal.md); máy hiện tại không phải máy pitch |
| H3 — video dự phòng | 20/11 | [Video nháp 1080p, 1:52,88 và kịch bản](backup-video.md); chờ Nghĩa duyệt và phát thử máy pitch |
| H4 — QnA | 20/11 | [Bản nháp](qna.md); chờ Nghĩa/Nhật duyệt |

Đầu yêu cầu ghi C/D hạn 19/11 nhưng mục C và bảng tổng hợp ghi 18/11;
dùng **mốc sớm hơn 18/11 cho C** để chuẩn bị.

## Phần chờ người hoặc thiết bị

- [ ] **18/11 — Khang:** lấy xác nhận riêng của Nghĩa, Nhật, Khang có mặt đủ buổi pitch;
  chưa có phản hồi của cả 3, chưa đánh dấu đã xác nhận.
- [ ] **Salesforce:** người dùng xác nhận chưa đăng nhập org; cần mở Developer org được Nghĩa
  cấp quyền rồi thực hiện Data Import Wizard, tìm 4 số, chụp kết quả và thêm ảnh vào PR.
  Không ghi mật khẩu/token vào repo hoặc PR.
- [ ] **Backend CRM:** sau PR Nghĩa merge, nối đúng dependency/interface adapter, gỡ skip,
  chạy test outage/retry/idempotency/SE/NO và test khớp khách.
- [ ] **20/11 — máy pitch:** người dùng xác nhận máy hiện tại không phải máy mang đi pitch;
  chạy lại từ DB trống, tắt mạng thật, đo khởi động và đi đủ 4 đơn qua giao diện.
- [ ] **20/11 — video:** Nghĩa duyệt kịch bản 1–2 phút; quay 1920×1080 không thuyết minh,
  bản nháp đã có đủ 4 đơn và đã kiểm tra metadata/keyframe; xem lại từ đầu đến cuối,
  thử phát không mạng trên máy pitch trước khi chốt.
- [ ] **20/11 — Khang:** laptop, sạc, đầu chuyển HDMI; cắm thử vào màn hình ngoài.
- [ ] **20/11 — USB:** chép slide PDF/PPTX đã chốt và video; mở từng file từ USB trên máy pitch,
  kiểm tra font, hình, âm lượng và thời lượng. Chưa có slide/USB được cung cấp.

## Quyết định cần chốt

1. License/API thuộc vận hành DK hay dự án; Pro Suite cần quyền API/Order/External ID gì.
2. Nghĩa xác nhận B3 còn các số ngân sách đã giao. €535k là trần làm tròn;
   trần cắt 30% từ €764,5k chính xác là €535,15k.
3. Không coi CRM trong sơ đồ sau là tính năng đã có trên main; dùng ngôn ngữ thiết kế
   đến khi backend/frontend merge và kiểm thử thành công.
