# Round 3 · Bài pitch OneOrder trong 15 phút

Bản dàn ý chờ Nghĩa duyệt. Phân vai dưới đây là đề xuất. Slide tiếng Việt, tên nút và trạng thái theo giao diện. Dành 10 phút sau pitch cho Q&A.

| Thời gian | Slide | Người nói | Câu chốt |
| --- | --- | --- | --- |
| 0:00–1:30 · Kết luận trước | 1–2 · Quyết định và tác động lên 3 nước | Nghĩa | Với khoảng €533k, chúng tôi giữ khung 12 tháng cho Thụy Điển và Đan Mạch, đưa Salesforce vào DK và hoãn Na Uy sang năm 2. |
| 1:30–4:00 · Khả thi và chi phí | 3–4 · Cầu ngân sách, chi phí vận hành | Nghĩa | Hoãn và thu gọn giải phóng €335k, thêm €103,5k cho migration và adapter. Dư khoảng €2k so với trần làm tròn nên phải kiểm soát phạm vi. |
| 4:00–7:00 · MVP mới | 5–6 · Trước/sau, giữ/hoãn/bỏ | Nhật | Giữ Review–Plan–Confirm và khả năng hứa ngày giao. Giảm phạm vi triển khai năm đầu để có chỗ cho nhiệm vụ CRM. |
| 7:00–10:00 · Kiến trúc và hành trình | 7–9 · Sơ đồ, luồng Hoffmann, khi CRM lỗi | Nhật | Nhân viên chọn đúng khách ở Review. Confirm giữ kho trước, đồng bộ Salesforce có trạng thái và có thể thử lại. |
| 10:00–12:30 · Lộ trình và rủi ro | 10–12 · Migration, timeline, bảng rủi ro | Khang | Salesforce DK hoạt động ở T4. Một lượt chạy thử và đối soát dữ liệu là điều kiện để chuyển hẳn. |
| 12:30–15:00 · Giả định và bước tiếp | 13–14 · Điều cần xác nhận và việc đầu tiên | Nghĩa | Chốt quyền API, chủ dữ liệu, cửa sổ chuyển đổi và phạm vi pilot trước khi cam kết triển khai. |

## Nhịp nói và thao tác

- **Slide 1–2:** Nói rõ đề bài cắt 30% và bắt buộc đổi CRM. DK là giả định của nhóm; Salesforce nhận dữ liệu ở T4, OneOrder DK go-live T6–T12.
- **Slide 3–4:** Đọc tổng cũ €764,5k, trần sau cắt khoảng €535k, phương án €533k. Các dòng chi phí cloud và AI là ước tính riêng để kiểm tra dự phòng, chưa thay số ngân sách nhóm. Chốt quyền API và bên chịu license với Company A.
- **Slide 5–6:** Nhấn mạnh nhu cầu của người dùng vẫn là xử lý một đơn và hứa ngày giao. Nêu tác động thực tế của việc hoãn Na Uy, co pilot và loại kết nối tạm với Dynamics.
- **Slide 7–9:** Dùng đơn email Hoffmann. Chỉ gợi ý khách, rồi chỉ kết quả khi đồng bộ. Chuyển sang slide 9 để mô tả CRM tạm lỗi: đơn đã Confirm, kho đã giữ, nhân viên thấy Pending sync. Nếu demo bằng mock, giới thiệu rõ dữ liệu giả lập. Chuẩn bị ảnh hoặc video dự phòng.
- **Slide 10–12:** Chỉ mốc T4 và T6. Nói ai có quyền dừng cutover nếu kiểm tra dữ liệu hoặc quyền thất bại. Nêu ví dụ Contact phải nối đúng Account.
- **Slide 13–14:** Mời Company A chốt người phụ trách từng việc. Chuyển Q&A bằng câu “Điều nào Company A muốn xác nhận trước khi bắt đầu pilot?”

Nguồn hình ngân sách, timeline và kiến trúc trước → sau: [PR #33](https://github.com/pumpowhat/OneOrder/pull/33). Nguồn dự toán và lộ trình migration: [PR #34](https://github.com/pumpowhat/OneOrder/pull/34).
