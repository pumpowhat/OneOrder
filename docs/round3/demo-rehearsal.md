# Kiểm tra demo — 17/11/2026

**Phạm vi:** kiểm tra kỹ thuật trên máy hiện tại. Người dùng xác nhận đây **không phải
laptop mang đi pitch**; buổi diễn tập ngày 20/11 vẫn chưa hoàn thành. Không có đăng nhập
Salesforce, không kiểm tra CRM live và không ngắt mạng vật lý của máy.

## Kết quả pytest

`.venv/Scripts/python.exe -m pytest -q`: **443 passed, 11 skipped, 6 xfailed**,
59,63 giây, trên Windows / Python 3.14.4. Bảy case skip mới thuộc CRM chưa merge;
bốn skip và sáu xfail còn lại thuộc suite hiện có. Không coi skip/xfail là chức năng đã đạt.

Test Confirm dùng ngày hôm nay + 30 ngày qua PATCH trước Approve; test cố ý tạo ETA
trễ vẫn giữ ngày quá khứ. Fixture demo API ép `AI_MODE=demo` để `/api/health` không
phụ thuộc cấu hình live trong `.env` cục bộ. Không sửa fixture AI hoặc backend/frontend.

## Preflight API của 4 đơn

Chạy lại từ gốc repo:

```powershell
.\.venv\Scripts\python.exe scripts/round3/rehearse_demo.py --output docs/round3/evidence/api-rehearsal.json
```

[Bằng chứng JSON](evidence/api-rehearsal.json) có phiên bản, timestamp, môi trường,
thời gian từng bước, status và kết quả kiểm chứng. Script dùng SQLite/rules/model tạm,
DemoClient và chặn DNS/kết nối ngoài trong tiến trình; loopback được cho phép cho
event loop Windows. Đây là chặn mạng của tiến trình API, không thay cho thử rút mạng thật.

| Đơn | Review / tình huống | Kết quả |
|---|---|---|
| Email Hoffmann | Thông tin đủ; requested date cố định đã qua | Chặn Confirm 409 khi chưa chấp nhận late risk; sau chấp nhận → confirmed |
| Ảnh Skanska | Nhập số `+46 70 555 12 34`, kiểm tra dòng | Chặn late risk đúng thiết kế; sau chấp nhận → confirmed |
| Excel Bygg Väst | Nhập tên, sửa dòng 3 thành 25, xác nhận dòng | Thiếu site → 422; chọn Göteborg → plan/confirmed; không có requested date nên risk null |
| PDF Lars Byg | Nhập tên, kiểm tra dòng; cross-border và xe cẩu | Tắt cross-border → thiếu gỗ/dầm; bật lại → đủ hàng; chấp nhận late risk → confirmed |

Đã kiểm: cả 4 đơn có reservation trùng phân bổ kế hoạch, tồn khả dụng giảm đúng số giữ,
các đơn đã Confirm giữ nguyên kế hoạch sau khi đổi rules. Không có lỗi chưa xử lý trong
preflight; các 409/422 trên là tình huống kiểm soát được chủ động kiểm tra.
Hash `data/rules.json`, đầu vào demo và mọi fixture AI giữ nguyên sau lượt chạy.

Số thời gian chính xác của lượt gần nhất nằm trong JSON; thời gian setup trong tiến trình
không phải thời gian khởi động đủ backend + frontend. Độ trễ API cũng không bao gồm render UI.
Lượt ghi ngày 17/11 lúc 22:30 (+07): setup **5,045 giây**, tổng **6,016 giây**;
bước API chậm nhất là plan đơn email **273 ms**. Cả 39 bước đạt kỳ vọng.

## Vấn đề khi thử đúng lệnh Bash trên Windows hiện tại

```bash
AI_MODE=demo FRESH=1 INBOX_DIR=samples/video-demo ./run-oneorder.sh start
```

Git Bash tìm thấy MSYS Python 3.12 nhưng không có `setsid` trên PATH. Launcher chỉ kiểm tra
`.venv/bin/python`, trong khi venv Windows hiện có dùng `.venv/Scripts/python.exe`, nên nó
bắt đầu tạo lại cấu hình venv và cài dependency; lượt chạy đã được dừng trước khi có app sẵn sàng.
Môi trường Python 3.14 đã được khôi phục và kiểm tra dependency/pytest lại thành công.
**Chưa đo được thời gian khởi động thành công bằng lệnh này**; không sửa launcher vì nằm
ngoài phần test/dữ liệu được giao. Cần chọn môi trường Bash/WSL phù hợp trên laptop pitch
và chạy thử lệnh trước ngày 20/11; tránh chạy trực tiếp trên venv Windows đang dùng.

## Việc cần làm trên laptop pitch ngày 20/11

- [ ] Chốt môi trường chạy, cài sẵn dependencies; kiểm tra lệnh start bằng DB trống.
- [ ] Tắt Wi-Fi/rút mạng thật, giữ `AI_MODE=demo`, mở đúng inbox 4 đơn.
- [ ] Ghi thời gian từ start đến UI sẵn sàng, import từng định dạng, Review/Plan/Confirm;
  ghi từng lỗi và bước chậm vào issue #32.
- [ ] Chạy đủ thao tác UI theo [kịch bản](../video/KichBanVideo.md), đọc ETA theo ngày thực tế;
  không đọc lại các ngày 10–12/11 cũ trong lời thoại.
- [ ] Nếu backend CRM đã merge: mock outage → Confirm thành công/Pending sync,
  khôi phục → retry synced, External ID không trùng; kiểm lại SE/NO not_applicable.
- [ ] Khởi động lại DB sạch trước lượt trình diễn/quay cuối; xác nhận rules cross-border đã phục hồi.

Video dự phòng và trạng thái duyệt: [backup-video.md](backup-video.md).
