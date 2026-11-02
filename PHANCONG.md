# Phân công công việc: OneOrder (Vòng 2)

**Hạn nộp bài:** 22:00 (GMT+7), 9/11/2026 · Mục tiêu nộp sớm: trước 20:00.
**Cập nhật lần cuối:** 2/11/2026

## Thành viên

| Thành viên | Vai trò chính | Mức độ task |
|---|---|---|
| **Nghĩa** | Trưởng nhóm, backend, AI, mô hình ML | Khó |
| **Khang** | Dữ liệu mẫu, ERP giả lập, kiểm thử | Dễ – vừa |
| **Nhật** | Frontend, tài liệu, sơ đồ | Dễ – vừa |

---

## Task đầu tiên (hạn: **3/11/2026**)

### Khang: Dữ liệu mẫu và ERP giả lập

**Mục tiêu:** có đủ dữ liệu để backend chạy được luồng đầu-cuối.

- [ ] Tạo `data/catalog.json`: khoảng 150–200 sản phẩm xây dựng (mã, tên bằng tiếng Đan Mạch/Thụy Điển/Na Uy/Anh, đơn vị, trọng lượng, có cần xe cẩu không).
- [ ] Tạo `data/warehouses.json`: khoảng 15 kho gồm chi nhánh và DC ở DK, SE, NO (mã kho, tên, quốc gia, loại, toạ độ).
- [ ] Tạo `data/sites.json`: khoảng 10 công trường mẫu có địa chỉ và toạ độ.
- [ ] Tạo dữ liệu tồn kho theo **3 định dạng gốc khác nhau**:
  - DK: CSV
  - SE: JSON, tên trường tiếng Thụy Điển
  - NO: JSON, tên trường tiếng Anh
- [ ] Có một số mặt hàng hiếm chỉ tồn tại ở nước ngoài, để demo cross-border.

**Kết quả cần nộp:** các file nằm trong `data/`, kèm một đoạn mô tả ngắn về định dạng trong `docs/data-formats.md`.
**Cách nghiệm thu:** Nghĩa đọc được cả 3 nguồn bằng adapter mà không phải sửa tay dữ liệu.

### Nhật: Khung giao diện frontend

**Mục tiêu:** có app React chạy được, với layout và điều hướng cho các màn hình chính.

- [ ] Khởi tạo `frontend/` bằng React + Vite + TypeScript + Tailwind CSS.
- [ ] Dựng layout chung (thanh bên, header) và route cho 6 màn hình: **Inbox, Review, Kế hoạch thực hiện, Tồn kho nhóm, Rules, Model**.
- [ ] Mỗi màn hình có nội dung giả (placeholder) với dữ liệu cứng, chưa cần gọi API.
- [ ] Hiển thị badge chế độ AI (`live` / `demo`) ở header.
- [ ] Cấu hình proxy `/api` tới `http://localhost:8000`.

**Kết quả cần nộp:** `npm install && npm run dev` mở được tại `http://localhost:5173`, điều hướng giữa 6 màn hình không lỗi.
**Cách nghiệm thu:** Nghĩa chạy thử và không phải sửa cấu hình.

### Nghĩa: Dịch vụ tiếp nhận đơn (intake)

**Mục tiêu:** từ ảnh/email/Excel ra được đơn nháp dạng JSON.

- [ ] Viết `AI client` với 2 chế độ `live` (Claude vision) và `demo` (fixture ghi sẵn).
- [ ] Viết `backend/services/intake` xử lý ảnh, văn bản email và Excel.
- [ ] Endpoint `POST /api/intake` trả về đơn nháp kèm điểm tin cậy cho từng dòng.

---

## Các task tiếp theo (dự kiến)

| Ngày | Nghĩa | Khang | Nhật |
|---|---|---|---|
| **4/11** | Bộ đối khớp danh mục (RapidFuzz + gợi ý AI), audit log, endpoint `approve` | Viết test cho adapter ERP và đối khớp danh mục; chuẩn bị file mẫu (ảnh viết tay, email, Excel) | Màn hình **Inbox** và **Review** nối API thật |
| **5/11** | Orchestration engine: quy tắc chọn nguồn, tách lô, chọn phương tiện | Màn hình **Tồn kho nhóm** và dữ liệu cho `rules.json` | Màn hình **Rules** (xem và sửa quy tắc) |
| **6/11** | Mô hình ETA (P50/P90), endpoint `plan` và `confirm`, nối toàn bộ luồng | Script sinh dữ liệu huấn luyện mô phỏng, tài liệu `docs/eta-calibration.md` | Màn hình **Kế hoạch thực hiện** và **Model** |
| **7/11** | Sửa lỗi tích hợp, tinh chỉnh độ chính xác | Chạy thử với nhiều file mẫu, ghi lại lỗi | Soạn **System Context Diagram.pdf** |
| **8/11** | Quay video demo (**MVP.mp4**) | Soạn **User Journey.pdf**, hỗ trợ video | Hoàn thiện **AI Journal.pdf** cùng Nghĩa |
| **9/11** | Dự phòng, rà soát, nộp bài trước 20:00 | Dự phòng | Dự phòng |

> Các task sau 3/11 là bản nháp, sẽ chốt lại khi hoàn thành task đầu tiên.

---

## Quy ước làm việc

- Mỗi người làm trên **nhánh riêng** (ví dụ `khang/data`, `nhat/frontend`) rồi tạo Pull Request vào `main`, vì `main` yêu cầu PR.
- Commit nhỏ, thông điệp rõ ràng. Không commit `.env`, API key hay dữ liệu thật.
- Gặp vướng mắc quá 30 phút thì báo ngay trong nhóm, không để đến cuối ngày.
- Mỗi người tự ghi lại cách dùng trợ lý AI (đã hỏi gì, đã kiểm tra hoặc sửa gì) để làm **AI Journal**.
- Cuối mỗi ngày, cập nhật các ô checkbox trong file này.
