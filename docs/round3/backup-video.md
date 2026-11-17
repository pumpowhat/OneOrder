# Video dự phòng 1–2 phút — bản đề xuất chờ Nghĩa duyệt

Kịch bản hiện có [KichBanVideo.md](../video/KichBanVideo.md) dài 7 phút, thuộc luồng
4 đơn hiện tại. Chưa nhận kịch bản 1–2 phút Round 3 của Nghĩa; bảng sau là phương án
rút gọn để chuẩn bị, không thay cho bản đã duyệt.

| Thời gian | Cảnh cần quay, không thuyết minh |
|---|---|
| 00:00–00:12 | Dashboard, nhãn AI: demo; mở Sample inbox 4 định dạng |
| 00:12–00:35 | Email Hoffmann: nguồn, Review, duyệt, kế hoạch, Confirm |
| 00:35–00:58 | Ảnh Skanska: bổ sung số điện thoại, kiểm dòng độ tin cậy thấp, Confirm |
| 00:58–01:20 | Excel Bygg Väst: nhập tên, sửa lượng 25, chọn Göteborg, Confirm |
| 01:20–01:45 | PDF Lars Byg: nhập tên, kiểm dòng, chỉ cross-border/xe cẩu, Confirm |
| 01:45–02:00 | Stock và Dashboard 4 Confirmed; nếu CRM đã merge, dùng bản quay đã kiểm thử để chỉ Pending sync/retry |

Chuẩn bị bằng lệnh `AI_MODE=demo FRESH=1 INBOX_DIR=samples/video-demo ./run-oneorder.sh start`.
Đọc ngày ETA thật; các ngày trong fixture đã qua, nên khi cần phải chủ động tick chấp nhận
late risk hoặc sửa ngày giao sau khi xác nhận với khách giả lập. Không sửa fixture AI.

Quay màn hình ứng dụng thật, 1920×1080, 25/30 fps, không thu mic; tránh hiện tài khoản,
token hoặc thông báo cá nhân. Nếu cắt thời gian chờ, giữ đúng thứ tự thao tác và không ghép
trạng thái CRM chưa được triển khai. Lưu MP4 H.264 để dễ phát offline, kiểm tra đủ 60–120 giây
và phát thử trên laptop pitch/USB. Chưa đánh dấu hoàn tất H3 khi chưa có bản quay được duyệt.
