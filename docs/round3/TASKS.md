# Round 3: danh sách task

**Thuyết trình:** thứ Bảy 21/11/2026, 13:30–18:00, Netcompany, Opal Tower, 92 Nguyễn Hữu Cảnh. **Cả 3 người phải có mặt.**
**Hình thức:** 15 phút trình bày + 10 phút QnA. Không nộp gì online.
**Tài liệu định hướng:** [Định hướng Round 3 – OneOrder](https://claude.ai/artifact/D4UNGSi6FxSZaQBKMquqFz)

Đề Round 3 có hai thay đổi: **ngân sách bị cắt 30%** và **bắt buộc chuyển CRM của một nước từ Microsoft Dynamics 365 sang Salesforce**. Ban giám khảo muốn nghe: đề xuất thay đổi ra sao, MVP / user journey / system diagram điều chỉnh thế nào, và các trade-off, rủi ro, giả định.

Mức ưu tiên:

- **P0**: bắt buộc phải có cho buổi pitch.
- **P1**: demo, giúp bài thuyết phục hơn.
- **P2**: làm nếu còn thời gian.

Người phụ trách chỉ là gợi ý theo vai trò ở [PHANCONG.md](../../PHANCONG.md): Nghĩa làm backend/AI, Khang làm dữ liệu/mock/kiểm thử, Nhật làm frontend/tài liệu/sơ đồ.


| Thành viên | Mức độ | Task phụ trách chính |
| --- | --- | --- |
| **Nghĩa** | quyết định phạm vi, chi phí, tích hợp Salesforce ở backend | A2, B1 (nhân sự), B2, B3, C4, D1, D3, D4, D5, E1, H1 (duyệt), H3 (demo trực tiếp) |
| **Nhật** | nghiên cứu migration, giao diện, sơ đồ, slide | B1 (cloud, AI), C1, C2, C3, C5, D6, D7, E2, F2, G1, G2, H1, H2 |
| **Khang** | dữ liệu mẫu, bảng giá, test, chạy thử, hậu cần | B4, C6, D2, E3, F1, F3, G3, G4, H3 (video dự phòng), H4, I1, I2 |

---

## Lịch

| Ngày | Việc chính |
| --- | --- |
| Thứ Ba 17/11 | Chốt giả định (A1). Bắt đầu nghiên cứu chi phí (B) và migration (C). Tạo Salesforce Developer org (D1). |
| Thứ Tư 18/11 | Hoàn thành B và C. Code: CRM adapter, khớp khách hàng, đồng bộ khi Confirm (D, E). |
| Thứ Năm 19/11 | Hoàn thành code và test (D, E, F). Sửa System Context Diagram, User Journey (G). |
| Thứ Sáu 20/11 | Slide (H). Tập dượt ít nhất 2 lần, bấm giờ đúng 15 phút. Chạy thử demo trên máy dùng thuyết trình. |
| Thứ Bảy 21/11 | Tập dượt buổi sáng. Có mặt trước 13:30. |

---

## A. Chốt phạm vi và giả định (P0)

- [ ] **A1. Chốt các giả định** · cả nhóm · 17/11. Mỗi giả định phải ghi được lý do.
  - Nước dùng Dynamics 365. Đề không nói, tài liệu định hướng tạm chọn **Đan Mạch**.
  - "Migration" gồm những gì: chỉ chuyển dữ liệu và dùng cấu hình Salesforce chuẩn, hay làm lại cả quy trình bán hàng.
  - Ai trả tiền license Salesforce: ngân sách dự án hay ngân sách vận hành IT của nước đó.
  - Khung thời gian dự án giữ 12 tháng. Dynamics còn chạy được ít nhất 4 tháng.
  - Đơn giá nhân sự (đang tạm dùng €9.000 / người-tháng).
- [ ] **A2. Chốt MVP mới: giữ / điều chỉnh / hoãn / bỏ** · Nghĩa · 18/11. Dựa trên kết quả B, viết thành một bảng có cột lý do cho từng quyết định.

## B. Chi phí và cắt giảm 30% (P0)

- [ ] **B1. Ước tính chi phí triển khai theo đề xuất vòng 1 và vòng 2** · Nghĩa + Nhật · 18/11
  - Chia theo giai đoạn: pilot Thụy Điển, go-live SE + DK, mở rộng Na Uy.
  - **Nghĩa:** nhân sự (FTE × tháng), đào tạo, dự phòng.
  - **Nhật:** chi phí cloud tại EU (app, DB, giám sát, số môi trường), AI API theo số đơn/năm, API bản đồ / khoảng cách. Ghi nguồn giá cho từng con số.
  - Bản nháp hiện có: khoảng **€765k cho 12 tháng** (mục 4 tài liệu định hướng). Cần cả nhóm rà lại từng con số.
- [ ] **B2. Cộng chi phí CRM migration và tính khoảng thiếu** · Nghĩa · 18/11. Nhu cầu mới khoảng €868k, ngân sách còn khoảng €535k, nên phải cắt khoảng 38%, không phải 30%.
- [ ] **B3. Kịch bản cắt giảm** · Nghĩa · 18/11
  - Liệt kê các hạng mục bị cắt, hoãn hoặc làm gọn, kèm số tiền tiết kiệm của từng hạng mục.
  - Chuẩn bị thêm phương án nếu ngân sách bị cắt thêm 10%, hoặc nếu license Salesforce bị tính vào dự án.
- [ ] **B4. Biểu đồ cầu ngân sách (waterfall) cho slide** · Khang · 19/11. Đi từ €765k về khoảng €533k, lấy số từ B3. Có đường ngân sách €535k để người xem so sánh.

## C. Nghiên cứu chuyển Dynamics 365 sang Salesforce (P0)

Giả định chuyển cho **một nước**. OneOrder **không tích hợp với Dynamics 365**: Dynamics chỉ là nguồn dữ liệu cho một lần chuyển sang Salesforce.

- [ ] **C1. Chuyển dịch những gì** · Nhật · 18/11
  - Ánh xạ đối tượng: Account, Contact, Opportunity đang mở, lịch sử liên hệ 12–24 tháng gần nhất.
  - Ghi rõ phần không chuyển: plugin, workflow và báo cáo tùy biến của Dynamics; dữ liệu cũ hơn 24 tháng (để ở file lưu trữ chỉ đọc).
- [ ] **C2. Công cụ và định dạng dữ liệu** · Nhật · 18/11
  - Dynamics: đọc qua Dataverse Web API (OData v4, JSON), hoặc xuất ra Excel / CSV.
  - Salesforce: nạp bằng Bulk API 2.0 (CSV) hoặc Data Loader.
  - Ghi các giới hạn API của hai bên: Dataverse 6.000 request / 5 phút, Salesforce theo số license.
  - Kiểm lại các số liệu Salesforce trên trang tài liệu gốc. Trong tài liệu định hướng, các số này chưa xác minh được trên trang gốc.
- [ ] **C3. Lộ trình migration** · Nhật · 18/11. Các bước: khảo sát → ánh xạ → làm sạch (gộp khách trùng, chuẩn hóa số điện thoại) → chạy thử trên sandbox → chuyển hẳn (cut-over) → lưu trữ dữ liệu cũ rồi tắt Dynamics. Đặt các bước này lên timeline 12 tháng (tháng 1–4).
- [ ] **C4. Chi phí migration** · Nghĩa · 18/11. Ước tính nhân sự và thời gian.
- [ ] **C6. So sánh giá license Dynamics 365 và Salesforce** · Khang · 18/11. Lập bảng giá các gói (USD/EUR mỗi user mỗi tháng), tính chi phí một năm cho khoảng 50 user, và chênh lệch so với license Dynamics đang trả. Ghi link nguồn.
- [ ] **C5. (P2) Script demo migration nhỏ** · Nhật · 19/11. Lấy file mẫu xuất từ Dynamics, chuyển cột cho đúng định dạng Salesforce, rồi nạp vào Developer org bằng Bulk API. Dùng làm bằng chứng kỹ thuật khi bị hỏi trong QnA.

## D. Kết nối Salesforce cho OneOrder (P1)

- [ ] **D1. Tạo Salesforce Developer Edition org (miễn phí) và cấu hình truy cập API** · Nghĩa · 17/11
  - Tạo External Client App với OAuth client credentials.
  - Lưu key vào `.env`. Không commit key.
- [ ] **D2. Nạp dữ liệu khách mẫu vào Salesforce** · Khang · 18/11
  - Tạo Account và Contact cho các khách trong `samples/video-demo/`: Hoffmann Byg A/S, Skanska Sverige AB, Bygg Väst AB, Lars Byg ApS.
  - Thêm vài khách gần trùng (tên gần giống, cùng số điện thoại) để demo được việc khớp khách.
- [ ] **D3. CRM adapter** · Nghĩa · 18/11
  - Tạo interface `CustomerDirectory` với hai hàm: `find_customers(phone, name)` và `push_order(order)`.
  - Có hai chế độ, giống `AI_MODE`: `live` gọi Salesforce REST API, `mock` đọc file JSON để demo chạy được khi không có mạng.
  - Nước không có CRM dùng adapter "không CRM", giữ cách nhập tay như hiện tại.
- [ ] **D4. Đồng bộ khi Confirm và test trên Salesforce thật** · Nghĩa · 19/11
  - Sau khi giữ hàng trong ERP, ghi Order (hoặc Task) lên Salesforce, kèm ngày cam kết P90 và mã đơn OneOrder làm External ID để gửi lại không bị trùng.
  - Salesforce lỗi thì **không chặn Confirm**: xếp bản ghi vào hàng đợi, gửi lại sau và xử lý lỗi 429 / `Retry-After`.
  - Ghi audit log.
- [ ] **D5. Cấu hình CRM theo nước trong `rules.json`** · Nghĩa · 19/11. Ví dụ `"crm": {"DK": "salesforce", "SE": "none", "NO": "none"}`.
- [ ] **D6. Giao diện trạng thái đồng bộ CRM** · Nhật · 19/11
  - Trên trang đơn: badge "Synced to Salesforce" / "Pending sync" / "Sync failed", kèm nút "Retry sync".
  - Trong History: dòng ghi lại lần đồng bộ.
  - Trên Dashboard: số đơn đang chờ đồng bộ.
- [ ] **D7. Bật/tắt CRM theo nước trên màn hình Rules** · Nhật · 19/11. Dùng cấu hình ở D5 để demo được "đổi cấu hình, không cần sửa code".

## E. Gợi ý tên khách và số điện thoại ở bước Review (P1)

Không tự điền mù: hệ thống **gợi ý khách từ Salesforce, nhân viên chốt**. Cách làm giống bước khớp sản phẩm đang có.

- [ ] **E1. Backend tìm và gợi ý khách** · Nghĩa · 19/11
  - AI đọc được số điện thoại thì tìm theo số và gợi ý tên khách. AI đọc được tên thì tìm theo tên (fuzzy) và gợi ý số điện thoại.
  - Không tìm thấy thì gắn cờ "Customer not found in CRM", không tự tạo khách mới.
  - Thêm cột `crm_account_id` và `crm_contact_id` vào đơn hàng. Vẫn giữ chữ gốc AI đọc được để đối chiếu.
- [ ] **E2. Giao diện chọn khách** · Nhật · 19/11
  - Trong Review / Edit draft: hiện danh sách khách gợi ý (tên, số điện thoại, thành phố). Bấm chọn thì tự điền tên và số điện thoại.
  - Thêm nút "Use typed name" cho khách chưa có trong CRM.
- [ ] **E3. Test** · Khang · 19/11. Các trường hợp: khớp đúng một khách; nhiều khách gần trùng; không tìm thấy; CRM lỗi hoặc timeout; nước không có CRM.

## F. Dọn dẹp kỹ thuật trước demo (P1)

- [ ] **F1. Sửa 3 test trong `tests/test_confirm.py` đang đỏ vì ngày cứng `2026-11-10` đã qua** · Khang · 18/11. Cho test tính ngày theo hôm nay để CI trên `main` xanh lại.
- [ ] **F2. Cập nhật ngày giao trong mẫu demo** · Nhật · 19/11
  - Email và PDF trong `samples/video-demo/` đang có ngày 12–13/11, đã qua.
  - Đổi sang ngày sau 21/11, rồi ghi lại fixture bằng `scripts.record_fixture`.
  - Ảnh viết tay không đổi được ngày, nên ghi chú trong kịch bản là phải tick *Confirm even though…*.
- [ ] **F3. Chạy thử toàn bộ demo trên đúng máy sẽ dùng thuyết trình** · Khang · 20/11. Chạy cả hai chế độ: có mạng (`live`) và không mạng (`mock` / `demo`).

## G. Cập nhật tài liệu thiết kế (P0)

- [ ] **G1. System Context Diagram** · Nhật · 19/11. Sửa `docs/report/SystemContextDiagram.tex`:
  - Thêm Salesforce CRM, kết nối hai chiều với OneOrder (tra khách, ghi đơn).
  - Vẽ Dynamics 365 bằng nét đứt, chỉ có một mũi tên "migration một lần" sang Salesforce, không nối với OneOrder.
- [ ] **G2. User Journey** · Nhật · 19/11. Sửa `docs/report/UserJourney.tex`:
  - Bước Review thêm "Khách đã khớp trong Salesforce".
  - Bước Confirm thêm "Đã đồng bộ lên Salesforce".
  - Thêm persona nhân viên phụ trách khách hàng (account owner), người xem đơn dự án ngay trong Salesforce.
- [ ] **G3. Sơ đồ kiến trúc trước → sau** · Khang · 19/11. Lấy từ mục 3 tài liệu định hướng, tô màu phần mới.
- [ ] **G4. Timeline 12 tháng** · Khang · 19/11. Gồm: pilot SE, go-live SE, migration CRM DK, Salesforce adapter, go-live DK trên Salesforce. Na Uy chuyển sang năm 2.

## H. Slide và thuyết trình (P0)

- [ ] **H1. Dàn ý 15 phút** · Nhật (viết) + Nghĩa (duyệt) · 19/11
  1. Kết luận trước (1:30)
  2. Đánh giá khả thi và chi phí (2:30)
  3. MVP mới (3:00)
  4. Kiến trúc và user journey (3:00)
  5. Lộ trình và rủi ro (2:30)
  6. Giả định và bước tiếp theo (2:30)
- [ ] **H2. Làm slide** · Nhật (thiết kế) + cả nhóm (nội dung) · 20/11. Cần có các slide sau:
  - So sánh MVP trước và sau.
  - Biểu đồ cầu ngân sách.
  - Bảng giữ / hoãn / bỏ.
  - Sơ đồ kiến trúc mới.
  - User journey mới.
  - Timeline 12 tháng.
  - Bảng rủi ro.
  - Bảng giả định.
- [ ] **H3. (P1) Đoạn demo 1–2 phút** · Nghĩa (demo trực tiếp) + Khang (video dự phòng) · 20/11. Import đơn → hệ thống gợi ý khách từ Salesforce → Confirm → mở Salesforce thấy đơn mới. Nghĩa viết kịch bản demo; Khang quay sẵn video dự phòng theo kịch bản đó, phòng khi mạng lỗi.
- [ ] **H4. Chuẩn bị QnA** · Khang (tổng hợp) + cả nhóm (trả lời) · 20/11. Khang gom câu hỏi và câu trả lời vào một file, kèm số liệu để tra nhanh. Chia người trả lời theo chủ đề. Các câu nên chuẩn bị:
  - Sao không nối tạm OneOrder với Dynamics 365?
  - Sao hoãn Na Uy mà không bỏ ETA hay bỏ AI?
  - License Salesforce ai trả? Nếu bị tính vào dự án thì cắt gì tiếp?
  - Nếu ngân sách bị cắt thêm 10% thì sao?
  - Lúc chuyển hẳn sang Salesforce, bán hàng có bị gián đoạn không?
  - Dữ liệu cá nhân trong CRM xử lý theo GDPR thế nào?
  - Hệ thống gợi ý sai khách thì phát hiện bằng cách nào?
- [ ] **H5. Tập dượt** · cả nhóm · 20–21/11. Ít nhất 2 lần, bấm giờ đúng 15 phút, phân vai người nói. Thống nhất ai cầm máy demo.

## I. Hậu cần (P0)

- [ ] **I1.** Khang · 18/11 · Xác nhận cả 3 người dự được 13:30–18:00 ngày 21/11 tại Opal Tower.
- [ ] **I2.** Khang · 20/11 · Mang laptop và sạc, đầu chuyển HDMI. Chép slide và video demo dự phòng vào USB.

---

## Không làm trong Round 3

- Kết nối OneOrder với Dynamics 365, kể cả tạm thời.
- Làm lại quy trình bán hàng hoặc chuyển dữ liệu cũ hơn 24 tháng từ Dynamics.
- Cho hai nước còn lại dùng Salesforce.
- Tự động tạo khách mới trong Salesforce từ OneOrder.
- Trang theo dõi đơn cho nhà thầu, tối ưu tuyến đường. Các mục này đã nằm ngoài MVP từ vòng 2.
