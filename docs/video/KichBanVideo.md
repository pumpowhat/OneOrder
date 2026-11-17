# Kịch bản video demo OneOrder (7 phút)

Bộ test: [samples/video-demo/](../../samples/video-demo/README.md). Lời thoại viết bằng tiếng Việt để đọc. Tên nút, tên tab và nhãn trên màn hình viết **nguyên văn tiếng Anh** vì giao diện đang để tiếng Anh, bạn bấm theo đúng chữ đó.

## Ý tưởng

Import **cả 4 đơn** một lần, rồi xử lý **từng đơn một, từ review OCR đến plan và Confirm**, theo thứ tự **từ dễ đến khó**. Việc sửa (tên khách, số điện thoại, số lượng, sản phẩm) làm trong form **Edit draft**, bấm **Save draft**, rồi mới **Approve OCR result**. Mỗi đơn thêm một tình huống cần người can thiệp, đến đơn cuối thì đổi cả rules. Cuối cùng kiểm tra tồn kho cho cả 4 đơn.

| # | Đơn | Nguồn | Cần làm gì | Chỉ ra điều gì |
|---|---|---|---|---|
| 1 | Hoffmann Byg A/S | Email | **Không cần sửa gì**, Approve rồi plan | Trường hợp lý tưởng: AI đọc đúng hết, người chỉ bấm duyệt. |
| 2 | Skanska Sverige AB | Ảnh viết tay | **Nhập số điện thoại**, xác nhận 2 dòng độ tin cậy thấp | Hệ thống không tin AI mù quáng. |
| 3 | (thiếu tên) | Excel | **Nhập tên khách**, **sửa số lượng** thiếu, xác nhận 1 dòng, **chọn công trường tay** | Nhiều thiếu sót cùng lúc, nhưng vẫn đi hết luồng. |
| 4 | (thiếu tên) | PDF | **Nhập tên khách**, xác nhận 2 dòng, plan cross-border + xe cẩu, **đổi rules rồi plan lại** | Quy tắc nghiệp vụ đổi được tại chỗ. |

## Chuẩn bị trước khi quay

1. Ở nhánh `demo/video-recording`. Kiểm tra `data/rules.json` còn `"allow_cross_border": true`.
2. Khởi động bằng DB trống và inbox riêng:
   ```bash
   AI_MODE=demo FRESH=1 INBOX_DIR=samples/video-demo ./run-oneorder.sh start
   ```
   Phải truyền `AI_MODE=demo` trên dòng lệnh. Script không đọc `AI_MODE` trong `.env`, mà `.env` có API key, nên thiếu biến này app sẽ chạy **live**.
3. Mở `http://localhost:5173`, chuyển giao diện sang **English**, phóng trình duyệt khoảng 110–125%.
4. Chuẩn bị sẵn các thứ sẽ gõ (có thể dán từ ghi chú):

   | Đơn | Gõ gì |
   |---|---|
   | Ảnh | số điện thoại `+46 70 555 12 34` |
   | Excel | tên khách `Bygg Väst AB`, số lượng dòng 3 là `25`, công trường chọn **Göteborg** |
   | PDF | tên khách `Lars Byg ApS` |

5. **Chạy thử một lượt**, rồi tắt app (Ctrl-C) và khởi động lại bằng đúng lệnh trên để có DB sạch trước khi quay thật.
6. Quay xong chạy `git checkout data/rules.json`. Màn hình Rules ghi thẳng vào file này và tăng version mỗi lần Save.

Về chế độ demo: kết quả đọc email, ảnh và PDF là kết quả **AI thật đã ghi lại** (fixture), phát lại để video không phụ thuộc mạng hay quota. Góc trên hiện "AI: demo". Cảnh 2 có câu thoại nói rõ điều này.

## Phân bổ thời gian

| Cảnh | Nội dung | Thời gian |
|---|---|---|
| 1 | Giới thiệu các tab | 0:00–0:35 |
| 2 | Import cả 4 đơn | 0:35–1:15 |
| 3 | Đơn 1, Email: lý tưởng | 1:15–1:55 |
| 4 | Đơn 2, Ảnh: thiếu số điện thoại | 1:55–2:50 |
| 5 | Đơn 3, Excel: thiếu tên, số lượng, công trường | 2:50–3:55 |
| 6 | Đơn 4, PDF: review, plan | 3:55–5:00 |
| 7 | Đơn 4, PDF: đổi rules, plan lại, Confirm | 5:00–6:05 |
| 8 | Kiểm tra tồn kho cho cả 4 đơn | 6:05–6:50 |
| 9 | Kết | 6:50–7:00 |

Nhịp rất chặt: mỗi đơn dưới 1 phút, nên đọc nhanh và thao tác dứt khoát, đừng chờ màn hình. Nếu quay thấy dài, xem mục "Nếu thiếu thời gian" ở cuối.

---

## Cảnh 1: Giới thiệu các tab (0:00–0:35)

| Thao tác | Lời thoại |
|---|---|
| Mở **Dashboard**. | "Đây là OneOrder, một lớp điều phối nằm trên các ERP quốc gia của Đan Mạch, Thụy Điển và Na Uy. Nó biến những đơn hàng lộn xộn của nhà thầu thành đơn đã xác nhận, kèm ngày giao đáng tin cậy." |
| Chỉ qua 4 ô đếm *To review / Ready to plan / To confirm / Confirmed*. | "Mọi đơn đi qua bốn bước: kiểm tra, lên kế hoạch, xác nhận, hoàn tất." |
| Bấm lần lượt **Orders**, **Stock**, **Rules**. | "Orders là nơi đơn đi vào: tải file, lấy từ hộp thư, hoặc nhập tay bằng nút Create manual order. Stock là tồn kho chung của cả ba nước. Còn Rules là nơi cấu hình cách chọn kho và chọn xe, nằm trong cấu hình chứ không nằm trong mã nguồn. Lát nữa tôi sẽ đổi một quy tắc ngay tại đây." |

## Cảnh 2: Import cả 4 đơn (0:35–1:15)

| Thao tác | Lời thoại |
|---|---|
| Vào **Orders**. Ở **Sample inbox**, bấm *Import order* lần lượt cho 4 file: email `dk-odense-order.txt`, ảnh `se-handwritten-1.jpg`, Excel `se-goteborg-materiallista.xlsx`, PDF `dk-nordhavn-materialeliste.pdf`. Chờ cả 4 đơn xuất hiện. | "Hôm nay hộp thư nhận bốn đơn, bốn định dạng, bốn kiểu viết: một email, một ảnh chụp tay, một bảng Excel và một file PDF. Tôi nhập tất cả vào, và AI đọc từng đơn." |
| Chỉ vào danh sách: hai đơn hiện **"Unknown customer"** (Excel và PDF), hai đơn có tên (Hoffmann, Skanska). | "Có đơn AI đọc được tên khách, có đơn thì không: Excel và PDF này khách không điền tên công ty, nên hệ thống ghi 'Unknown customer'. Chúng ta sẽ xử lý từng đơn, từ dễ đến khó." |
| Chỉ nhãn "AI: demo". | "Trong video này, chúng tôi phát lại kết quả AI đã đọc từ trước để demo không phụ thuộc mạng. Ở chế độ live, cùng lệnh gọi đó được gửi tới mô hình." |

## Cảnh 3: Đơn 1, Email, trường hợp lý tưởng (1:15–1:55)

| Thao tác | Lời thoại |
|---|---|
| Mở đơn **Hoffmann Byg A/S**. Chỉ cả 5 dòng không có nhãn *check*, tên khách và số điện thoại đã điền sẵn. | "Đơn đầu tiên là trường hợp lý tưởng: khách ghi rõ tên, số điện thoại, địa chỉ, ngày giao, và từng sản phẩm khớp đúng danh mục. AI đọc với độ tin cậy 99%, không dòng nào bị gắn cờ." |
| Bấm **Approve OCR result**, không sửa gì. | "Với đơn như vậy, nhân viên chỉ cần bấm duyệt, một cú click." |
| Bấm **Make plan** (để *Detect from address*). Chỉ *Deliver to* nhận ra công trường Odense, lướt 2 shipment. | "Công trường được nhận ra tự động từ địa chỉ. Hệ thống xem tồn kho cả ba ERP, chọn chi nhánh đủ hàng trước, và giải thích lý do cho từng shipment. Ngày dự kiến là 10, ngày an toàn có thể hứa là 11." |
| Bấm **Confirm order**. | "Xác nhận một lần: giữ hàng trong ERP và khóa kế hoạch cùng ngày đã hứa." |
| Bấm **All orders**. | |

## Cảnh 4: Đơn 2, Ảnh viết tay, thiếu số điện thoại (1:55–2:50)

| Thao tác | Lời thoại |
|---|---|
| Mở đơn **Skanska Sverige AB**. Chỉ *Original file* bên cạnh *What the system read*. | "Đơn thứ hai là ảnh chụp tờ ghi chú viết tay tiếng Thụy Điển. Bên trái là ảnh gốc, bên phải là điều hệ thống đọc được, nên kiểm tra rất nhanh." |
| Chỉ dòng 2 và dòng 4 có nhãn *check* (AI 72% và 70%). | "Hệ thống không tin AI mù quáng: dòng nào độ tin cậy dưới 85% đều bị gắn cờ. Ở đây có hai dòng chữ viết vội." |
| Chỉ nút **Approve OCR result** đang khóa và dòng nhắc nhập số điện thoại. Bấm **Edit draft**. | "Tờ ghi chú không có số điện thoại, nên nút Approve vẫn khóa. Muốn sửa thông tin, nhân viên bấm Edit draft." |
| Trong form: gõ `+46 70 555 12 34` vào ô điện thoại (giữ cờ Thụy Điển). **Tick "I have checked this product and quantity" ở cả 5 dòng.** Bấm **Save draft**. | "Tôi nhập số điện thoại. Rồi tôi đối chiếu từng dòng với ảnh gốc: hai dòng chữ viết vội đều đúng. Tôi đánh dấu đã kiểm tra, rồi lưu nháp." |
| Quay lại màn hình Review, chỉ *All lines checked*. Bấm **Approve OCR result**. Bấm **Make plan**. Lướt 2 shipment (chi nhánh Stockholm 8 km, DC Jönköping). Bấm **Confirm order**, **All orders**. | "Mọi dòng đã kiểm, nên duyệt được. Lên kế hoạch: tấm thạch cao và bông thủy tinh từ chi nhánh Stockholm cách tám cây số, phần còn lại từ trung tâm Jönköping. Ngày dự kiến 10, an toàn 11. Xác nhận." |

## Cảnh 5: Đơn 3, Excel, thiếu tên, số lượng và công trường (2:50–3:55)

| Thao tác | Lời thoại |
|---|---|
| Mở đơn **Unknown customer** có số điện thoại `+46 70 123 45 67` (đó là đơn Excel, đơn kia là PDF). Chỉ cảnh báo *quantity is missing*. | "Đơn thứ ba là bảng Excel, khó hơn. Số điện thoại tự điền từ cột *Telefon*, nhưng có ba vấn đề: thiếu tên khách, một dòng thiếu số lượng, và không có địa chỉ giao hàng." |
| Bấm **Edit draft**. Gõ tên khách `Bygg Väst AB`. | "Tên khách thì nhập tay." |
| Dòng 3 *Regel C24 45x145mm 4.8m*: đổi **Quantity** từ `0` thành `25`. | "Dòng này khách bỏ trống số lượng. Hệ thống không đoán, mà để số 0 và gắn cờ. Tôi hỏi lại khách và nhập 25." |
| Dòng 4 *Träskruv 5x80mm*: chỉ SKU gợi ý `SCR-WOOD-580`. **Tick "I have checked…" ở cả 5 dòng**. Bấm **Save draft**. | "Dòng này mô tả hơi mơ hồ, hệ thống gợi ý đúng vít gỗ 5 nhân 80, nhưng vẫn bắt người xác nhận. Tôi kiểm tra các dòng, rồi lưu nháp." |
| Bấm **Approve OCR result**. Ở ô chọn công trường (mặc định *Detect from address: —*), chọn **Göteborg**. Bấm **Make plan**. | "Bảng Excel không có địa chỉ, nên hệ thống không tự nhận công trường. Tôi chọn tay công trường Göteborg. Nếu cứ bấm lên kế hoạch mà không chọn, hệ thống sẽ từ chối và nhắc chọn." |
| Lướt 2 shipment (chi nhánh Göteborg 1,6 km, DC Jönköping 172 km). Bấm **Confirm order**, **All orders**. | "Kế hoạch ra hai shipment: phần lớn từ chi nhánh Göteborg chỉ cách hai cây số, phần còn lại từ trung tâm Jönköping. Xác nhận." |

## Cảnh 6: Đơn 4, PDF, review và plan (3:55–5:00)

| Thao tác | Lời thoại |
|---|---|
| Mở đơn **Unknown customer** còn lại, là PDF (số điện thoại `+45 31 24 56 78`). Chỉ *Original file* và *What the system read*, rồi ô **Customer name** trống. | "Đơn cuối cùng là PDF của anh Lars ở Copenhagen. Tên công ty bị bỏ trống, nên cũng phải nhập tay." |
| Bấm **Edit draft**. Gõ `Lars Byg ApS` vào ô **Customer**. | "Tôi bấm Edit draft và nhập tên khách." |
| Dòng 4 *Stålbjælke HEA 200*: tick "I have checked…". Dòng 5 *Skruer til gips, ca. 40 mm*: chỉ ô **Product** đang là `SCR-GIP-40` (mở danh sách để cho thấy có thể chọn sản phẩm khác trong cả catalog), giữ nguyên, tick "I have checked…". Bấm **Save draft**. | "Dầm thép ghép đúng, tôi đánh dấu đã kiểm. Dòng 5 khách ghi mơ hồ 'vít thạch cao, khoảng 40 li'. Hệ thống gợi ý vít thạch cao 3,9 nhân 40. Nếu sai, tôi chọn bất kỳ sản phẩm nào khác trong danh mục ngay tại đây. Gợi ý này đúng, nên tôi giữ và lưu nháp." |
| Bấm **Approve OCR result**, **Make plan**. Chỉ **3 shipment**. | "Duyệt xong, lên kế hoạch." |
| Shipment 1: chỉ lý do *Nearest branch with full stock: DK-BR-01 (9.5 km)*. | "Thạch cao, bông khoáng và vít lấy từ chi nhánh Sydhavn ở Đan Mạch, cách chín cây số rưỡi." |
| Shipment 2 và 3: chỉ nhãn **Cross-border** và **Crane needed**. | "Gỗ thông Thụy Điển và dầm HEA 200 không có ở kho Đan Mạch nào, nên được lấy từ trung tâm Jönköping bên Thụy Điển. Dầm nặng hơn hai trăm rưỡi ký mỗi cây, cần cẩu lên sàn, nên hệ thống tự xếp xe cẩu." |
| Chỉ **Expected (P50)** 10/11 và **Safe commitment (P90)** 12/11. | "Dự kiến giao ngày 10, mốc an toàn là 12, vẫn kịp ngày khách yêu cầu." |

## Cảnh 7: Đơn 4, PDF, đổi rules, plan lại, Confirm (5:00–6:05)

| Thao tác | Lời thoại |
|---|---|
| Vào **Rules**. | "Giả sử ban lãnh đạo quyết định: tạm dừng giao hàng xuyên biên giới." |
| Tắt **Allow cross-border delivery**, bấm **Save**. Chỉ thông báo *Rules saved (version …)*. | "Chỉ cần gạt một công tắc, lưu lại, có đánh số phiên bản, không cần lập trình viên, không cần triển khai lại." |
| Quay lại đơn PDF, bấm **Re-plan**. Chỉ khung *Some items are not fully in stock*. | "Lập lại kế hoạch: gỗ thông và dầm thép giờ thành thiếu hàng, kèm lý do cụ thể. Quy tắc đổi thì quyết định đổi theo." |
| Vào **Rules**, bật lại cross-border, **Save**. Quay lại đơn, **Re-plan**. | "Bật lại, kế hoạch đầy đủ quay trở lại. Ba đơn trước, đã xác nhận, vẫn giữ nguyên kế hoạch cũ, vì kế hoạch đã xác nhận được khóa theo phiên bản quy tắc lúc tạo." |
| Bấm **Confirm order**. Chỉ *Stock reserved: 5 lines. Plan and ETA are locked.* Kéo xuống **History**. | "Xác nhận đơn cuối. Hệ thống giữ hàng trong từng ERP và ghi lại lịch sử ai đã đọc, sửa, duyệt, lên kế hoạch và xác nhận." |
| *(Nếu ETA hiện `late`: tick *Confirm even though delivery is predicted after the requested date* rồi mới Confirm.)* | *("Nếu ngày giao có rủi ro trễ, nhân viên phải chủ động chấp nhận rủi ro, hoặc gọi cho khách và hứa theo mốc P90.")* |

## Cảnh 8: Kiểm tra tồn kho cho cả 4 đơn (6:05–6:50)

Mở **Stock**, dùng ô tìm kiếm, mở dòng từng kho. Số liệu dưới đây là **reserved** và **available** (trước → sau) tính trên DB trống.

| Tìm | Kho | Reserved | Available | Từ đơn |
|---|---|---|---|---|
| `Gipsplade standard 13mm` | DK-BR-02 | 5 → **65** | 67 → **7** | Email (60 tấm) |
| `Gipsplade standard 13mm` | DK-BR-01 | 6 → **46** | 96 → **56** | PDF (40 tấm) |
| `Brandgipsskiva` (hoặc `GYP-15-FIRE`) | SE-BR-01 | 18 → **58** | 149 → **109** | Ảnh (40 tấm) |
| `Träskruv` (hoặc `SCR-WOOD-580`) | SE-BR-02 | 15 → **35** | 135 → **115** | Excel (20 gói) |
| `Svensk furu` | SE-DC-01 | 45 → **105** | 3455 → **3395** | PDF (60 m) |
| `HEA 200` | SE-DC-01 | 45 → **49** | 805 → **801** | PDF (4 dầm) |

| Thao tác | Lời thoại |
|---|---|
| Tìm `Gipsplade standard 13mm`, mở hai kho DK-BR-02 và DK-BR-01. | "Quay về Stock. Tấm thạch cao 13 ly: đơn email lấy sáu mươi tấm ở kho DK-BR-02, giờ chỉ còn bảy tấm khả dụng, và đơn PDF lấy bốn mươi tấm ở kho DK-BR-01. Số 'reserved' tăng đúng bằng những gì mỗi đơn đã hứa." |
| Tìm `Brandgipsskiva` rồi `Träskruv`. | "Đơn ảnh giữ bốn mươi tấm thạch cao chống cháy ở Stockholm, đơn Excel giữ hai mươi gói vít gỗ ở Göteborg." |
| Tìm `Svensk furu` rồi `HEA 200`. | "Và gỗ thông Thụy Điển cùng bốn dầm thép của đơn cuối cũng đã được giữ ở Jönköping. Cả bốn đơn đều đã trừ vào tồn kho, nên không đơn nào khác có thể hứa cùng số hàng đó." |

## Cảnh 9: Kết (6:50–7:00)

| Thao tác | Lời thoại |
|---|---|
| Quay lại **Dashboard**. Chỉ ô *Confirmed* = 4. | "Bốn đơn, bốn định dạng, từ dễ đến khó, đều thành đơn đã xác nhận, giải thích được. AI lo việc đọc, con người đưa ra quyết định, và các ERP hiện có vẫn giữ nguyên. Đó là OneOrder. Cảm ơn mọi người đã xem." |

---

## Lưu ý khi quay

- **ETA phụ thuộc ngày quay.** Các ngày 10, 11, 12/11 trong lời thoại là kết quả chạy thử ngày 9/11. Nếu quay ngày khác, ngày sẽ dịch, và đơn có thể thành `at_risk` hoặc `late`. Hãy đọc ngày thật trên màn hình thay vì đọc theo kịch bản.
- **Số liệu tồn kho** lấy từ DB trống. Nếu bạn chạy thử mà không tắt và khởi động lại app, số sẽ lệch.
- **Sau khi bấm Save draft, một số dòng bị đòi kiểm tra lại**, kể cả dòng bạn chưa sửa (đơn Ảnh và đơn Excel, vì đơn vị "st" bị đổi thành "stk"). Vì vậy kịch bản bảo tick "I have checked…" ở cả 5 dòng ngay trong form. Đơn PDF chỉ cần tick 2 dòng. Nếu quên, nút Approve vẫn khóa và hiện số dòng còn lại cần kiểm.
- **Dòng index trong UI** đánh số từ 1: "dòng 3 của Excel" là *Regel C24*, "dòng 4" là *Träskruv*.
- **Nếu thiếu thời gian:** bỏ phần "Chỉ **Expected (P50)** / **Safe commitment (P90)**" ở đơn 1 và đơn 2 (chỉ giữ ở đơn 4), rồi rút gọn lời thoại phần plan của đơn Excel. Không bỏ cảnh đổi rules và cảnh tồn kho, đây là hai bằng chứng rõ nhất.
- Tôi chưa xem giao diện thật trên trình duyệt. Tên nút lấy từ file i18n tiếng Anh, nên hãy chạy thử một lượt để chắc chắn khớp.
