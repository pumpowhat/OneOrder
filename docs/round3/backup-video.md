# Video dự phòng 1–2 phút — bản đề xuất chờ Nghĩa duyệt

**Đã quay bản nháp ngày 17/11/2026:** [oneorder-backup-DRAFT.mp4](evidence/oneorder-backup-DRAFT.mp4),
**1 phút 52,88 giây**, 1920×1080, H.264 High/yuv420p, 25 fps, không có audio, khoảng 3,61 MB.
Đây là màn hình ứng dụng thật ở chế độ demo, DB riêng: cả 4 đơn đi từ import/Review
đến Confirm; có cross-border, xe cẩu, tồn kho và Dashboard 4 Confirmed.
Ba đơn có ngày lịch sử được chủ động chấp nhận late risk. Chưa có cảnh CRM vì backend/UI
CRM chưa merge; vẫn chờ Nghĩa duyệt kịch bản và phát thử trên laptop pitch/USB.

[Nhật ký thao tác thật](evidence/backup-draft-recording.json) xác minh 4 đơn confirmed,
không lỗi trình duyệt, không request ngoài localhost; [metadata và QA](evidence/backup-draft-qa.json)
có SHA-256 và các khung hình đã xem ở 40/80/108 giây. Các khoảng dừng trong video phục vụ
người xem, không dùng để suy ra độ trễ hệ thống. Chưa thử ngắt mạng vật lý.

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

## Quay lại từ nguồn

[record_backup.mjs](../../scripts/round3/record_backup.mjs) khởi động backend/Vite cục bộ
với `AI_MODE=demo`, SQLite tạm và inbox video; dùng Playwright thao tác thật, rồi ffmpeg
chuyển thành MP4. Cần cài trước requirements Python, dependencies frontend,
Playwright/Chromium và ffmpeg H.264; có thể cài `imageio-ffmpeg` trong môi trường biên soạn.
Các thư viện này không thêm vào dependency ứng dụng.

```powershell
# Nếu Playwright ở ngoài repo, đặt PLAYWRIGHT_MODULES tới thư mục node_modules đó.
# Có thể đặt PYTHON_EXE, FFMPEG_EXE, VIDEO_BACKEND_PORT và VIDEO_FRONTEND_PORT.
node scripts/round3/record_backup.mjs
```

Recorder ghi đè file video/bằng chứng cùng tên. Cần có môi trường authoring đã chuẩn bị,
không thay cho lệnh khởi động và diễn tập chính thức trên laptop pitch.
