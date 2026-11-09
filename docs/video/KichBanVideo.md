# Kịch bản video demo OneOrder (7 phút)

Bộ test: [samples/video-demo/](../../samples/video-demo/README.md). Lời thoại viết bằng tiếng Anh cho khớp các tài liệu nộp khác; cột thao tác viết bằng tiếng Việt.

## Chuẩn bị trước khi quay

1. Ở nhánh `demo/video-recording`. Kiểm tra `data/rules.json` còn `"allow_cross_border": true`.
2. Khởi động bằng DB trống và inbox riêng:
   ```bash
   AI_MODE=demo FRESH=1 INBOX_DIR=samples/video-demo ./run-oneorder.sh start
   ```
   Phải truyền `AI_MODE=demo` trên dòng lệnh. Script không đọc `AI_MODE` trong `.env`, mà `.env` có API key, nên nếu thiếu biến này app sẽ chạy **live**.
3. Mở `http://localhost:5173`, chuyển giao diện sang **English**, phóng to trình duyệt khoảng 110–125% cho dễ đọc.
4. Mở sẵn thư mục `samples/video-demo/pdf/` trong file manager để kéo thả. Chép nội dung `samples/video-demo/emails/en_order.txt` vào clipboard.
5. **Chạy thử một lượt**, rồi tắt app (Ctrl-C) và khởi động lại bằng đúng lệnh trên để có DB sạch trước khi quay thật.
6. Sau khi quay xong: `git checkout data/rules.json`. Màn hình Rules lưu vào file này và tăng version mỗi lần bấm Save.

Ghi chú về chế độ demo: kết quả đọc PDF và ảnh là kết quả **Gemini thật đã ghi lại** (fixture), phát lại để video không phụ thuộc mạng hay quota. Badge góc trên hiện "AI: demo". Câu thoại ở cảnh 2 nói rõ điều này.

---

## Cảnh 1 — Giới thiệu và các tab (0:00–0:45)

| Thao tác | Lời thoại |
|---|---|
| Mở **Dashboard**. | "This is OneOrder, an orchestration layer that sits on top of the Danish, Swedish and Norwegian ERPs. It turns messy contractor orders into confirmed orders with a delivery date we can trust." |
| Rê chuột qua 4 ô đếm *To review / Ready to plan / To confirm / Confirmed*. | "The dashboard follows every order through four steps: review, plan, confirm, done." |
| Bấm **Orders**. | "Orders is where requests come in, by upload, pasted email or the shared inbox." |
| Bấm **Stock**. | "Stock shows one view across all three countries, read live from each national ERP." |
| Bấm **Rules**. | "And Rules holds the business rules for choosing warehouses and trucks. They live in configuration, not in code. We'll change one later." |

## Cảnh 2 — Nhập 4 loại đầu vào (0:45–2:00)

| Thao tác | Lời thoại |
|---|---|
| Vào **Orders**. Kéo `dk-nordhavn-materialeliste.pdf` vào ô *Upload an order*. Chờ "Order read". | "Lars, a site foreman in Copenhagen, sends a PDF material list. I just drop it in. The AI reads every line, the phone number, the delivery address and the requested date." |
| Trong **Sample inbox**, bấm *Import order* cho `se-handwritten-1.jpg`. | "Next, a photo of a handwritten Swedish note, with crossings-out." |
| Bấm *Import order* cho `se-goteborg-materiallista.xlsx`. | "A spreadsheet from a Swedish contractor." |
| Mở *Or paste the email text*, dán email, bấm **Read email**. | "And a plain email in English. Four formats, four languages, one queue." |
| Chỉ vào badge "AI: demo". | "For this recording we replay results that Gemini produced earlier, so the demo does not depend on the network. In live mode the same call goes to the model." |

## Cảnh 3 — Kiểm tra và sửa đơn (2:00–3:45)

| Thao tác | Lời thoại |
|---|---|
| Mở đơn **ảnh viết tay**. Chỉ vào 2 dòng có nhãn *check* (AI 72%, 70%) và ô số điện thoại trống. | "The system never trusts the AI blindly. Lines under 85% confidence are flagged, and this handwritten note had no phone number, so Approve stays locked until someone enters one." |
| Mở đơn **Excel**. Chỉ vào cảnh báo *quantity is missing* và dòng *golvmatta* bị match sai, ô tên khách trống. | "In the spreadsheet one row has no quantity, and the floor mat is not in our catalogue. Instead of guessing silently, the system marks the line for review." |
| Mở đơn **PDF**. Chỉ vào cột *Original file* bên cạnh *What the system read*. | "Back to Lars's order. On the left the original PDF, on the right what the system read, so checking takes seconds." |
| Chỉ vào ô **Customer name** trống và nút Approve bị khóa. | "The customer field on the form was left blank, so the name is required before approval." |
| Gõ **Lars Byg ApS**. | |
| Dòng 5 *Skruer til gips*: chỉ vào SKU `GYP-13-2400`, mở *Choose a product*, chọn **SCR-GIP-40**. | "Here's a real catch: 'screws for plasterboard' was matched to the plasterboard itself. I pick the right product, drywall screws 3.9 by 40." |
| Dòng 4 dầm HEA 200: tick xác nhận. | "The steel beam match is right, so I just confirm it." |
| Bấm **Approve OCR result**. | "Every edit is recorded. Now the order is ready to plan." |

## Cảnh 4 — Lên plan (3:45–4:40)

| Thao tác | Lời thoại |
|---|---|
| Chỉ vào *Deliver to*: hệ thống tự nhận công trường Nordhavn từ địa chỉ. Bấm **Make plan**. | "The delivery site is detected from the address." |
| Lướt qua **3 shipment**. | "OneOrder checks stock in all three ERPs and follows the rules: nearest branch first, then a domestic DC, then a DC abroad." |
| Shipment 1: chỉ vào lý do *Nearest branch with full stock: DK-BR-01 (9.5 km)*. | "Plasterboard, insulation and screws come from the Sydhavn branch, 9 kilometres away." |
| Shipment 2 và 3: chỉ vào nhãn **Cross-border** và **Crane needed**. | "The Swedish pine and the HEA 200 beams are not stocked anywhere in Denmark, so they come from our DC in Jönköping. The beams weigh a tonne and must be lifted onto the deck, so the system books a crane truck." |
| Chỉ vào **Expected (P50)** 10/11 và **Safe commitment (P90)** 12/11. Bấm *How is this predicted?*. | "For the date, P50 is the most likely day and P90 is the day we can safely promise. Both are inside Lars's requested date of the 12th, so the order is on time." |

## Cảnh 5 — Đổi rules (4:40–5:40)

| Thao tác | Lời thoại |
|---|---|
| Vào **Rules**. | "Now suppose management decides: no more cross-border deliveries for this market." |
| Tắt **Allow cross-border delivery**, bấm **Save**. Chỉ vào thông báo *Rules saved (version …)*. | "It's one switch, saved and versioned, with no developer and no redeploy." |
| Quay lại đơn PDF, bấm **Re-plan**. Chỉ vào khung *Some items are not fully in stock*. | "Re-plan, and the pine and the beams now show as shortages, with the reason. The rules change the decision, and the system explains why." |
| Vào **Rules**, bật lại cross-border, **Save**. Quay lại đơn, **Re-plan**. | "We switch it back, and the full plan returns." |

## Cảnh 6 — Duyệt plan (5:40–6:15)

| Thao tác | Lời thoại |
|---|---|
| Bấm **Confirm order**. Chỉ vào *Stock reserved: 5 lines. Plan and ETA are locked.* | "Confirming reserves the stock in each national ERP in one step and locks the plan and the date we promised." |
| Kéo xuống **History**. | "The history shows who read, edited, approved, planned and confirmed this order." |
| (Nếu ETA hiện *late*: tick *Confirm even though delivery is predicted after the requested date* rồi mới Confirm.) | ("If the date is at risk, the clerk must accept that risk explicitly, or call the customer with the P90 date instead.") |

## Cảnh 7 — Kiểm tra tồn kho (6:15–6:45)

| Thao tác | Lời thoại |
|---|---|
| Vào **Stock**, tìm `Svensk furu`. Mở dòng SE-DC-01. | "In Stock, the Swedish pine at Jönköping now shows 60 more metres reserved and 60 fewer available: 3,395 instead of 3,455." |
| Tìm `HEA 200`. | "The four beams are reserved too, so no other order can promise the same stock." |

## Cảnh 8 — Kết (6:45–7:00)

| Thao tác | Lời thoại |
|---|---|
| Quay lại **Dashboard** (đơn đã ở *Confirmed*). | "From a messy PDF to a confirmed, explainable order in a few minutes. The AI does the reading, people make the decisions, and the existing ERPs stay in place. That's OneOrder." |

---

## Nếu thiếu thời gian

- Cắt đầu tiên: đơn Excel ở cảnh 3 (chỉ nói một câu khi import).
- Cắt thứ hai: phần *How is this predicted?* ở cảnh 4.
- Không cắt cảnh 5 (đổi rules) và cảnh 7 (tồn kho): đây là hai bằng chứng rõ nhất.
