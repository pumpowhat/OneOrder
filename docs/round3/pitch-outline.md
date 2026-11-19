# Round 3 · Dàn ý pitch 15 phút

Bản khớp với [OneOrder-Round3.pptx](OneOrder-Round3.pptx), 15 slide, cập nhật 18/11/2026. Số liệu và nguồn ở [round3-proposal.md](round3-proposal.md). Phân vai dưới đây là đề xuất. Mỗi slide có ghi chú người nói trong file PPTX.

Mạch trình bày đi theo đúng 4 câu ban giám khảo hỏi: **khả thi → ưu tiên → đánh đổi → khuyến nghị.**

| Thời gian | Slide | Người nói | Ý chính |
| --- | --- | --- | --- |
| 0:00–0:45 | 1 · Mở đầu | Nghĩa | Kết luận trước: €533k trong trần €535k; Salesforce DK chạy cuối T3; SE + DK có OneOrder năm đầu, NO năm 2 |
| 0:45–1:45 | 2 · Đề bài | Nghĩa | Hai thay đổi kéo ngược chiều; 4 câu cần trả lời; giả định DK dùng Dynamics |
| 1:45–2:45 | 3 · Khả thi | Nghĩa | Phương án cũ thiếu €333k (38%); tính năng MVP vẫn vừa, phạm vi 3 nước thì không |
| 2:45–3:45 | 4 · Phương án | Nghĩa | 5 phương án A–E, chọn E (lần lượt từng nước) |
| 3:45–4:45 | 5 · Cầu ngân sách | Khang | €764,5k → €533k: −€335k cắt và hoãn, +€103,5k CRM |
| 4:45–5:45 | 6 · Cơ cấu ngân sách | Khang | 82% nhân sự; đơn giá €9.000/PM có nguồn; dự phòng 10,5% |
| 5:45–6:45 | 7 · Cloud và AI | Khang | Số thật khoảng €5k/năm; phần chênh trả license và dự phòng vận hành |
| 6:45–7:45 | 8 · MVP trước/sau | Nhật | Luồng đơn giữ nguyên, thêm CRM ở 2 điểm; đã chạy với Salesforce thật |
| 7:45–8:30 | 9 · Giữ, thêm, hoãn, bỏ | Nhật | Mỗi nhóm kèm tác động tiền |
| 8:30–9:30 | 10 · System context | Nhật | Salesforce nối hai chiều; Dynamics chỉ để migration; ERP Na Uy năm 2 |
| 9:30–10:30 | 11 · User journey | Nhật | Hai điểm chạm mới; nhánh Salesforce lỗi; đơn Thụy Điển; persona Freja |
| 10:30–11:30 | 12 · Migration | Nhật | 18 tuần, Gate 0 và Gate 2, tiêu chí go/no-go, so với mức tham chiếu thị trường |
| 11:30–12:30 | 13 · Lộ trình | Nghĩa | 12 tháng, 4 cổng quyết định, KPI Gate 1 |
| 12:30–13:45 | 14 · Đánh đổi và rủi ro | Nghĩa | Na Uy chờ 12 tháng; rủi ro lớn nhất là dữ liệu CRM; giới hạn của số liệu |
| 13:45–15:00 | 15 · Khuyến nghị | Nghĩa | 6 quyết định khởi động; 4 điều Company A cần xác nhận; mở sang hỏi đáp |

## Gợi ý demo (tùy chọn, khoảng 1 phút, trong slide 11)

1. Đơn email Hoffmann: chọn Hoffmann Byg A/S từ gợi ý Salesforce, Confirm, badge *Synced to Salesforce*.
2. Bật lỗi giả lập bằng `PUT /api/crm/mock-failure` với `{"modes": ["transient"]}`, Confirm một đơn: đơn vẫn `confirmed`, badge *Pending sync*.
3. Tắt lỗi giả lập, bấm *Retry sync*, badge đổi thành *Synced*. Hướng dẫn chi tiết: [docs/crm-integration.md](../crm-integration.md).

Nếu mạng hoặc máy có vấn đề, dùng video dự phòng ([backup-video.md](backup-video.md)) và nói ngắn theo ghi chú slide 11.

## Câu hỏi nên chuẩn bị

Trả lời chi tiết trong [qna.md](qna.md), bổ sung theo bản rà soát:

- **License Salesforce ai trả?** Phần tương đương Dynamics (€57,3k/năm) do ngân sách vận hành IT của DK trả. Phần chênh của Pro Suite + API (€10,9k) có trong ngân sách dự án năm đầu.
- **Vì sao không chọn gói Core?** Core đắt hơn Dynamics €49k/năm. Pro Suite + API đủ cho OneOrder; chạy thử migration trên Developer org.
- **€81k cho migration có thấp không?** Đó là chuyển gọn khoảng 50 user, không dựng lại tùy biến. Gate 0 xác nhận phạm vi trước khi cam kết; migration toàn phần thường $250–750k.
- **Cắt thêm 10% thì sao?** Dời OneOrder Đan Mạch sang năm 2 (−€90k), giữ CRM vì là bắt buộc.
