# QnA Round 3 — bản nháp để Nghĩa và Nhật duyệt

Cập nhật 17/11/2026. Câu trả lời dưới đây được tổng hợp từ yêu cầu và mã hiện tại;
**chưa thu được xác nhận của Nghĩa/Nhật**. Người trả lời là phân công đề xuất.
Các hành vi CRM là thiết kế Round 3, chưa có trên main tại commit `901b59b`.

## Sao không nối tạm OneOrder với Dynamics 365?

**Trả lời (Nghĩa, chờ duyệt):** Dynamics ở DK chỉ là nguồn cho một lần chuyển dữ liệu,
nên nối tạm sẽ tạo thêm tích hợp phải bỏ khi hệ thống ngừng hoạt động.
Chúng tôi dành €81k cho migration và €22,5k cho adapter Salesforce có thể tiếp tục dùng;
OneOrder đọc khách khi Review và ghi đơn khi Confirm qua adapter này.

Tra nhanh: €103,5k = €81k + €22,5k; không có kết nối runtime OneOrder–Dynamics.

## Sao hoãn Na Uy mà không bỏ ETA hay bỏ AI?

**Trả lời (Nhật, chờ duyệt):** ETA và AI trực tiếp giải quyết cam kết giao hàng và nhập
đơn thủ công, là giá trị của pilot và phần lõi dùng chung.
Hoãn triển khai Na Uy sang năm 2 tiết kiệm €162k trong năm 1, còn SE và DK vẫn triển khai
trong 12 tháng; đây là hoãn phạm vi, không phải cam kết xóa bỏ chi phí năm 2.

Tra nhanh: SE pilot T0–T3, go-live T3–T6; DK migration T1–T4, adapter T4–T6,
go-live trên Salesforce T6–T12.

## License Salesforce ai trả? Nếu bị tính vào dự án thì cắt gì tiếp?

**Trả lời (Khang; Nghĩa xác nhận gói/API):** Giả định kế hoạch là DK trả license CRM từ
ngân sách vận hành, còn dự án trả migration và adapter.
Với 50 user, Pro Suite cơ bản khoảng €54,60k/năm nhưng nếu cả 50 user chịu phụ phí API
thì tổng khoảng €68,25k, đắt hơn Dynamics Enterprise €10,92k/năm; nếu phải tính vào dự án,
nhóm sẽ trình phê duyệt thu hẹp số user/đợt rollout DK và các phần giai đoạn 2 chưa cam kết,
kèm dự toán B3 mới thay vì khẳng định €533k đã bao gồm khoản đó.

Tra nhanh: phần dư €2k; nếu tính toàn bộ license/API cần giảm thêm khoảng €66,25k;
nếu chỉ tính phần tăng so với Dynamics cần giảm thêm khoảng €8,92k.
Nguồn, tỷ giá và điều kiện: [bảng license](license-pricing.md).

## Nếu ngân sách bị cắt thêm 10%?

**Trả lời (Nhật; Nghĩa duyệt phạm vi):** Nếu cắt tiếp 10% trên trần làm tròn €535k,
trần mới là €481,5k và kế hoạch €533k cần giảm thêm €51,5k.
Nhóm sẽ trình phương án chia rollout DK thành đợt nhỏ hơn và hoãn thêm hạng mục giai đoạn 2,
giữ migration bắt buộc, kiểm thử dữ liệu, tồn kho và các kiểm soát an toàn;
chưa có dự toán được duyệt để khẳng định phương án này đủ tiết kiệm €51,5k.

Tra nhanh: `535 × 90% = 481,5`; `533 − 481,5 = 51,5` (nghìn EUR).
Nếu dùng trần chính xác `764,5 × 70% = 535,15`, trần mới là €481,635k,
cần giảm €51,365k; slide dùng €535k theo đề.

## Lúc chuyển hẳn sang Salesforce, bán hàng có bị gián đoạn không?

**Trả lời (Nghĩa, chờ duyệt):** Mục tiêu là giảm gián đoạn bằng chạy thử migration,
đối soát số bản ghi, khóa ghi Dynamics trong cửa sổ chuyển đổi và nhập phần thay đổi cuối
trước khi mở Salesforce; chủ dữ liệu DK phải duyệt tiêu chí chuyển và phương án quay lui.
Thiết kế OneOrder cho phép Confirm vẫn giữ hàng khi CRM lỗi, lưu Pending sync rồi retry
theo External ID mã đơn để tránh tạo trùng; không hứa gián đoạn bằng không khi chưa chạy thử.

Tra nhanh: Salesforce sẵn sàng T4; adapter T4–T6; rollout DK T6–T12;
test lỗi/retry đang chờ backend CRM, chưa phải bằng chứng production.

## Dữ liệu cá nhân trong CRM xử lý theo GDPR thế nào?

**Trả lời (Nghĩa, chờ chủ dữ liệu/DPO duyệt):** Thiết kế chỉ lấy tên/số điện thoại cần
cho khớp khách, có phân quyền, mã hóa, nhật ký hạn chế dữ liệu cá nhân và lịch lưu/xóa;
Company A cần xác định căn cứ xử lý và trách nhiệm với nhà cung cấp trước khi dùng dữ liệu thật.
Triển khai EU/EEA cần kiểm tra cả nơi xử lý của CRM và AI, hợp đồng xử lý và cơ chế chuyển
dữ liệu ngoài EEA nếu có; demo chỉ dùng dữ liệu giả và chưa chứng minh tuân thủ production.

Tra nhanh: tối thiểu hóa, mục đích rõ, chính xác, thời hạn lưu và bảo mật theo
[European Commission — GDPR principles](https://commission.europa.eu/law/law-topic/data-protection/rules-business-and-organisations/principles-gdpr_en);
kiểm tra chuyển dữ liệu theo [hướng dẫn quốc tế của European Commission](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection_en)
(tra 17/11/2026). Không coi vùng lưu trữ EU tự động đáp ứng mọi yêu cầu GDPR.

## Hệ thống gợi ý sai khách thì phát hiện bằng cách nào?

**Trả lời (Khang; Nhật trình diễn Review):** Danh sách gợi ý phải hiển thị tên và số
điện thoại để nhân viên đối chiếu với nguồn và chốt, đặc biệt khi gần trùng tên hoặc dùng chung số.
Bộ CSV có các cặp gây nhầm và fixture có ca đúng, sai chính tả, nhiều ứng viên, không tìm thấy,
khác định dạng số để kiểm thử; chưa có backend matcher nên chưa tuyên bố độ chính xác.

Tra nhanh: [dữ liệu CRM](../../samples/crm/README.md),
[test cases](../../tests/fixtures/customer_match_cases.json); số trùng không đủ căn cứ tự chọn khách.

## Xác nhận trước pitch

| Nội dung | Người duyệt | Trạng thái |
|---|---|---|
| Hợp đồng adapter, Pending sync, External ID, cutover | Nghĩa | Chờ phản hồi và kiểm thử backend |
| Phạm vi €533k, phương án nếu cắt tiếp, timeline | Nghĩa + Nhật | Chờ B3 và slide chốt |
| Phần Review và sơ đồ kiến trúc trên slide | Nhật | Chờ duyệt |
| License, nguồn giá, số liệu CSV/test | Khang | Đã chuẩn bị; cần báo giá license production |
