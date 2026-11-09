# Kịch bản video demo OneOrder (7 phút)

Bộ test: [samples/video-demo/](../../samples/video-demo/README.md). Lời thoại viết bằng tiếng Việt để đọc. Tên nút, tên tab và nhãn trên màn hình viết **nguyên văn tiếng Anh** vì giao diện đang để tiếng Anh, bạn bấm theo đúng chữ đó.

## Tóm tắt luồng quay

Import **4 đơn**, chỉ **plan 2 đơn**:

| Đơn | Làm gì |
|---|---|
| **Ảnh viết tay (Thụy Điển)** | Review, nhập số điện thoại, plan **luôn**, Confirm. |
| **PDF (Đan Mạch)** | Review, nhập tên khách, sửa dòng sai, plan, **đổi rules, plan lại**, Confirm. |
| Excel (Thụy Điển) | Chỉ xem lỗi ở màn hình Review, **không duyệt**. |
| Email (tiếng Anh) | Chỉ import, **không duyệt**. |

Hai đơn Excel và email nằm lại ở "To review" trên Dashboard, cho thấy hệ thống xử lý nhiều đơn cùng lúc.

## Chuẩn bị trước khi quay

1. Ở nhánh `demo/video-recording`. Kiểm tra `data/rules.json` còn `"allow_cross_border": true`.
2. Khởi động bằng DB trống và inbox riêng:
   ```bash
   AI_MODE=demo FRESH=1 INBOX_DIR=samples/video-demo ./run-oneorder.sh start
   ```
   Phải truyền `AI_MODE=demo` trên dòng lệnh. Script không đọc `AI_MODE` trong `.env`, mà `.env` có API key, nên thiếu biến này app sẽ chạy **live**.
3. Mở `http://localhost:5173`, chuyển giao diện sang **English**, phóng trình duyệt khoảng 110–125%.
4. Mở sẵn thư mục `samples/video-demo/pdf/` trong file manager để kéo thả. Chép sẵn nội dung `samples/video-demo/emails/en_order.txt` vào clipboard.
5. Chuẩn bị sẵn để gõ: số điện thoại `+46 70 555 12 34` (đơn ảnh) và tên khách `Lars Byg ApS` (đơn PDF).
6. **Chạy thử một lượt**, rồi tắt app (Ctrl-C) và khởi động lại bằng đúng lệnh trên để có DB sạch trước khi quay thật.
7. Quay xong chạy `git checkout data/rules.json`. Màn hình Rules ghi thẳng vào file này và tăng version mỗi lần Save.

Về chế độ demo: kết quả đọc PDF và ảnh là kết quả **Gemini thật đã ghi lại** (fixture), phát lại để video không phụ thuộc mạng hay quota. Góc trên hiện "AI: demo". Cảnh 2 có câu thoại nói rõ điều này.

## Phân bổ thời gian

| Cảnh | Nội dung | Thời gian |
|---|---|---|
| 1 | Giới thiệu các tab | 0:00–0:40 |
| 2 | Nhập 4 loại đầu vào | 0:40–1:30 |
| 3 | Đơn ảnh: review và duyệt | 1:30–2:15 |
| 4 | Đơn Excel: xem lỗi, không duyệt | 2:15–2:40 |
| 5 | Đơn ảnh: plan luôn và Confirm | 2:40–3:20 |
| 6 | Đơn PDF: review và duyệt | 3:20–4:10 |
| 7 | Đơn PDF: lên plan | 4:10–4:40 |
| 8 | Đổi rules, plan lại | 4:40–5:40 |
| 9 | Đơn PDF: Confirm | 5:40–6:05 |
| 10 | Kiểm tra tồn kho | 6:05–6:40 |
| 11 | Kết | 6:40–7:00 |

---

## Cảnh 1: Giới thiệu các tab (0:00–0:40)

| Thao tác | Lời thoại |
|---|---|
| Mở **Dashboard**. | "Đây là OneOrder, một lớp điều phối nằm trên các ERP quốc gia của Đan Mạch, Thụy Điển và Na Uy. Nó biến những đơn hàng lộn xộn của nhà thầu thành đơn đã xác nhận, kèm ngày giao đáng tin cậy." |
| Chỉ qua 4 ô đếm *To review / Ready to plan / To confirm / Confirmed*. | "Dashboard theo dõi mọi đơn qua bốn bước: kiểm tra, lên kế hoạch, xác nhận, hoàn tất." |
| Bấm **Orders**. | "Tab Orders là nơi đơn hàng đi vào: tải file, dán email hoặc lấy từ hộp thư chung." |
| Bấm **Stock**. | "Tab Stock cho một cái nhìn tồn kho chung của cả ba nước." |
| Bấm **Rules**. | "Còn Rules là nơi cấu hình cách chọn kho và chọn xe. Quy tắc nằm trong cấu hình, không nằm trong mã nguồn. Lát nữa chúng ta sẽ đổi một quy tắc ngay trên màn hình này." |

## Cảnh 2: Nhập 4 loại đầu vào (0:40–1:30)

| Thao tác | Lời thoại |
|---|---|
| Vào **Orders**. Kéo `dk-nordhavn-materialeliste.pdf` vào ô *Upload an order*. Chờ "Order read". | "Anh Lars, đốc công ở Copenhagen, gửi một danh sách vật tư dạng PDF. Tôi chỉ cần thả file vào. AI đọc từng dòng vật tư, số điện thoại, địa chỉ giao hàng và ngày yêu cầu." |
| Ở **Sample inbox**, bấm *Import order* cho `se-handwritten-1.jpg`. | "Tiếp theo là ảnh chụp một tờ ghi chú viết tay tiếng Thụy Điển, có cả chỗ gạch xóa." |
| Bấm *Import order* cho `se-goteborg-materiallista.xlsx`. | "Một bảng Excel của nhà thầu Thụy Điển." |
| Mở *Or paste the email text*, dán email, bấm **Read email**. | "Và một email thường bằng tiếng Anh. Bốn định dạng, bốn ngôn ngữ, chung một hàng đợi." |
| Chỉ vào nhãn "AI: demo". | "Trong video này chúng tôi phát lại kết quả mà Gemini đã đọc từ trước để demo không phụ thuộc mạng. Ở chế độ live thì cùng lệnh gọi đó được gửi tới mô hình." |

## Cảnh 3: Đơn ảnh, review và duyệt (1:30–2:15)

| Thao tác | Lời thoại |
|---|---|
| Mở đơn **ảnh viết tay (Skanska)**. Chỉ vào cột *Original file* bên cạnh *What the system read*. | "Bên trái là ảnh gốc, bên phải là những gì hệ thống đọc được, nên kiểm tra chỉ mất vài giây." |
| Chỉ vào dòng 2 và dòng 4 có nhãn *check* (AI 72%, AI 70%). | "Hệ thống không tin AI mù quáng. Dòng nào độ tin cậy dưới 85% đều bị gắn cờ. Ở đây có hai dòng chữ viết vội, cần người xem lại." |
| Tick xác nhận dòng 2 và dòng 4. | "Tôi đối chiếu với ảnh gốc, hai dòng này đúng, nên xác nhận." |
| Chỉ vào ô số điện thoại trống và nút *Approve OCR result* bị khóa. | "Tờ ghi chú không có số điện thoại, nên nút Approve vẫn bị khóa cho đến khi nhân viên nhập số liên hệ." |
| Gõ `+46 70 555 12 34`, bấm **Approve OCR result**. | "Mọi chỉnh sửa đều được ghi lại. Đơn giờ đã sẵn sàng để lên kế hoạch." |

## Cảnh 4: Đơn Excel, xem lỗi nhưng không duyệt (2:15–2:40)

| Thao tác | Lời thoại |
|---|---|
| Quay lại **Orders**, mở đơn **Excel**. Chỉ cảnh báo *quantity is missing*, dòng *golvmatta* bị gắn *check*, ô tên khách trống. | "Với bảng Excel này, một dòng thiếu số lượng, và tấm lót sàn không có trong danh mục sản phẩm. Thay vì đoán ngầm, hệ thống đánh dấu để người kiểm tra. Đơn này tôi để lại, chưa duyệt." |
| Bấm **All orders** để quay về danh sách. | |

## Cảnh 5: Đơn ảnh, lên plan luôn và Confirm (2:40–3:20)

| Thao tác | Lời thoại |
|---|---|
| Mở lại đơn ảnh (đã *Ready to plan*). Chỉ vào *Deliver to* tự nhận **Solnavägen 12, Stockholm**. Bấm **Make plan**. | "Công trường được nhận ra tự động từ địa chỉ. Tôi bấm lên kế hoạch." |
| Chỉ vào **2 shipment**. | "OneOrder xem tồn kho của cả ba ERP rồi chọn nguồn theo quy tắc: chi nhánh gần nhất trước, rồi đến trung tâm phân phối trong nước." |
| Shipment 1: chỉ lý do *Nearest branch with full stock*. | "Tấm thạch cao chống cháy và bông thủy tinh lấy từ chi nhánh Stockholm, cách công trường tám cây số." |
| Shipment 2: chỉ DC trong nước. | "Phần còn lại, gỗ, vít và xi măng, lấy từ trung tâm phân phối Jönköping." |
| Chỉ **Expected (P50)** và **Safe commitment (P90)**. | "Dự kiến giao ngày 10, và mốc an toàn có thể hứa với khách là ngày 11. Đều trước hạn yêu cầu." |
| Bấm **Confirm order**. | "Xác nhận sẽ giữ hàng trong từng ERP và khóa kế hoạch cùng ngày giao đã hứa." |

## Cảnh 6: Đơn PDF, review và duyệt (3:20–4:10)

| Thao tác | Lời thoại |
|---|---|
| Mở đơn **PDF**. Chỉ vào *Original file* và *What the system read*, rồi vào ô **Customer name** trống. | "Quay lại đơn của anh Lars. Ô tên khách trong PDF bị bỏ trống, nên hệ thống bắt buộc phải nhập tên trước khi duyệt." |
| Gõ `Lars Byg ApS`. | |
| Dòng 5 *Skruer til gips*: chỉ vào SKU `GYP-13-2400`. Mở *Choose a product*, chọn **SCR-GIP-40**. | "Đây là một lỗi thật: 'vít bắt thạch cao' bị ghép nhầm với chính tấm thạch cao. Tôi chọn lại đúng sản phẩm: vít thạch cao 3,9 nhân 40." |
| Dòng 4 dầm HEA 200: tick xác nhận. | "Dầm thép ghép đúng, nên tôi chỉ xác nhận." |
| Bấm **Approve OCR result**. | "Đơn đã sẵn sàng lên kế hoạch." |

## Cảnh 7: Đơn PDF, lên plan (4:10–4:40)

| Thao tác | Lời thoại |
|---|---|
| Chỉ *Deliver to* tự nhận công trường **Nordhavn**. Bấm **Make plan**. | "Công trường Nordhavn được nhận ra từ địa chỉ." |
| Chỉ **3 shipment**. Shipment 1: *Nearest branch with full stock: DK-BR-01 (9.5 km)*. | "Thạch cao, bông khoáng và vít lấy từ chi nhánh Sydhavn ở Đan Mạch, cách chín cây số rưỡi." |
| Shipment 2 và 3: chỉ nhãn **Cross-border** và **Crane needed**. | "Gỗ thông Thụy Điển và dầm HEA 200 không có ở kho Đan Mạch nào, nên được lấy từ trung tâm phân phối Jönköping bên Thụy Điển. Mỗi dầm nặng hơn hai trăm rưỡi ký, cần cẩu lên sàn, nên hệ thống tự xếp xe cẩu." |
| Chỉ **Expected (P50)** 10/11 và **Safe commitment (P90)** 12/11. | "Ngày dự kiến là 10, mốc an toàn là 12, vẫn kịp ngày khách yêu cầu." |

## Cảnh 8: Đổi rules và plan lại (4:40–5:40)

| Thao tác | Lời thoại |
|---|---|
| Vào **Rules**. | "Giả sử ban lãnh đạo quyết định: tạm dừng giao hàng xuyên biên giới." |
| Tắt **Allow cross-border delivery**, bấm **Save**. Chỉ thông báo *Rules saved (version …)*. | "Chỉ cần gạt một công tắc, lưu lại, có đánh số phiên bản, không cần lập trình viên, không cần triển khai lại." |
| Quay lại đơn PDF, bấm **Re-plan**. Chỉ khung *Some items are not fully in stock*. | "Lập lại kế hoạch: gỗ thông và dầm thép giờ thành thiếu hàng, kèm lý do cụ thể. Quy tắc đổi thì quyết định đổi theo, và hệ thống giải thích được vì sao." |
| Vào **Rules**, bật lại cross-border, **Save**. Quay lại đơn, **Re-plan**. | "Bật lại, và kế hoạch đầy đủ quay trở lại. Đơn Confirm trước đó (đơn Thụy Điển) vẫn giữ nguyên kế hoạch cũ, vì kế hoạch đã xác nhận được khóa với phiên bản quy tắc lúc tạo." |

> Câu cuối của dòng này dựa trên ghi chú trong [rules.py](../../backend/routers/rules.py): "plans already stored keep the rules_version they were made with". Nếu không muốn nói ý này trong video thì bỏ câu cuối đi.

## Cảnh 9: Đơn PDF, Confirm (5:40–6:05)

| Thao tác | Lời thoại |
|---|---|
| Bấm **Confirm order**. Chỉ *Stock reserved: 5 lines. Plan and ETA are locked.* | "Xác nhận sẽ giữ hàng trong từng ERP quốc gia chỉ bằng một thao tác, và khóa kế hoạch cùng ngày giao đã hứa." |
| Kéo xuống phần **History**. | "Lịch sử cho thấy ai đã đọc, sửa, duyệt, lên kế hoạch và xác nhận đơn này." |
| *(Nếu ETA hiện `late`: tick *Confirm even though delivery is predicted after the requested date* rồi mới Confirm.)* | *("Nếu ngày giao có rủi ro trễ, nhân viên phải chủ động chấp nhận rủi ro, hoặc gọi cho khách và hứa theo mốc P90.")* |

## Cảnh 10: Kiểm tra tồn kho (6:05–6:40)

| Thao tác | Lời thoại |
|---|---|
| Vào **Stock**, tìm `Svensk furu`. Mở dòng SE-DC-01. | "Ở tab Stock, gỗ thông Thụy Điển tại Jönköping giờ có thêm 60 mét bị giữ, còn lại 3.395 mét thay vì 3.455." |
| Tìm `HEA 200`. | "Bốn dầm thép cũng đã được giữ, nên không đơn nào khác có thể hứa cùng số hàng đó." |
| Tìm `Brandgipsskiva` (hoặc `GYP-15-FIRE`). | "Đơn Thụy Điển lúc nãy cũng đã giữ hàng tại chi nhánh Stockholm và trung tâm Jönköping." |

## Cảnh 11: Kết (6:40–7:00)

| Thao tác | Lời thoại |
|---|---|
| Quay lại **Dashboard**. Chỉ ô *Confirmed* (2 đơn) và *To review* (Excel, email). | "Từ một tờ PDF hay một tấm ảnh viết tay, OneOrder đưa ra đơn hàng đã xác nhận, giải thích được, chỉ trong vài phút. AI lo việc đọc, con người đưa ra quyết định, và các ERP hiện có vẫn giữ nguyên. Đó là OneOrder. Cảm ơn mọi người đã xem." |

---

## Lưu ý khi quay

- **ETA phụ thuộc ngày quay.** Các ngày 10, 11, 12 trong lời thoại là kết quả chạy thử ngày 9/11. Nếu quay ngày khác, ngày sẽ dịch, và đơn PDF có thể thành `at_risk` hoặc `late`. Hãy đọc ngày thật trên màn hình thay vì đọc theo kịch bản.
- **Nếu thiếu thời gian:** bỏ cảnh 4 (Excel) trước, rồi bỏ dòng "Bấm *How is this predicted?*". Không bỏ cảnh 8 (đổi rules) và cảnh 10 (tồn kho), đây là hai bằng chứng rõ nhất.
- **Số liệu tồn kho** (3.455 → 3.395) lấy từ DB sạch. Nếu bạn chạy thử mà không tắt và khởi động lại app, số sẽ lệch.
- Tôi chưa xem giao diện thật trên trình duyệt. Tên nút lấy từ file i18n tiếng Anh, nên hãy chạy thử một lượt để chắc chắn khớp.
