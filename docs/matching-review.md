# Quy tắc lựa chọn sản phẩm và yêu cầu kiểm tra

Phạm vi: bản sửa issue #24. Đây là mô tả hành vi đã kiểm tra, không phải quy định cho phép thay thế vật tư.

## Các quyết định đã xác nhận

- Không tự thay 100mm bằng 150mm; cũng không tự coi 9mm và 9,5mm là tương đương. Chưa có quy định cho phép thay thế hai độ dày này.
- Đọc số đo và đơn vị trước khi so tên. Tên chính của sản phẩm là nguồn số đo ưu tiên; tên gọi khác không được ghi đè số đo mâu thuẫn trong tên chính.
- Các cụm kích thước phải khớp nguyên cụm và giữ thứ tự. Không lấy 45 từ 45x95 và 145 từ 145x200 để đáp ứng 45x145.
- Nếu yêu cầu có mã C, mã đó phải có ở sản phẩm. Mã trong tên chính được ưu tiên; khi tên chính không ghi mã thì dùng tên gọi khác. Điều này giữ được cả C24 của gỗ và C70 của thanh thép.
- Khi một số đo đơn lẻ chỉ khớp với thành phần trong cụm kích thước và còn số đo đơn lẻ khác ở tên chính, hệ thống chưa đủ cơ sở khẳng định cùng ý nghĩa; dòng cần người kiểm tra, kể cả tên gọi khác khớp hoàn toàn.

## Những tình huống đã kiểm tra

| Yêu cầu | Kết quả |
| --- | --- |
| Hai mô tả bông đá 100mm của issue #24 | Loại sản phẩm 150mm; vẫn cần người kiểm tra vì chưa xác định chắc chắn sản phẩm phù hợp |
| Tấm 9mm, sản phẩm 9,5mm (và chiều ngược lại) | Không tự chọn sản phẩm đó |
| Gỗ C24, sản phẩm ghi C18 | Không tự chọn sản phẩm đó |
| Gỗ C24 45x145mm dài 4,2m | Sản phẩm TIM-SPRU-45145-42 ghi C24, 45x145mm, 4,2m; khi thông tin trích xuất đủ tin cậy và lựa chọn đủ rõ, dòng không bắt buộc kiểm tra lại |
| Gỗ C24 45x145mm nhưng không ghi chiều dài | Vẫn cần người kiểm tra |
| Tấm gọi là gipsplade 3m | Giữ được SKU tấm dài 3m, nhưng cần người kiểm tra vì số đo 3m được suy ra từ cụm kích thước trong tên chính |
| Số 100 ở chiều rộng của sản phẩm 150mm 100x1000mm | Không được dùng để tự chấp nhận yêu cầu insulation 100mm; dòng cần kiểm tra |

Bỏ yêu cầu kiểm tra ở một dòng không phải tự duyệt đơn. Người dùng vẫn thực hiện thao tác duyệt đơn.

## Giới hạn

Catalogue hiện lưu quy cách trong tên và tên gọi khác, chưa tách thành các trường độ dày, đường kính, chiều rộng, chiều dài và cấp chất lượng. Các chốt trên xử lý những trường hợp đã tái hiện; không chứng minh hệ thống hiểu mọi quy cách hay mọi điều kiện thay thế vật tư. Việc tách quy cách thành dữ liệu có cấu trúc là công việc tiếp theo nếu mở rộng phạm vi tự động lựa chọn.

Các nhóm kích thước không ghi đơn vị trong tên catalogue (ví dụ 1200x3000) được đọc theo quy ước mm đang có của catalogue. Không bổ sung chiều dài mà khách chưa ghi. Những yêu cầu thiếu thông tin khác vẫn chịu quy tắc điểm khớp, độ mơ hồ và độ tin cậy hiện hành; chưa có cơ chế bảo đảm phát hiện mọi thông tin nghiệp vụ còn thiếu.
