# OneOrder · Phương án Round 3 (bản rà soát)

Ngày rà soát: **18/11/2026**. Người viết: Nghĩa, có AI hỗ trợ tổng hợp. Mọi số tiền tính bằng EUR, chưa gồm VAT. Danh sách nguồn ở [cuối tài liệu](#nguồn); nguồn nào là blog, trang của nhà cung cấp hay ước tính của nhóm đều được ghi rõ.

**Khuyến nghị:** giữ nguyên lõi MVP (AI đọc đơn, người duyệt, kế hoạch đa kho, ETA P50/P90, Confirm giữ kho). Năm đầu triển khai theo thứ tự: pilot Thụy Điển trước; ở Đan Mạch chuyển CRM sang Salesforce trước rồi mới đưa OneOrder vào; Na Uy sang năm 2. Phương án tốn **€533,0k**, nằm trong trần **€535,15k**, vẫn giữ khung 12 tháng.

So với bản trình bày hôm 17–18/11, phương án này sửa năm điểm:

1. **Ngân sách cloud và AI dùng số đo thật** (€4,95k/năm) thay cho số ước trước đó, cộng một khoản dự phòng vận hành ghi tên rõ.
2. **Đưa khoản chênh license Salesforce so với Dynamics (€10,9k/năm) vào ngân sách năm đầu**, thay vì để "chờ báo giá".
3. **Migration bắt đầu từ tuần 1 với Gate 0** (khảo sát 2 tuần). Salesforce chạy chính thức ở cuối T3, sớm hơn 1 tháng so với bản trước.
4. **Org Salesforce thiết kế sẵn cho cả Bắc Âu** ngay từ đầu, để Thụy Điển và Na Uy vào sau mà không phải làm migration lần hai.
5. **Có cổng quyết định (gate) và KPI cho từng giai đoạn**, và nêu rõ cái giá Company A phải trả khi hoãn Na Uy.

---

## 1. Đề Round 3 yêu cầu gì

| Thay đổi | Nội dung | Tác động |
| --- | --- | --- |
| Cắt ngân sách | Tổng ngân sách giảm **30%** | Kế hoạch 3 nước trong 12 tháng không còn vừa |
| CRM migration (bắt buộc) | Một nước dùng **Microsoft Dynamics 365**; hệ thống sắp ngừng, phải chuyển sang **Salesforce** trong dự án này | Thêm một hạng mục lớn trong khi tiền ít đi |

Ban giám khảo chấm theo 4 câu hỏi: **giải pháp cũ còn khả thi không**, **giữ gì và hoãn gì**, **đánh đổi và rủi ro là gì**, và **nên triển khai thế nào**. Phần trình bày phải cho thấy MVP, user journey và system diagram đã thay đổi ra sao. Được phép đặt giả định, nhưng phải nêu rõ và giải thích.

**Giả định nền:** nước dùng Dynamics 365 là **Đan Mạch (DK)**. Lý do: Dynamics có gốc từ Navision (Đan Mạch). Ngoài ra, bản on-premises Dynamics CRM 2016 đã hết hỗ trợ từ 13/01/2026 ([Microsoft Lifecycle](https://learn.microsoft.com/en-us/lifecycle/end-of-support/end-of-support-2026)), khớp với chữ "sắp ngừng hoạt động" trong đề.

## 2. Phương án Round 1–2 còn vừa ngân sách mới không?

**Không.** Các tính năng của MVP vẫn vừa, nhưng phạm vi triển khai 3 nước trong 12 tháng thì không.

| Chỉ số | Giá trị | Cách tính |
| --- | ---: | --- |
| Kế hoạch cũ: pilot SE → go-live SE + DK → NO, 12 tháng | **€764,5k** | Mục 4.2, theo lộ trình Round 1 |
| Trần sau khi cắt 30% | **€535,15k** | €764,5k × 70% |
| Nhu cầu mới nếu giữ kế hoạch cũ và thêm CRM | **€868,0k** | €764,5k + migration €81k + Salesforce adapter €22,5k |
| Khoảng thiếu | **€332,9k (38%)** | Lớn hơn mức 30% đề nêu, vì phải gánh thêm CRM |

Riêng lõi MVP (pilot SE và go-live SE) tốn €243k, chỉ bằng 45% trần. Phần đội chi phí lên là mở rộng sang nhiều nước, không phải bản thân sản phẩm.

## 3. Các phương án đã cân nhắc

| Phương án | Mô tả | Giá trị kinh doanh | Vừa ngân sách | Rủi ro | Kết luận |
| --- | --- | --- | --- | --- | --- |
| A. Cắt đều | Giữ 3 nước, mỗi hạng mục giảm khoảng 38% | Thấp: 3 nước đều làm dở | Vừa trên giấy | Cao | Loại |
| B. Nối tạm Dynamics | Nối OneOrder với Dynamics trước, chuyển Salesforce sau | Trung bình | Không: làm tích hợp 2 lần | Cao: Dynamics đã hết hỗ trợ | Loại |
| C. Cả 3 nước lên Salesforce | Chuẩn hóa CRM toàn tập đoàn ngay năm đầu | Cao về dài hạn | Không: thêm 2 migration và license | Rất cao | Loại năm 1 (vẫn chuẩn bị org sẵn) |
| D. Chỉ làm CRM | Hoãn OneOrder, chỉ làm migration DK | Thấp: mất mục tiêu gốc | Vừa | Thấp | Loại |
| **E. Tuần tự (chọn)** | Giữ lõi MVP; SE trước; DK làm CRM rồi OneOrder; NO năm 2 | **Cao:** 2/3 nước có OneOrder, CRM DK an toàn | **€533k** | Trung bình, có gate | **Khuyến nghị** |

Phương án E giữ được cả hai mục tiêu đề đặt ra (mục tiêu kinh doanh ban đầu và CRM). Nó không phải làm gì hai lần, và để lại một nền Salesforce dùng chung cho năm 2.

## 4. Cơ cấu ngân sách năm đầu

### 4.1 Đơn giá nhân sự

| Nhóm | Mức thị trường | Quy đổi EUR | Nguồn | Mức dùng |
| --- | --- | --- | --- | --- |
| Tư vấn IT Đan Mạch, senior | 700–1.100 DKK/giờ; ngày công 7.000–10.500 DKK | €94–147/giờ | consultant.dev, Nordic market 2026 và European rates Q2 2026 (blog thị trường, không công bố cách thu thập số liệu) | €120/giờ |
| Lập trình viên Việt Nam | Mid $28–45/giờ; senior $40–70/giờ | €25–41 và €36–64/giờ | Incorp Vietnam 2026 (trang của công ty outsourcing) | €45/giờ |
| Tỷ giá | 1 EUR = 7,46038 DKK (tỷ giá trung tâm ERM II); 1 EUR = 1,0989 USD (ECB, 17/11/2026) | | Danmarks Nationalbank; ECB | |

- Đội trộn **1 người Bắc Âu với 3 người Việt Nam** (trưởng nhóm, kiến trúc, BA ở Bắc Âu; delivery ở Việt Nam). Bình quân (120 + 3 × 45) / 4 = **€63,75/giờ**. Nhân 140 giờ tính phí mỗi tháng (giả định khoảng 20 ngày × 7 giờ) ra **€8.925/người-tháng**, làm tròn **€9.000/PM**.
- Không tính thời gian nhân viên Company A tham gia (key user, chủ dữ liệu, admin Dynamics). Phần này cần Company A tự bố trí người.

### 4.2 Bảng ngân sách

Kế hoạch cũ (trước Round 3):

| Hạng mục | Thời gian | PM | Chi phí |
| --- | --- | ---: | ---: |
| Pilot Thụy Điển (5 chi nhánh + 1 DC), 7,5 FTE | T0–T3 | 22,5 | €202,5k |
| Go-live SE + mở rộng DK, 4,5 FTE | T4–T9 | 27 | €243k |
| Mở rộng Na Uy, gồm adapter cho các thương hiệu mua lại, 3 FTE | T7–T12 | 18 | €162k |
| Cloud (ước lượng cũ) | 12 tháng | | €18k |
| AI và bản đồ (ước lượng cũ) | 12 tháng | | €12k |
| Đào tạo và quản lý thay đổi, 3 nước | | | €45k |
| Dự phòng (12%) | | | €82k |
| **Tổng** | | **67,5** | **€764,5k** |

Phương án Round 3 (đề xuất):

| Hạng mục | Thời gian | PM | Chi phí | Căn cứ |
| --- | --- | ---: | ---: | --- |
| Pilot Thụy Điển, thu gọn còn 6 FTE (dùng lại code MVP, QA kiêm nhiệm) | T0–T3 | 18 | €162,0k | Đơn giá 4.1 |
| Go-live Thụy Điển, 3 FTE | T3–T6 | 9 | €81,0k | Đơn giá 4.1 |
| Migration CRM Đan Mạch, khoảng 2,5 FTE (mục 9) | T0–T4 (18 tuần) | 9 | €81,0k | Kế hoạch tuần ở mục 9 |
| Salesforce adapter: đưa lên production, bảo mật, vận hành (code đã chạy được với Salesforce org thật) | T3–T5 | 2,5 | €22,5k | PR #36, #37 |
| Go-live OneOrder ở DK trên Salesforce, khoảng 1,7 FTE, chia 2 đợt | T6–T12 | 10 | €90,0k | Đơn giá 4.1 |
| **Cộng nhân sự** | | **48,5** | **€436,5k** | |
| Cloud Azure North Europe, production + staging | 12 tháng | | €4,15k | Mục 5 (Azure Retail Prices) |
| AI (Gemini Flash-Lite) và bản đồ, mức trần 100.000 đơn/năm | 12 tháng | | €0,80k | Mục 5 |
| Dự phòng vận hành (HA, egress, tải tăng) | | | €5,00k | Gấp đôi phần cloud và AI đo được |
| Chênh lệch license Salesforce so với Dynamics, 50 user | 12 tháng | | €10,92k | Mục 4.4 |
| Đào tạo theo mô hình train-the-trainer, SE + DK | | | €25,00k | Giả định của nhóm |
| Dự phòng dự án (10,5%) | | | €50,63k | Mức thường gặp 5–15% (Smartsheet) |
| **Tổng** | **12 tháng** | | **€533,0k** | **Dư €2,15k so với trần** |

Dự phòng dự án được tính trên phần dư còn lại, ra 10,5% của €482,4k. Tỷ lệ này nằm giữa khoảng 5–15% mà nguồn tham khảo nêu. Vì migration có rủi ro dữ liệu, dự phòng gắn với danh sách rủi ro ở mục 11. Mọi khoản chi từ dự phòng đều phải qua gate.

### 4.3 Cầu ngân sách: từ €764,5k xuống €533,0k

| Bước | Thay đổi | Lũy kế |
| --- | ---: | ---: |
| Kế hoạch cũ | | €764,5k |
| Hoãn Na Uy sang năm 2 | −€162,0k | €602,5k |
| Tách giai đoạn 2: go-live SE nhỏ hơn, DK đi sau Salesforce | −€72,0k | €530,5k |
| Thu gọn pilot SE (7,5 → 6 FTE) | −€40,5k | €490,0k |
| Cloud, AI, đào tạo về số thật (kể cả dự phòng vận hành và chênh lệch license) | −€29,1k | €460,9k |
| Dự phòng 12% → 10,5% | −€31,4k | €429,5k |
| Thêm: migration CRM DK | +€81,0k | €510,5k |
| Thêm: Salesforce adapter | +€22,5k | **€533,0k** |

Các khoản cắt và hoãn giải phóng €335k, đủ trả €103,5k cho phần CRM bắt buộc. Riêng dòng cloud/AI/đào tạo: các khoản cũ €75k (€18k + €12k + €45k) giờ còn €45,9k (€4,15k + €0,80k + €5,00k + €10,92k + €25,00k).

### 4.4 License Salesforce

| Phương án (50 user, 12 tháng, giá niêm yết) | USD/user/tháng | EUR/năm | So với Dynamics Enterprise (€57,33k) | Ghi chú |
| --- | ---: | ---: | ---: | --- |
| Dynamics 365 Sales Enterprise (đang dùng) | 105 | €57,33k | | Microsoft |
| Salesforce Pro Suite | 100 | €54,60k | −€2,73k | **Không có API**, nên OneOrder không kết nối được |
| **Salesforce Pro Suite + Web Services API** | 125 | **€68,25k** | **+€10,92k** | Mức tối thiểu để OneOrder chạy. Chạy thử migration trên Developer org. |
| Salesforce Core | 195 | €106,47k | +€49,14k | Có 1 Partial Sandbox. Chỉ nên chọn nếu Company A cần sandbox hoặc tự động hóa. |

Nguồn: trang giá Salesforce Sales Cloud và tài liệu add-on (add-on API $25/user/tháng chỉ áp cho Pro Suite; Core có "1 Partial Sandbox included per org"), trang giá Dynamics 365. Đã tra ngày 17–18/11/2026 ([docs/round3/license-pricing.md](license-pricing.md)).

- **Khuyến nghị:** dùng Pro Suite + API. **€57,33k vẫn do ngân sách vận hành IT của DK trả**, vì đó là tiền license Dynamics đang trả. **Riêng phần chênh €10,92k đưa vào ngân sách dự án năm đầu**, để tích hợp OneOrder không phụ thuộc vào một khoản tiền chưa ai duyệt.
- **Nếu Company A buộc cả license nằm trong €535k:** cần thêm €57,33k (license tương đương Dynamics), trừ €2,15k còn dư thì thiếu khoảng **€55k**. Cách bù: chỉ mua license cho người bán hàng thật sự dùng (30 user giảm khoảng €27k), hoặc dời đợt 2 go-live DK sang năm 2 (khoảng €45k).

### 4.5 Kịch bản nhạy

| Nếu… | Hệ quả | Cách xử lý |
| --- | --- | --- |
| Ngân sách bị cắt thêm 10% (trần khoảng €481k) | Thiếu khoảng €52k | Dời go-live DK sang năm 2 (−€90k). Giữ CRM vì đây là việc bắt buộc. |
| Gate 0 phát hiện Dynamics có nhiều tùy biến | Migration có thể lên mức tham chiếu thị trường ($250–750k, mục 9.5) | Giữ cách "chuyển gọn" (lift-and-shift, bỏ tùy biến). Phần dựng lại quy trình tách thành dự án riêng do sales DK tài trợ. |
| Dynamics tắt sớm hơn T3 | Mất dữ liệu nếu chưa xuất | Xuất snapshot đầy đủ ngay tuần 1 (mục 9) |
| Pilot SE vượt chi | Lấn sang ngân sách DK | Gate 1 (T3): tối đa 30% dự phòng cho SE |

## 5. Cloud và AI trong cấu hình pilot

Số đo theo đơn giá công khai ngày 18/11/2026, chi tiết ở [docs/round3/cost-infra.md](cost-infra.md):

| Khoản | Cấu hình | €/tháng | €/năm | Nguồn |
| --- | --- | ---: | ---: | --- |
| Azure Container Apps | Production 1 vCPU / 2 GiB chạy 24/7; staging 0,5 vCPU / 1 GiB chạy 160 giờ/tháng | 81,64 | 979,7 | Azure Retail Prices API, Container Apps pricing |
| PostgreSQL Flexible Server B2ms | Production 64 GB + staging 32 GB | 199,63 | 2.395,6 | PostgreSQL pricing |
| Blob Storage Hot LRS | 110 GB, lưu file đơn gốc | 2,49 | 29,9 | Blob pricing |
| Azure Monitor / Log Analytics | 25 GB/tháng | 61,94 | 743,3 | Monitor pricing |
| **Cộng cloud** | North Europe, 2 môi trường | **345,71** | **4.148,5** | |
| AI Gemini 3.5 Flash-Lite | 3.000 token vào + 1.500 token ra mỗi đơn, 100.000 đơn/năm | | 423,2 | Gemini API pricing ($0,30 / $2,50 mỗi triệu token) |
| Bản đồ (Route Matrix) | 2 phần tử/đơn, 10.000 phần tử miễn phí mỗi tháng | | 364,0 | Google Maps pricing |
| **Cộng cloud + AI** | | | **€4.935,7** | |

- **Kết luận:** chi phí vận hành thật khoảng **€5k/năm**, bằng 0,9% ngân sách. Cắt AI không tiết kiệm được gì đáng kể nhưng mất đi giá trị cốt lõi. Vì vậy AI được giữ.
- **So với dự toán cũ €30k:** bản đề xuất ghi số thật, cộng €5k dự phòng vận hành (HA đa vùng, egress, tải tăng). Khoản còn lại dùng trả chênh lệch license (€10,92k) và nâng dự phòng dự án.
- **Lựa chọn vùng:** Sweden Central rẻ hơn khoảng €944/năm và gần pilot hơn. Giữ North Europe làm mặc định cho đến khi Company A chốt yêu cầu về nơi lưu dữ liệu.

## 6. MVP trước và sau khi đổi đề bài

| Khía cạnh | Round 2 (trước) | Round 3 (sau) |
| --- | --- | --- |
| Phạm vi năm 1 | SE, DK, NO | SE và DK. **NO sang năm 2**: ERP Na Uy chưa nối, tồn kho NO chưa dùng để lập kế hoạch giao hàng. |
| Luồng đơn | Đọc đơn → Review → Plan/ETA → Confirm | Giữ nguyên. Thêm **chọn khách từ CRM** ở Review và **đồng bộ đơn lên CRM** sau Confirm, chỉ ở DK. |
| Khách hàng | Nhập tay tên và số điện thoại | Ở DK: gợi ý khách từ Salesforce (khớp theo số điện thoại hoặc tên), người chốt. SE: vẫn nhập tay. |
| Tích hợp | ERP DK/SE/NO (mock) + AI | ERP DK/SE + AI + **Salesforce (DK)**. Dynamics chỉ là nguồn migration một lần. |
| Độ tin cậy tích hợp | Gọi ERP đồng bộ | CRM lỗi không chặn Confirm: hàng đợi, tự thử lại 3 lần, có nút Retry. |
| Pilot | 7,5 FTE, 5 chi nhánh + 1 DC | 6 FTE, cùng phạm vi, có KPI và Gate 1 |

Đã chứng minh được trong code (merge ngày 18/11): gợi ý khách và ghi Order đã chạy với Salesforce Developer org thật. Kết quả: 33/33 ca khớp khách đạt, ghi Order hai lần không tạo bản ghi trùng.

## 7. Giữ, hoãn và bỏ

| Quyết định | Hạng mục | Lý do |
| --- | --- | --- |
| **Giữ** | AI đọc đơn 4 định dạng; người duyệt dòng có độ tin cậy dưới 85%; audit log | Giá trị cốt lõi; AI chỉ tốn khoảng €0,4k/năm |
| **Giữ** | Tồn kho chung, kế hoạch theo rules, ETA P50/P90, Confirm giữ kho | Giải quyết vấn đề giao hàng của SE; đã có trong MVP |
| **Thêm** | Migration CRM DK; chọn khách và đồng bộ đơn với Salesforce | Yêu cầu bắt buộc |
| **Điều chỉnh** | Pilot SE gọn hơn; go-live DK chia 2 đợt sau khi Salesforce đã chạy | Không phải tích hợp hai lần; có thời gian ổn định |
| **Hoãn (năm 2)** | Triển khai Na Uy: ERP NO và các thương hiệu mua lại | Khoản lớn nhất tách được (€162k) |
| **Hoãn (năm 2)** | Trang theo dõi đơn cho nhà thầu, cảnh báo trễ chủ động, tối ưu tuyến | Ngoài MVP từ Round 2 |
| **Bỏ** | Mọi kết nối OneOrder với Dynamics; dựng lại plugin, workflow, báo cáo Dynamics; chuyển lịch sử quá 24 tháng | Hệ thống sắp tắt; lịch sử cũ lưu chỉ đọc |

## 8. Thay đổi ở User Journey và System Context Diagram

Đã cập nhật [User Journey.pdf](../report/User%20Journey.pdf) và [System Context Diagram.pdf](../report/System%20Context%20Diagram.pdf).

**User Journey**
- **Kịch bản khớp với demo:** Anna (sales desk DK) nhận email của Mette Hoffmann (Hoffmann Byg A/S), giao tới Havnegade 45, Odense.
- **Bước 3 (Review) có thêm việc chọn khách từ Salesforce.** Nếu nhiều khách dùng chung số, hệ thống cảnh báo để Anna kiểm tra kỹ.
- **Bước 6 (Confirm):** đơn được giữ kho trước, rồi mới ghi lên Salesforce.
- **Persona mới:** Freja, account owner, xem đơn ngay trong Salesforce.
- **Nhánh mới:** khi CRM lỗi, đơn hiện *Pending sync* rồi tự đồng bộ lại; khi đơn ở SE (không có CRM), Anna nhập tay khách như cũ.
- **Bảng "Thay đổi so với Round 2".** Toàn bộ văn bản thống nhất bằng tiếng Anh.

**System Context Diagram**
- **Thêm Salesforce CRM (DK, org dùng chung Bắc Âu)**, kết nối hai chiều: tra khách ở Review, ghi đơn sau Confirm.
- **Dynamics 365 vẽ nét đứt,** chỉ có đường migration một lần sang Salesforce, không nối với OneOrder.
- **ERP Na Uy đánh dấu "năm 2".**
- **Bên trong OneOrder có thêm:** khớp khách hàng, CRM adapter, hàng đợi đồng bộ và worker thử lại.

## 9. Migration Dynamics 365 → Salesforce

### 9.1 Phạm vi

| Chuyển | Không chuyển |
| --- | --- |
| Account, Contact (kèm owner và quan hệ cha-con) | Plugin, workflow, báo cáo tùy biến. Chỉ kiểm kê; sales DK chọn cái nào cần dựng lại thành dự án riêng. |
| Opportunity đang mở | Opportunity đã đóng: lưu chỉ đọc |
| Hoạt động 24 tháng gần nhất: cuộc gọi, email, công việc, lịch hẹn → Task/Event | Hoạt động cũ hơn 24 tháng: lưu chỉ đọc |
| Mã gốc của Dynamics vào `Legacy_*__c` (External ID) | |

Ánh xạ trường chi tiết: [docs/round3/crm-migration.md](crm-migration.md), mục C1.

### 9.2 Công cụ

| Bước | Công cụ | Định dạng |
| --- | --- | --- |
| Xuất từ Dynamics | Dataverse Web API (OData v4); Export to Excel để rà mẫu | JSON, rồi CSV |
| Làm sạch, gộp trùng | Script của nhóm. Chuẩn hóa số điện thoại theo quy tắc OneOrder; gộp phải có sales DK duyệt. | CSV |
| Nạp vào Salesforce | Data Loader (miễn phí) chạy Bulk API 2.0. Data Import Wizard cho lượt thử nhỏ. | CSV |
| Đối soát | Đếm số lượng; so mẫu theo `Legacy_*__c` | Báo cáo |

Giới hạn cần tính: Dataverse cho 6.000 request mỗi 5 phút cho mỗi user, vượt thì trả 429 kèm `Retry-After`. Salesforce tính hạn mức API theo org trong 24 giờ; Developer Edition có 15.000 request/ngày.

### 9.3 Lịch 18 tuần (T0–T4)

| Tuần | Giai đoạn | Việc chính | Đầu ra | Cổng |
| --- | --- | --- | --- | --- |
| 1–2 | **Gate 0: khảo sát** | Kiểm kê bảng, số bản ghi, tùy biến, tích hợp đang nối; chốt ngày tắt Dynamics; **xuất snapshot đầy đủ ngay tuần 1** | Phạm vi và ước tính chốt; danh sách tùy biến | **Gate 0:** cách chuyển gọn có vừa €81k không? |
| 3–6 | Thiết kế, cấu hình org | Org dùng chung Bắc Âu: trường `Country`, record type theo nước, role và owner; tạo `Legacy_*__c` và `OneOrder_Id__c`; workshop ánh xạ với sales DK | Bảng ánh xạ đã duyệt; org cấu hình xong | |
| 5–9 | Xuất và làm sạch | Trích xuất qua Web API; chuẩn hóa số điện thoại; danh sách nghi trùng; ánh xạ owner | CSV sạch; bảng ID gộp | |
| 8–11 | Chạy thử lần 1 | Nạp vào org thử; đối soát số lượng, quan hệ Contact–Account, owner; sửa lỗi | Báo cáo lỗi lần 1 | |
| 11–13 | Chạy thử lần 2 và UAT | Nạp đủ khối lượng; 5–8 key user của sales DK kiểm tra; đào tạo người hướng dẫn nội bộ | Runbook cut-over; biên bản UAT | |
| 14 | Diễn tập cut-over | Chạy thử runbook có bấm giờ | | **Gate 2:** go / no-go |
| 15 | **Cut-over** (cuối tuần) | Thứ Sáu 18:00 khóa ghi Dynamics → nạp phần thay đổi cuối → đối soát → thứ Hai mở Salesforce | Salesforce DK chạy chính thức (**cuối T3**) | |
| 16–18 | Hỗ trợ sau go-live, lưu trữ | Hỗ trợ người dùng; lưu trữ chỉ đọc (kèm checksum); biên bản tắt Dynamics | Dynamics tắt (**T4**) | |

**Đội** (khoảng 9 PM):
- Trưởng nhóm migration (Bắc Âu, 50%).
- Tư vấn hoặc admin Salesforce (100%).
- Kỹ sư dữ liệu (Việt Nam, 100%).
- Sau go-live giảm còn 1 người.

**Company A cần bố trí:** admin Dynamics, chủ dữ liệu DK, 5–8 key user.

### 9.4 Tiêu chí go/no-go (Gate 2) và quay lui

- **Go khi:**
  - Số lượng chênh lệch ≤ 0,5%, và mọi chênh lệch đều có lý do.
  - 100% Contact có Account đúng; 100% Opportunity đang mở có owner đang hoạt động.
  - Key user ký UAT; runbook diễn tập trong cửa sổ 48 giờ.
- **Quay lui:** nếu đến Chủ nhật 18:00 vẫn chưa đạt, mở lại quyền ghi trên Dynamics, ghi lại các đơn nhận trong cửa sổ để đối soát, và hẹn lại cut-over sau 2 tuần.

### 9.5 Chi phí so với thị trường

| Nguồn | Mức tham chiếu | So với phương án |
| --- | --- | --- |
| Folio3 (đơn vị triển khai) | Doanh nghiệp vừa: $250–750k, 16–24 tuần, gồm cấu hình Salesforce, dựng lại tích hợp, đào tạo | Đó là migration toàn phần. Phương án Round 3 chỉ "chuyển gọn": không dựng lại tùy biến, chỉ một tích hợp (OneOrder, đã tính riêng €22,5k). |
| Veelead (đơn vị triển khai, chiều ngược lại) | Dưới 50 user: 4–6 tuần; 50–200 user: 8–12 tuần | Phần chuyển dữ liệu của phương án là khoảng 11 tuần (tuần 3–13), khớp mức 50–200 user |

**Kết luận:** €81k đủ cho cách chuyển gọn với khoảng 50 user và đơn giá trộn. Rủi ro lớn nhất là khối lượng tùy biến, nên Gate 0 phải đi trước mọi cam kết khác.

## 10. Lộ trình 12 tháng

| Tháng | Thụy Điển | Đan Mạch: CRM | Đan Mạch: OneOrder | Na Uy |
| --- | --- | --- | --- | --- |
| T0 | Khởi động pilot (5 chi nhánh + 1 DC) | **Gate 0** (tuần 1–2), snapshot | | |
| T1–T2 | Pilot chạy, đo KPI | Thiết kế, làm sạch, chạy thử | | |
| T3 | **Gate 1:** KPI pilot → quyết định go-live | Cut-over cuối T3 (**Gate 2**) | Đưa Salesforce adapter lên production | |
| T4–T5 | Go-live SE toàn quốc | Hỗ trợ sau go-live; tắt Dynamics (T4) | Adapter lên production | |
| T6 | Ổn định SE | | **Gate 3:** sẵn sàng → đợt 1 (2–3 chi nhánh) | |
| T7–T12 | Vận hành | | Đợt 2 (các chi nhánh còn lại) | Khảo sát nếu dự phòng chưa dùng (tùy chọn, T10) |
| Năm 2 | | Salesforce sẵn sàng cho SE/NO (org dùng chung) | | Triển khai NO |

**KPI cho Gate 1**, giả thuyết của nhóm từ Round 1, đo so với baseline của pilot:
- tỷ lệ giao đúng hạn và đủ hàng tăng 15 điểm phần trăm;
- thời gian nhập đơn thủ công giảm 50%;
- 100% đơn có ngày P90 khi Confirm.

## 11. Đánh đổi, giới hạn và rủi ro

**Đánh đổi:** cái Company A chấp nhận mất.

| Đánh đổi | Hệ quả kinh doanh |
| --- | --- |
| Na Uy chờ thêm khoảng 12 tháng | Vấn đề vận hành cửa hàng ở NO chưa được giải quyết; tồn kho NO chưa dùng cho giao hàng xuyên biên giới năm đầu |
| Go-live DK chỉ bắt đầu từ T6 | Đan Mạch (nơi đau nhất về quy trình thủ công) có OneOrder muộn hơn kế hoạch cũ 2 tháng |
| Dự phòng 10,5% thay vì 12% | Ít đệm hơn, bù lại bằng các gate |
| Chuyển CRM gọn | Quy trình bán hàng tùy biến trên Dynamics không được dựng lại ngay |

**Giới hạn của phương án**
- Đơn giá và số liệu thị trường lấy từ blog và trang của nhà cung cấp, chưa phải báo giá thật.
- KPI là giả thuyết, cần baseline thật.
- Giá license là giá niêm yết, chưa có chiết khấu.
- Số user (50) và khối lượng dữ liệu Dynamics là giả định.

**Rủi ro**

| Rủi ro | Khả năng | Tác động | Giảm thiểu | Người quyết định |
| --- | --- | --- | --- | --- |
| Tùy biến Dynamics nhiều hơn dự kiến | Trung bình | Cao | Gate 0; chuyển gọn; tách phần dựng lại | Ban dự án + sales DK |
| Dữ liệu bẩn, gộp nhầm khách | Cao | Trung bình | 2 lần chạy thử; gộp phải có người duyệt; giữ ID gốc | Chủ dữ liệu DK |
| Dynamics tắt sớm | Thấp | Cao | Snapshot tuần 1, thử đọc lại | IT DK |
| Người dùng DK mệt vì hai thay đổi liên tiếp | Trung bình | Trung bình | Salesforce live cuối T3, OneOrder từ T6: cách nhau 3 tháng; dùng chung super-user | Trưởng nhóm sales DK |
| Edition Salesforce thiếu API hoặc sandbox | Trung bình | Cao | Chốt Pro Suite + API ở Gate 0; nếu cần Core thì xin ngân sách vận hành | IT DK |
| CRM lỗi sau Confirm | Thấp | Thấp | Hàng đợi, tự thử lại, Retry (đã test) | Đội vận hành OneOrder |
| Pilot SE vượt chi | Trung bình | Trung bình | Gate 1; trần dự phòng cho SE | Ban dự án |

## 12. Khuyến nghị triển khai cuối cùng

1. **Duyệt phương án E** với €533k, 12 tháng, 4 gate (Gate 0 tuần 2, Gate 1 T3, Gate 2 tuần 14, Gate 3 T6).
2. **Tuần 1:** khởi động pilot SE, và cùng lúc làm Gate 0 cho CRM DK, xuất snapshot Dynamics.
3. **Chọn Salesforce Pro Suite + API.** License tương đương Dynamics do ngân sách vận hành DK trả; phần chênh €10,9k năm 1 do dự án trả.
4. **Thiết kế Salesforce dùng chung cho Bắc Âu** ngay từ đầu, để năm 2 đưa SE/NO vào mà không phải migration lần hai.
5. **OneOrder vào DK sau khi Salesforce đã chạy ổn định** (từ T6, chia 2 đợt), không bao giờ nối với Dynamics.
6. **Na Uy:** giữ hồ sơ thiết kế adapter; nếu dự phòng chưa dùng thì khảo sát vào T10 để khởi động năm 2 sớm.

## 13. Nhận xét bộ slide Round 3 (bản ngày 18/11) và những gì đã sửa

| Vấn đề trong bản cũ | Ảnh hưởng | Đã sửa |
| --- | --- | --- |
| Không có slide trả lời câu hỏi đầu tiên của đề: "giải pháp cũ còn khả thi không" | Thiếu bước lập luận "vì sao phải đổi" | Thêm slide khả thi: €764,5k so với €535k, khoảng thiếu 38% |
| Không có phương án so sánh | Giám khảo không thấy tư duy tư vấn | Thêm slide 5 phương án A–E |
| Slide 4 so số đo thật (€4k, €0,8k) với "dự toán €18k, €12k" của kế hoạch cũ, trong khi biểu đồ cầu đã dùng số mới | Hai slide mâu thuẫn nhau | Một bảng ngân sách thống nhất; cloud/AI dùng số thật |
| License để "chờ báo giá" | Lỗ hổng lớn nhất khi bị hỏi | Đưa ra bảng license; chênh €10,9k đã có trong ngân sách |
| Biểu đồ, kiến trúc, timeline là ảnh chụp, chữ rất nhỏ | Không đọc được khi chiếu | Vẽ lại bằng chart và shape của PowerPoint |
| Không có slide "đánh đổi" riêng, chỉ có rủi ro | Thiếu ý thứ ba của đề | Thêm bảng đánh đổi và giới hạn |
| Hành trình chỉ cho thấy bản "sau" | Đề hỏi "đã điều chỉnh ra sao" | Đánh dấu rõ các điểm mới ở user journey và sơ đồ hệ thống |
| Lộ trình migration chỉ có 6 bước, không có tuần và gate | Không thấy được tiến độ | Lịch 18 tuần, Gate 0/2, tiêu chí go/no-go |
| Câu "Giữ cam kết 12 tháng cho SE và DK" ở slide 1 nhưng thiếu khuyến nghị cuối cùng | Kết thúc yếu | Slide khuyến nghị cuối cùng với 6 quyết định |

Điểm mạnh giữ lại: giao diện thống nhất (navy, cam, nền giấy), mở đầu bằng kết luận, ví dụ Hoffmann xuyên suốt, slide "Khi Salesforce không phản hồi".

## 14. Giả định cần Company A xác nhận

| Giả định | Nếu sai |
| --- | --- |
| DK là nước dùng Dynamics 365, đang chạy bản cũ hết hỗ trợ | Đổi thứ tự: nếu là SE thì migration chạy cùng pilot; nếu là NO thì migration NO là việc riêng năm 1 |
| Khoảng 50 user Salesforce, ít tùy biến | Gate 0 điều chỉnh; xem mục 4.5 |
| License tương đương Dynamics do ngân sách vận hành trả | Xem mục 4.4 |
| Khung 12 tháng không đổi | |
| Company A bố trí key user, admin Dynamics, chủ dữ liệu | Migration trễ, chi phí tăng |

## Nguồn

Ngày tra cứu 17–18/11/2026, trừ khi ghi khác.

**Giá và kỹ thuật (nguồn chính thức)**
- Microsoft Lifecycle, sản phẩm hết hỗ trợ năm 2026: https://learn.microsoft.com/en-us/lifecycle/end-of-support/end-of-support-2026
- Microsoft, giá Dynamics 365 Sales: https://www.microsoft.com/en-us/dynamics-365/products/sales/pricing
- Salesforce, giá Sales Cloud (các gói, add-on API, sandbox): https://www.salesforce.com/sales/pricing/
- Salesforce, tài liệu add-on (Web Services API): https://www.salesforce.com/en-us/wp-content/uploads/sites/4/documents/pricing/all-add-ons.pdf
- Microsoft Learn, Dataverse Web API: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/overview
- Microsoft Learn, Dataverse service protection API limits: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/api-limits
- Azure Retail Prices API: https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
- Azure Pricing Calculator: https://azure.microsoft.com/en-us/pricing/calculator/
- Gemini API pricing: https://aistudio.google.com/docs/pricing
- Google Maps Platform pricing: https://developers.google.com/maps/billing-and-pricing/pricing
- ECB, tỷ giá tham chiếu EUR/USD: https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html
- Danmarks Nationalbank, chính sách tỷ giá cố định (746,038 DKK/100 EUR): https://www.nationalbanken.dk/en/frequently-asked-questions/questions-regarding-fixed-exchange-rate-policy

**Thị trường (blog, nhà cung cấp; chỉ để tham khảo)**
- consultant.dev, Nordic IT consultant market 2026: https://consultant.dev/blog/nordisk-konsultmarknad-2026
- consultant.dev, European IT contractor rates Q2 2026: https://consultant.dev/blog/european-it-rates-q2-2026
- Incorp Vietnam, chi phí outsource tại Việt Nam 2026: https://vietnam.incorp.asia/cost-to-outsource-ai-development-to-vietnam/
- Folio3, Dynamics to Salesforce migration: https://crm.folio3.com/blog/dynamics-to-salesforce-migration/
- Veelead, thời gian migration theo số user: https://www.veelead.com/migrating-from-salesforce-to-dynamics-365-sales-what-to-know-before-you-switch/
- Smartsheet, dự phòng ngân sách dự án (5–15%): https://www.smartsheet.com/content/project-budget-contingency

**Tài liệu của nhóm**
- [license-pricing.md](license-pricing.md) (Khang, #33)
- [cost-infra.md](cost-infra.md) và [crm-migration.md](crm-migration.md) (Nhật, #34)
- [docs/crm-integration.md](../crm-integration.md) (backend CRM, #36–#38)
- [samples/crm/README.md](../../samples/crm/README.md) (dữ liệu khách mẫu đã nạp vào org, 33/33 ca đạt)
