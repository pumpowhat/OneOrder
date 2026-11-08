# OneOrder

**Một luồng xử lý thống nhất cho đơn hàng dự án B2B, từ danh sách vật tư đến công trường.**

Netcompany IT Consultant Challenge 2026 · Đội **3changlinhngulam**

---

## Mục lục

1. [Bài toán](#1-bài-toán)
2. [Giải pháp Vòng 1: OneOrder](#2-giải-pháp-vòng-1-oneorder)
3. [Vòng 2: MVP xây dựng](#3-vòng-2-mvp-xây-dựng)
4. [Thiết kế hệ thống](#4-thiết-kế-hệ-thống)
5. [Công nghệ đề xuất](#5-công-nghệ-đề-xuất)
6. [Cấu trúc repository](#6-cấu-trúc-repository)
7. [Bắt đầu nhanh](#7-bắt-đầu-nhanh)
8. [Sử dụng AI và kiểm chứng bởi con người](#8-sử-dụng-ai-và-kiểm-chứng-bởi-con-người)
9. [Sản phẩm bàn giao và tiến độ Vòng 2](#9-sản-phẩm-bàn-giao-và-tiến-độ-vòng-2)
10. [Lưu ý và miễn trừ](#10-lưu-ý-và-miễn-trừ)

---

## 1. Bài toán

**Công ty A** là nhà bán lẻ vật liệu xây dựng hàng đầu của Đan Mạch, có hàng trăm cửa hàng tại Đan Mạch, Na Uy và Thụy Điển. Công ty phục vụ cả khách hàng chuyên nghiệp (B2B) lẫn cá nhân (B2C) với vật liệu xây dựng, dụng cụ và sản phẩm cải tạo nhà.

Mỗi quốc gia tự xây hệ thống và quy trình thủ công riêng theo thời gian. Đề bài nêu bốn thách thức liên quan với nhau:

| Thách thức | Hệ quả |
|---|---|
| Quy trình thủ công | Kém hiệu quả, tốn nhiều công sức của nhân viên |
| Vận hành thiếu nhất quán | Mỗi cửa hàng vận hành và phục vụ khách một kiểu |
| Giao hàng và thực hiện đơn | Đơn hàng và giao hàng thiếu tin cậy |
| Hệ thống phân mảnh | Cải tiến khó nhân rộng giữa các quốc gia |

Mức độ cấp bách khác nhau theo thị trường:

| Thị trường | Vấn đề cấp bách nhất |
|---|---|
| Đan Mạch | Quy trình thủ công |
| Na Uy | Vận hành cửa hàng |
| Thụy Điển | Giao hàng và thực hiện đơn |

Ban lãnh đạo cần **một** giải pháp số có tác động kinh doanh lớn nhất, tôn trọng khác biệt địa phương và ra thị trường nhanh. Các đội phải chọn một cơ hội, xếp thứ tự ưu tiên, đề xuất giải pháp với MVP tập trung và lập kế hoạch triển khai cho ba thị trường.

---

## 2. Giải pháp Vòng 1: OneOrder

### 2.1 Nhận định về vấn đề

Hệ thống của Công ty A hoạt động tốt **bên trong** từng thị trường, và các đơn hàng đơn giản đã được số hóa. Khoảng trống nằm ở **đơn hàng dự án B2B**: nhà thầu gửi danh sách vật tư dài qua email, Excel hoặc giấy viết tay. Hàng đến từ cả chi nhánh lẫn trung tâm phân phối (DC), thường giao nhiều đợt và đôi khi cần xe cẩu. Những đơn này rơi vào kẽ hở giữa các hệ thống:

| Khâu | Vấn đề | Nặng nhất tại |
|---|---|---|
| Tiếp nhận đơn | Nhân viên bán hàng nhập lại tay các danh sách dài | Đan Mạch |
| Tồn kho và cam kết giao | Chi nhánh và DC chỉ thấy tồn kho của riêng mình, nên không ai cam kết được ngày giao | Cả ba thị trường |
| Giao tới công trường | Giao theo giai đoạn và xe cẩu được lên kế hoạch bằng điện thoại và bảng tính | Thụy Điển |
| Thương hiệu được mua lại | Mỗi doanh nghiệp được mua lại giữ ERP và quy trình chi nhánh riêng | Na Uy |

### 2.2 Đối chuẩn công khai (tương tự, không phải Công ty A)

Dữ liệu công khai về **STARK Group**, một nhà phân phối vật liệu xây dựng Bắc Âu, củng cố các giả định của đội:

- Lỗ ròng 286 triệu EUR trong năm tài chính 2024/25, nên không có ngân sách thay thế ERP nhiều năm.
- Mỗi quốc gia một thương hiệu và vẫn đang mua lại, nên giải pháp tích hợp phải cắm thêm được.
- DC trung tâm mới tại Thụy Điển và Đan Mạch, nên đơn hàng bị tách giữa chi nhánh và DC.
- Bắc Âu là khu vực tăng trưởng, nên giao hàng đáng tin cậy giúp giữ vị thế dẫn đầu.

*Nguồn: starkgroup.dk (11/2025, 9/2026), Octus (3/2026).*

### 2.3 Vì sao ưu tiên bài toán này

1. Đơn dự án chiếm phần lớn doanh thu: giao trễ làm đội thợ ngừng việc tại công trường và nhà thầu sẽ đổi nhà cung cấp.
2. Chạm đến cả bốn thách thức cùng lúc.
3. Giúp khoản đầu tư vào DC trung tâm hiện có sinh lợi.
4. Nhanh và vừa ngân sách: chạy trên các ERP hiện có.

### 2.4 Giải pháp

OneOrder là một **lớp điều phối đặt trên các ERP hiện có**, không thay thế chúng. Phần lõi dùng chung cho các thị trường, còn quy tắc được cấu hình theo từng quốc gia:

- **Tiếp nhận đơn bằng AI**: biến danh sách vật tư thành đơn nháp.
- **Tồn kho dùng chung**: một góc nhìn thống nhất về tồn kho chi nhánh và DC.
- **Kế hoạch thực hiện đơn**: chọn nguồn, tách đơn, chia giai đoạn, có cần xe cẩu hay không.
- **Cam kết giao và theo dõi**: khung giờ giao hàng và cảnh báo chậm trễ.

Mỗi ERP kết nối qua adapter riêng, nên doanh nghiệp được mua lại chỉ cần thêm một adapter.

### 2.5 Thí điểm, KPI và lộ trình (đề xuất Vòng 1)

- **Thí điểm**: 12 tuần tại Thụy Điển, khoảng 5 chi nhánh và 1 DC.
- **KPI** *(giả thuyết của đội, cần đối chiếu với baseline đo được)*:
  - +15 điểm phần trăm tỷ lệ giao đúng hạn và đủ hàng (on-time-in-full)
  - −50% thời gian xử lý thủ công
  - −30% lượt liên hệ hỏi "đơn hàng của tôi đâu?"
  - −20% lượt giao hàng thất bại
- **Triển khai**: Thụy Điển (tháng 0–6), Đan Mạch (tháng 4–9), Na Uy (tháng 6–12).

---

## 3. Vòng 2: MVP xây dựng

### 3.1 Hành trình người dùng cốt lõi (đầu-cuối)

```text
Nhà thầu gửi đơn              (ảnh viết tay / email / Excel)
      │
      ▼
[1] AI trích xuất dòng hàng   (khách hàng, công trường, ngày, mặt hàng, số lượng)
      │
      ▼
[2] Nhân viên bán hàng duyệt  (dòng có độ tin cậy thấp bắt buộc phải kiểm tra)
      │
      ▼
[3] OneOrder kiểm tra tồn kho DK, SE, NO và lập kế hoạch thực hiện đơn
      │
      ▼
[4] Mô hình ML dự đoán thời gian giao cho từng lô hàng
      │
      ▼
[5] Nhân viên bán hàng xác nhận; đơn và ngày cam kết được ghi nhận
```

### 3.2 Tính năng 1: Tiếp nhận đơn tự động

**Thông tin khách hàng:** ngoài tên, đơn cần có số điện thoại hợp lệ trước khi duyệt. Hệ thống đọc số từ ảnh/email/Excel khi có; nhân viên có thể nhập bổ sung hoặc sửa ngay trong Review. Draft được phép thiếu số, các đơn cũ được giữ nguyên. Xem [quy tắc số điện thoại](docs/customer-phone.md).


**Đầu vào**

- Ảnh danh sách vật tư viết tay (OCR bằng mô hình AI thị giác).
- PDF (`.pdf`), gồm PDF văn bản và PDF scan/ảnh viết tay nhiều trang: AI đọc toàn bộ tài liệu thành một đơn nháp.
- Email đặt hàng (văn bản tự do, tiếng Đan Mạch, Thụy Điển, Na Uy hoặc Anh).
- Tệp Excel (`.xlsx`): AI ánh xạ bố cục cột riêng của từng khách hàng.

**Tải PDF và OCR:** chọn hoặc kéo thả tệp tại màn hình Đơn hàng. Giới hạn **10 MB / 20 trang**;
PDF lỗi, rỗng hoặc có mã hóa/mật khẩu bị từ chối trước khi gọi AI. Gemini và Claude nhận tài liệu
PDF gốc để đọc cả văn bản, bảng và trang scan; kết quả vẫn phải qua Review/Approve như ảnh.
Tệp PDF gốc được lưu và hiển thị cạnh kết quả để đối chiếu, có liên kết tải xuống khi trình duyệt
không hỗ trợ xem trực tiếp. Xem [chi tiết triển khai và kiểm thử](docs/pdf-intake.md).

**Xử lý**

- AI trả về JSON có cấu trúc: khách hàng, địa điểm giao, ngày yêu cầu và các dòng hàng gồm số lượng, đơn vị, mô tả và điểm tin cậy.
- Mỗi dòng được đối khớp với danh mục sản phẩm (fuzzy matching kết hợp gợi ý của AI). Hai kết quả phải trùng nhau, nếu không dòng sẽ bị gắn cờ.
- Dòng có độ tin cậy dưới **85%** **bắt buộc** được người kiểm tra trước khi duyệt. Mọi thay đổi đều được ghi vào nhật ký kiểm toán (audit log).

### 3.3 Tính năng 2: Điều phối đơn hàng đa quốc gia

- Đọc tồn kho từ ba ERP giả lập: Đan Mạch, Thụy Điển và Na Uy. Mỗi ERP dùng định dạng dữ liệu gốc khác nhau và adapter sẽ chuẩn hóa chúng.
- Chọn nguồn hàng theo quy tắc (cấu hình trong `data/rules.json`):

  `chi nhánh gần nhất` → `DC trung tâm trong nước` → `DC ở quốc gia khác`

- Kết quả: kế hoạch thực hiện đơn chia theo lô hàng, gồm kho nguồn, các dòng hàng, trọng lượng, loại phương tiện (xe tải nhỏ / xe tải / xe cẩu), cờ giao xuyên biên giới, cùng lý do chọn từng nguồn.

### 3.4 Tính năng 3: Dự đoán thời gian giao hàng (thị trường Bắc Âu)

- Mô hình học máy dự đoán thời gian giao cho từng lô hàng, trả về **ngày dự kiến (P50)** và **ngày cam kết an toàn (P90)**.
- Đặc trưng (features): khoảng cách, loại nguồn (chi nhánh / DC / DC nước ngoài), xuyên biên giới, cần xe cẩu, tổng trọng lượng, số dòng hàng, thứ trong tuần, mùa đông.
- Dữ liệu huấn luyện là **dữ liệu mô phỏng**, được hiệu chỉnh theo các chuẩn giao hàng công khai tại Bắc Âu (dịch vụ DC giao hôm sau, thời gian vận chuyển xuyên biên giới, ảnh hưởng của mùa đông). Nguồn được ghi trong [docs/eta-calibration.md](docs/eta-calibration.md).
- Kế hoạch được so với ngày nhà thầu yêu cầu, mỗi lô hiển thị **đúng hạn** hoặc **có rủi ro**.

### 3.5 Ngoài phạm vi MVP

Tích hợp ERP thật, tối ưu tuyến đường, trang theo dõi dành cho nhà thầu, đăng nhập và phân quyền, ứng dụng di động, thanh toán.

### 3.6 Thay đổi so với Vòng 1 (giải thích trong video demo)

| Vòng 1 | Vòng 2 | Lý do |
|---|---|---|
| AI đọc email / PDF | Thêm ảnh viết tay và Excel | Đơn thực tế tại công trường đến theo các dạng này |
| Chi nhánh + DC trong một thị trường | Tồn kho xuyên DK, SE, NO | Giải quyết hệ thống phân mảnh; mặt hàng hiếm có thể chỉ có ở nước ngoài |
| Trang theo dõi + cảnh báo chậm | Dự đoán thời gian giao | Ngày giao đáng tin cậy ngay khi đặt hàng là giá trị cốt lõi, và khả thi trong 1 tuần |

---

## 4. Thiết kế hệ thống

### 4.1 Ngữ cảnh hệ thống (bên trong và bên ngoài OneOrder)

```text
                         ┌───────────────────────┐
                         │  Nhà thầu (B2B)       │
                         │  quản lý công trình,  │
                         │  người mua hàng       │
                         └───────────┬───────────┘
                                     │ gửi đơn: ảnh / email / Excel
                                     ▼
  ┌─────────────────┐  tải lên,   ╔═══════════════════════════════════════╗
  │ Nhân viên bán   │  duyệt,     ║                                       ║
  │ hàng / điều độ  │◄───────────►║          ONEORDER (MVP)               ║
  │ (Công ty A)     │  phê duyệt, ║                                       ║
  └─────────────────┘  xác nhận   ║  intake → review → plan → ETA         ║
                                  ║                                       ║
                                  ╚═══════════════════════════════════════╝
                                     │            │              │
                   trích xuất dòng   │            │ đọc tồn kho/ │ ghi xác nhận
                   (ảnh, văn bản,    │            │ đặt giữ hàng │ đơn hàng
                   cột Excel)        ▼            ▼              ▼
                         ┌─────────────────┐  ┌────────────────────────────┐
                         │ AI model API    │  │ ERP các nước (MOCK ở MVP)  │
                         │ (Gemini/Claude) │  │  - ERP Đan Mạch            │
                         │ Đặt tại EU khi  │  │  - ERP Thụy Điển + DC WMS  │
                         │ chạy production │  │  - ERP Na Uy               │
                         └─────────────────┘  └────────────────────────────┘
```

### 4.2 Bên trong OneOrder (container và thành phần)

```text
  ┌──────────────────────────────────────────────────────────────────────┐
  │  Web app (React)                                                     │
  │  Inbox | Review | Kế hoạch thực hiện | Tồn kho nhóm | Rules | Model  │
  └───────────────────────────────┬──────────────────────────────────────┘
                                  │ REST / JSON
  ┌───────────────────────────────▼──────────────────────────────────────┐
  │  Backend API (FastAPI)                                               │
  │                                                                      │
  │  ┌────────────────┐   ┌────────────────┐   ┌──────────────────────┐  │
  │  │ Intake service │──►│ Catalogue      │   │ Orchestration engine │  │
  │  │ - ảnh (OCR)    │   │ matcher        │   │ - quy tắc chọn nguồn │  │
  │  │ - văn bản email│   │ (RapidFuzz +   │   │ - tách / gom lô      │  │
  │  │ - Excel        │   │  gợi ý của AI) │   │ - chọn phương tiện   │  │
  │  └───────┬────────┘   └────────────────┘   └──────────┬───────────┘  │
  │          │                                            │              │
  │          ▼                                            ▼              │
  │  ┌────────────────┐   ┌────────────────┐   ┌──────────────────────┐  │
  │  │ AI client      │   │ Review & audit │   │ ETA model            │  │
  │  │ (live / demo)  │   │ log            │   │ (scikit-learn,       │  │
  │  └────────────────┘   └────────────────┘   │  P50 / P90)          │  │
  │                                            └──────────────────────┘  │
  │  ┌────────────────────────────────────────────────────────────────┐  │
  │  │ Lớp ERP adapter:  DK adapter | SE adapter | NO adapter         │  │
  │  └─────────────────────────────┬──────────────────────────────────┘  │
  └────────────────────────────────┼─────────────────────────────────────┘
            │                      │                       │
            ▼                      ▼                       ▼
     ┌─────────────┐     ┌────────────────────┐    ┌──────────────────┐
     │ SQLite DB   │     │ Mock ERP service   │    │ Cấu hình & dữ liệu│
     │ orders,     │     │ 3 định dạng gốc:   │    │ rules.json,      │
     │ lines,      │     │  DK: CSV           │    │ catalogue,       │
     │ audit log   │     │  SE: JSON (tên     │    │ warehouses,      │
     └─────────────┘     │      trường tiếng  │    │ sites            │
                         │      Thụy Điển)    │    └──────────────────┘
                         │  NO: JSON (tiếng   │
                         │      Anh)          │
                         └────────────────────┘
```

### 4.3 Luồng tuần tự cho một đơn hàng

```text
  Sales desk     Web app        Backend           AI API      Mock ERPs
      │  upload     │               │                 │            │
      │────────────►│ POST /intake  │                 │            │
      │             │──────────────►│ extract         │            │
      │             │               │────────────────►│            │
      │             │               │◄── JSON lines ──│            │
      │             │               │ match catalogue │            │
      │             │◄── draft ─────│                 │            │
      │ review/edit │               │                 │            │
      │────────────►│ POST /approve │                 │            │
      │             │──────────────►│ audit log       │            │
      │ plan        │               │                 │            │
      │────────────►│ POST /plan    │ read stock (x3) │            │
      │             │──────────────►│─────────────────────────────►│
      │             │               │◄──── native formats ─────────│
      │             │               │ normalise, apply rules,      │
      │             │               │ predict ETA                  │
      │             │◄── plan ──────│                 │            │
      │ confirm     │               │                 │            │
      │────────────►│ POST /confirm │ write reservation            │
      │             │──────────────►│─────────────────────────────►│
```

### 4.4 Các API endpoint chính

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/inbox` | Hộp thư mẫu (email, ảnh viết tay, Excel trong `samples/`) |
| `POST` | `/api/inbox/import` | Nhập một mục trong hộp thư mẫu như một lần tải lên, trả về đơn nháp |
| `POST` | `/api/intake` | Ảnh / PDF (văn bản hoặc scan) / văn bản email / Excel → đơn nháp |
| `GET` | `/api/orders/{id}` | Đơn hàng kèm dòng hàng, trạng thái và audit log |
| `POST` | `/api/orders/{id}/approve` | Các dòng đã kiểm tra (xác nhận bởi con người) |
| `POST` | `/api/orders/{id}/plan` | Kế hoạch thực hiện đơn kèm ETA P50/P90 cho từng lô và cho cả đơn; lưu kế hoạch, chuyển đơn sang `planned` |
| `POST` | `/api/orders/{id}/cancel` | Hủy đơn chưa xác nhận |
| `POST` | `/api/orders/{id}/confirm` | Ghi đặt giữ hàng vào ERP giả lập của từng nước (tất cả hoặc không), đóng băng kế hoạch và ETA, chuyển đơn sang `confirmed`. Trả 409 nếu thiếu hàng (trừ khi `allow_partial`), ETA bị trễ (trừ khi `accept_late_risk`) hoặc tồn kho đã bị đơn khác giữ |
| `GET` | `/api/stock` | Tồn kho toàn tập đoàn qua các adapter, đã trừ hàng đã giữ; lọc theo nước, từ khóa, hàng sắp hết |
| `GET` | `/api/orders` | Danh sách đơn (lọc `?status=`) |
| `GET` | `/api/orders/{id}/source` | File gốc của đơn (ảnh, PDF, nội dung email hoặc bảng Excel) để đối chiếu |
| `GET` | `/api/orders/{id}/availability` | Tiền kiểm tra từng dòng với tồn kho 3 nước |
| `GET` / `PUT` | `/api/rules` | Quy tắc nghiệp vụ |
| `GET` | `/api/model` | Chỉ số và đặc trưng của mô hình ETA |
| `GET` | `/mock-erp/{dk\|se\|no}/stock` | Tồn kho theo định dạng gốc của ERP từng nước (DK CSV, SE JSON tiếng Thụy Điển, NO JSON tiếng Anh), đã gồm hàng đã giữ |
| `GET` / `POST` | `/mock-erp/{dk\|se\|no}/reservations` | Xem và ghi đặt giữ hàng vào ERP của một nước; trả 409 nếu kho không đủ hàng |
| `DELETE` | `/mock-erp/{dk\|se\|no}/reservations/{order_ref}` | Giải phóng đặt giữ của một đơn |

### 4.5 Luồng trạng thái đơn hàng

```text
draft ──approve──► approved ──plan──► planned ──confirm──► confirmed
  │                   │                 │  ▲
  │                   │                 └──┘  plan lại (kế hoạch cũ bị ghi đè)
  └───────────────────┴─────────────────┴──► cancelled
```

| Trạng thái | Ý nghĩa |
|---|---|
| `draft` | Đơn nháp do AI trích xuất từ ảnh / email / Excel; có thể còn dòng cần kiểm tra |
| `approved` | Mọi dòng đã được nhân viên kiểm tra và duyệt |
| `planned` | Đã có kế hoạch thực hiện đơn, lưu cùng đơn; có thể lập lại |
| `confirmed` | Đã ghi đặt giữ hàng vào ERP giả lập. Trạng thái cuối |
| `cancelled` | Hủy trước khi xác nhận. Trạng thái cuối; kế hoạch cũ vẫn được giữ để tra cứu |

- Mỗi lần đổi trạng thái đều ghi vào audit log (`approve`, `plan`, `cancel`).
- Không thể hủy đơn đã `confirmed`, vì phải trả lại hàng đã giữ trong ERP (ngoài phạm vi MVP).
- Chuyển trạng thái không hợp lệ trả về `409`. Bảng chuyển nằm ở `backend/services/orders/status.py`.
- Bỏ `RECEIVED` và `EXTRACTED` của bản thiết kế đầu: file được xử lý ngay trong một lần gọi `/intake`, nên `draft` là trạng thái đầu tiên. Trạng thái `failed` (ERP từ chối đặt giữ hàng) sẽ được thêm cùng `/confirm`.

### 4.6 Các quyết định thiết kế chính

- **Lớp điều phối, không phải ERP mới**: các ERP vẫn là hệ thống ghi nhận chính thức (system of record).
- **Mỗi ERP một adapter**: thêm thị trường hoặc doanh nghiệp mua lại chỉ cần thêm một adapter.
- **Quy tắc nghiệp vụ nằm trong cấu hình** (`rules.json`), không nằm trong mã nguồn, nên có thể thay đổi theo thị trường hoặc theo yêu cầu mà không cần triển khai lại.
- **AI đề xuất, con người quyết định**: AI không bao giờ tự xác nhận đơn hàng.
- **Nhà cung cấp AI có thể thay thế** sau một giao diện client duy nhất; có chế độ demo không cần API key để ứng dụng luôn chạy được cục bộ.

---

## 5. Công nghệ đề xuất

| Tầng | Lựa chọn | Lý do |
|---|---|---|
| Frontend | React + Vite + TypeScript, Tailwind CSS | Xây nhanh, màn hình rõ ràng cho video demo |
| Backend API | Python 3.12 + FastAPI | Đơn giản, có kiểu dữ liệu, tự sinh tài liệu API (`/docs`); Python phù hợp với AI/ML |
| AI (OCR + văn bản) | Gemini API (`google-genai`, mặc định) hoặc Claude API (`anthropic`), chọn bằng `AI_PROVIDER`; model đặt bằng `AI_MODEL` trong `.env` | Đọc được chữ viết tay và nhiều ngôn ngữ Bắc Âu; trả về JSON có cấu trúc |
| Phân tích Excel | openpyxl / pandas | Đọc `.xlsx`; AI ánh xạ các bố cục cột chưa biết |
| Đối khớp danh mục | RapidFuzz | Fuzzy matching nhanh, có điểm số để làm độ tin cậy |
| Dự đoán ETA | scikit-learn `GradientBoostingRegressor` (quantile loss) | Quantile regression cho ngày P50 và P90; nhỏ gọn và dễ giải thích |
| Cơ sở dữ liệu | SQLite (SQLAlchemy) | Không cần cài đặt, chạy cục bộ |
| ERP giả lập | Dịch vụ FastAPI riêng (3 định dạng gốc) | Thể hiện tích hợp thực tế với các định dạng khác nhau |
| Cấu hình | JSON (`rules.json`) + `.env` | Sửa quy tắc không cần đụng mã nguồn |
| Kiểm thử | pytest | Đối khớp, quy tắc, adapter, ETA |
| Tùy chọn | Docker Compose | Một lệnh để chạy toàn bộ dịch vụ |

> **Hướng production (ngoài MVP):** cloud đặt tại EU, mô hình AI đặt tại EU hoặc có thể thay thế (GDPR), message queue hoặc sự kiện từ các ERP, đăng nhập một lần (SSO).

---

## 6. Cấu trúc repository

*(dự kiến)*

```text
oneorder-mvp/
├── README.md
├── .env.example            # AI_PROVIDER=gemini|claude, GEMINI_API_KEY=, ANTHROPIC_API_KEY=, AI_MODEL=, AI_MODE=live|demo
├── requirements.txt
├── backend/
│   ├── main.py             # FastAPI app
│   ├── services/           # intake, matching, orchestrator, eta
│   ├── erp/                # adapters + mock ERP service
│   └── db.py
├── frontend/               # React app
├── data/                   # catalog, warehouses, sites, stock, rules.json
├── samples/                # đầu vào demo: ảnh viết tay, email, Excel,
│                           # và fixture demo để chạy không cần key
├── scripts/                # script sinh dữ liệu mẫu và huấn luyện mô hình
├── docs/                   # hành trình người dùng, sơ đồ hệ thống, hiệu chỉnh ETA
└── tests/
```

---

## 7. Bắt đầu nhanh

*(thiết lập mục tiêu)*

### Backend

```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # thêm API key của bạn, hoặc đặt AI_MODE=demo
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                       # mở http://localhost:5173
```

### Kiểm thử

```bash
pytest                            # chỉ backend
./run-oneorder.sh                 # = start: bật backend + frontend, dùng AI thật nếu .env có khóa API
./run-oneorder.sh test            # pytest + kiểm tra kiểu, lint và build frontend
./run-oneorder.sh smoke           # dựng cả hai máy chủ trên DB tạm, chạy thử luồng đầu-cuối qua giao diện
./run-oneorder.sh all             # test rồi smoke
FRESH=1 ./run-oneorder.sh         # bật với DB trống (AI_MODE=demo để ép chế độ mô phỏng)
```

### Chế độ demo

Khi không có API key, ứng dụng dùng các fixture demo đã ghi sẵn cho các đầu vào mẫu, và dùng bộ phân tích theo quy tắc cho văn bản thuần. Giao diện luôn hiển thị chế độ đang hoạt động.

### Chạy bằng Docker

Khởi chạy toàn bộ dịch vụ backend với Docker Compose:

```bash
docker compose up --build
```

Sau khi khởi động, mở [http://localhost:8000/docs](http://localhost:8000/docs) để xem tài liệu API Swagger UI hoặc kiểm tra trạng thái tại [http://localhost:8000/api/health](http://localhost:8000/api/health).

---

## 8. Sử dụng AI và kiểm chứng bởi con người

### Trong sản phẩm

- AI trích xuất, con người phê duyệt. Mỗi dòng hiển thị văn bản gốc và điểm tin cậy.
- Bộ đối khớp danh mục kiểm tra chéo gợi ý sản phẩm của AI.
- Dòng dưới ngưỡng kiểm tra bị chặn cho đến khi có người xác nhận.
- Mọi chỉnh sửa và phê duyệt được lưu trong audit log.
- Việc chọn nguồn và phương tiện dùng quy tắc tường minh, không phải hộp đen.

### Trong dự án

- Đội ghi lại cách sử dụng trợ lý AI (nghiên cứu, slide, mã nguồn, sơ đồ) và những gì đã kiểm tra hoặc chỉnh sửa trong **AI Journal** (sản phẩm bàn giao Vòng 2).
- Không commit API key, mật khẩu hay dữ liệu bí mật. Key nằm trong `.env`, đã được liệt kê trong `.gitignore`.

---

## 9. Sản phẩm bàn giao và tiến độ Vòng 2

**Hạn nộp:** 22:00 (GMT+7), ngày 9/11/2026
**Gửi tới:** EB.VN@netcompany.com, tiêu đề `Round 2 - 3changlinhngulam`

### Sản phẩm bàn giao

- [ ] **MVP.mp4**: video demo, tối đa 7 phút, thuyết minh hoặc phụ đề tiếng Anh
- [ ] **User Journey.pdf**: tối đa 2 trang, có ít nhất một hành trình đầu-cuối
- [ ] **System Context Diagram.pdf**: tối đa 2 trang, có nhãn thực thể và luồng dữ liệu
- [ ] **AI Journal.pdf**: theo mẫu của ban tổ chức

### Kế hoạch

| Ngày | Công việc |
|---|---|
| 2/11 | Chốt phạm vi, dữ liệu mẫu, thiết lập dự án, bắt đầu AI Journal |
| 3–4/11 | Tiếp nhận đơn (ảnh, email, Excel) + màn hình review + ERP giả lập |
| 5/11 | Quy tắc điều phối + màn hình tồn kho nhóm |
| 6/11 | Mô hình ETA + màn hình kế hoạch; nối toàn bộ luồng |
| 7/11 | Kiểm thử với nhiều tệp mẫu; sơ đồ hệ thống |
| 8/11 | Quay video; hành trình người dùng; hoàn thiện AI Journal |
| 9/11 | Dự phòng; nộp trước 20:00 |

### Tiêu chí đánh giá

Chất lượng kỹ thuật, kiến trúc hợp lý, sử dụng AI phù hợp (có kiểm chứng bởi con người), lập luận kỹ thuật rõ ràng và nhất quán với bài toán Vòng 1.

---

## 10. Lưu ý và miễn trừ

- Công ty A được ẩn danh. Toàn bộ khách hàng, đơn hàng, tồn kho và lịch sử giao hàng trong repository này là **dữ liệu mẫu hư cấu**.
- Số liệu của STARK Group là dữ liệu công khai, chỉ dùng làm đối chuẩn tương tự.
- Mô hình ETA được huấn luyện trên dữ liệu mô phỏng, hiệu chỉnh theo nguồn công khai. Mô hình **không** dùng dữ liệu thật của Công ty A.
- Mục tiêu KPI là giả thuyết của đội, không phải kết quả đo được.
- Tài liệu đề bài là bí mật của IT Consultant Challenge 2026 và không được đưa vào repository này.

---

<p align="center"><sub>Đội 3changlinhngulam · IT Consultant Challenge 2026</sub></p>
