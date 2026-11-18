# Khách hàng CRM mẫu — Round 3

Chuẩn bị ngày **17/11/2026**. Có **18 Business Accounts và 18 Contacts**, gồm 4 khách bắt buộc và 14 khách bổ sung. Tên của 4 khách bắt buộc và 2 biến thể Hoffmann/Hofmann được giữ theo đề bài; mọi bản ghi trong bộ này chỉ là dữ liệu demo. Các công ty bổ sung được đặt tên cho kịch bản, không lấy thông tin từ danh bạ doanh nghiệp; đường phố và người liên hệ đều được tự tạo. Email dùng miền `example.invalid`; không gửi email hoặc gọi các số demo.

**Trạng thái:** CSV đã chuẩn bị; **chưa nạp vào Salesforce, chưa xác minh tìm kiếm và chưa có ảnh chụp kết quả**. Cần Developer org của Nghĩa để thực hiện các bước bên dưới. Không đưa tài khoản, mật khẩu, token hoặc cookie vào repo/PR.

## Mỗi khách dùng để demo gì?

| Account | Phone trong CSV | Thành phố | Trường hợp |
|---|---|---|---|
| Hoffmann Byg A/S | +45 33 12 45 78 | Odense | Khách email bắt buộc; tên chuẩn của nhóm gần trùng. |
| Skanska Sverige AB | +46 70 555 12 34 | Stockholm | Khách ảnh viết tay bắt buộc; cùng số với Skansbro, cần nhân viên chọn. |
| Bygg Väst AB | +46 70 123 45 67 | Göteborg | Khách Excel bắt buộc; tên gần giống Bygg Vaest. |
| Lars Byg ApS | +45 31 24 56 78 | København | Khách PDF bắt buộc; tìm theo số duy nhất. |
| Hoffmann Byg ApS | +45 00 00 10 01 | Odense | Tên gần Hoffmann Byg A/S nhưng khác loại hình công ty và số điện thoại. |
| Hofmann Byg A/S | +45 00 00 10 02 | Odense | Thiếu một chữ `f` so với Hoffmann Byg A/S; không tự gộp. |
| Moseglimt Materialer ApS | +45 33 12 45 78 | Odense | Khác tên nhưng cùng số hiển thị với Hoffmann Byg A/S. |
| Kobberengen Byg ApS | +4533124578 | Odense | Cùng số Hoffmann sau khi bỏ khoảng trắng. |
| Stenlunden Handel ApS | 33 12 45 78 | Odense | Số nội địa DK; chỉ thêm `+45` khi có ngữ cảnh DK. |
| Skansbro Projekt AB | +46 70 555 12 34 | Stockholm | Khác tên nhưng cùng số Skanska; số điện thoại không đủ để tự chốt. |
| Bygg Vaest AB | +46 00 000 10 03 | Göteborg | Biến thể `ä` → `ae` của Bygg Väst; cần kiểm tra tên và số. |
| Västglimt Material AB | +46 00 000 10 04 | Malmö | Khách SE bổ sung; kiểm tra tìm kiếm với dấu tiếng Thụy Điển. |
| Ravnekorn Montage ApS | +45 00 00 10 05 | Aarhus | Khách DK bổ sung, đối chứng khớp chính xác. |
| Birkelys Projekt ApS | +45 00 00 10 06 | Aalborg | Khách DK bổ sung, đối chứng tên không gần trùng. |
| Fjordmosaikk Bygg AS | +47 00 00 10 07 | Oslo | Khách Na Uy; dữ liệu có thể tồn tại trong org demo nhưng rollout OneOrder NO hoãn sang năm 2. |
| Granmåne Handel AS | +47 00 00 10 08 | Bergen | Khách Na Uy thứ hai; kiểm tra ký tự `å`. |
| Sølveng Entreprise ApS | +45 00 00 10 09 | Esbjerg | Khách DK bổ sung; kiểm tra ký tự `ø`. |
| Månglimt Logistik AB | +46 00 000 10 10 | Uppsala | Khách SE bổ sung, đối chứng tên và số duy nhất. |

### Các cặp gần trùng cần giữ riêng

1. Hoffmann Byg A/S ↔ Hoffmann Byg ApS: tên gần nhau, khác pháp nhân.
2. Hoffmann Byg A/S ↔ Hofmann Byg A/S: thiếu một chữ `f`.
3. Hoffmann Byg A/S ↔ Moseglimt Materialer ApS: khác tên, cùng số điện thoại.
4. Hoffmann Byg A/S ↔ Kobberengen Byg ApS: số điện thoại khác định dạng.
5. Hoffmann Byg A/S ↔ Stenlunden Handel ApS: số nội địa và số quốc tế DK.
6. Skanska Sverige AB ↔ Skansbro Projekt AB: cùng số điện thoại, khác công ty.
7. Bygg Väst AB ↔ Bygg Vaest AB: biến thể ký tự tên.

Các cặp này được cố ý giữ thành nhiều Account để demo gợi ý và Review. Khi tìm theo số chung, giao diện phải hiển thị các ứng viên và nhân viên xác nhận; không coi ứng viên đầu tiên là kết quả duy nhất. Số nội địa `33 12 45 78` cần ngữ cảnh DK để chuẩn hóa; không suy đoán quốc gia chỉ từ số.

## Nạp bằng Data Import Wizard

Chỉ dùng **Developer org demo** do Nghĩa cung cấp. Hai file là CSV UTF-8, dấu phẩy phân cách. Giữ Phone ở dạng chuỗi khi mở bằng Excel để không mất dấu `+` hoặc khoảng trắng. Không thay các số gần trùng thành số duy nhất vì sẽ làm mất tình huống kiểm thử.

1. Trong **Setup → Data Import Wizard → Launch Wizard → Standard Objects → Accounts and Contacts**, chọn thao tác thêm mới phù hợp. Nạp `accounts.csv` trước; không chọn Person Accounts. Chọn encoding UTF-8. Map thủ công cột `Name` → **Account: Account Name**, `Phone` → **Account: Phone** và các cột `Billing*`, `Shipping*` tới đúng trường Account. Không map nhầm Phone thành Contact Phone. Nếu org bật State and Country/Territory Picklists, kiểm tra các giá trị `Denmark`, `Sweden`, `Norway` được chấp nhận trong bước xem trước.
2. Dùng tên Account để đối chiếu bản ghi: các tên trong CSV là duy nhất, kể cả khi phone trùng. Kiểm tra mapping và preview trước khi Start Import; ghi lại job ID và số thành công/thất bại. Nếu org đã có dữ liệu từ một lần chạy trước, đối chiếu các bản ghi hiện có trước khi nạp lại để tránh tạo thêm bản sao ngoài chủ đích.
3. Nạp `contacts.csv` sau khi có đủ Accounts. Map `FirstName`, `LastName`, `Phone`, `Email` tới các trường **Contact**; map `AccountName` tới **Account: Account Name**/trường liên kết Account trong wizard và đối chiếu Account theo **Name** (hoặc **Name & Site**, giữ Site trống). `AccountName` là cột CSV phục vụ liên kết, không phải trường API `AccountId`: không map chuỗi tên trực tiếp vào Salesforce ID.
4. Chọn đối chiếu Contact theo **Email** để có khóa phân biệt ổn định cho 18 contact. Xem trước liên kết của ít nhất Hoffmann, Hofmann và Skanska; kết quả mong đợi là 18 Contacts gắn vào 18 Accounts đã có, không phát sinh Account mới. Nếu cấu hình org yêu cầu liên kết bằng ID, xuất danh sách Account Name + Salesforce ID sau lần nạp đầu, tạo **file tạm ngoài repo** với Account ID tương ứng và map theo Salesforce ID; giữ hai CSV gốc làm dữ liệu chuẩn.
5. Wizard có thể chặn dữ liệu gần trùng theo Duplicate Rules. Xem file lỗi và rule đang áp dụng trước khi thử lại; không gộp những cặp cố ý gần trùng. Nhờ quản trị viên Developer org cho phép tình huống demo trong org đó, hoặc nhập từng bản ghi bằng luồng cho phép lưu ứng viên trùng nếu rule hỗ trợ. Nếu rule vẫn chặn, ghi rõ bản ghi bị chặn và trạng thái chưa đạt; **không thay đổi rule trên production** và không tự tuyên bố đủ 18 Account.

Hướng dẫn chính thức (tra cứu 17/11/2026): [Import Data with the Data Import Wizard](https://help.salesforce.com/s/articleView?id=sf.import_with_data_import_wizard.htm&language=en_US&type=5), [What Is Imported for Business Accounts and Contacts?](https://help.salesforce.com/s/articleView?id=sf.for_accounts_and_contacts.htm&language=en_US&type=5), [Duplicate data blocks import](https://help.salesforce.com/s/articleView?id=000391118&language=en_US&type=1). Nhãn tùy chọn có thể khác theo cấu hình org; kiểm tra preview trước khi nạp.

## Kiểm tra và bằng chứng cho PR

- [ ] Job Accounts: 18 thành công, 0 lỗi chưa xử lý; lưu job ID và ngày giờ nạp.
- [ ] Job Contacts: 18 thành công, 0 lỗi chưa xử lý; kiểm tra liên kết đúng Account.
- [ ] Tìm Account theo `+45 33 12 45 78`: thấy Hoffmann Byg A/S và các ứng viên cùng số; kiểm tra thêm chuỗi số `33124578` theo khả năng tìm kiếm của org.
- [ ] Tìm `+46 70 555 12 34`: thấy Skanska Sverige AB và Skansbro Projekt AB.
- [ ] Tìm `+46 70 123 45 67`: thấy Bygg Väst AB.
- [ ] Tìm `+45 31 24 56 78`: thấy Lars Byg ApS.
- [ ] Kiểm tra ít nhất 4 cặp gần trùng ở trên vẫn tồn tại thành các Account riêng.
- [ ] Chụp màn hình kết quả hai job nạp, 4 lần tìm khách và danh sách gần trùng; thêm ảnh vào mô tả PR. Ảnh chỉ chứa dữ liệu demo, che tên đăng nhập/chi tiết tài khoản. Chưa có ảnh thì giữ checklist trống.

Có thể dùng Account list view với bộ lọc **Phone equals** để xác minh giá trị lưu; Global Search có thể lập chỉ mục chậm và không bảo đảm chuẩn hóa mọi định dạng. Việc tìm qua adapter OneOrder cần kiểm tra riêng sau khi backend CRM của Nghĩa merge.

## Dùng đúng bộ video demo

Dùng [samples/video-demo](../video-demo/README.md) theo [KichBanVideo.md](../../docs/video/KichBanVideo.md), đã có trên `main` tại commit `901b59b`. Các mẫu cũ ở `samples/emails`, `samples/photos`, `samples/excel`, `samples/pdf` có dữ liệu khách khác; không dùng lẫn với bộ quay này.

| Nguồn trong `samples/video-demo/` | Thông tin đầu vào | Việc cần làm tại Review |
|---|---|---|
| `emails/dk-odense-order.txt` | Hoffmann Byg A/S; `+45 33 12 45 78` | Giữ tên/số; sau khi backend CRM có, kiểm tra các ứng viên cùng số và chọn đúng Account. |
| `photos/se-handwritten-1.jpg` | Skanska Sverige AB; thiếu số điện thoại | Nhập `+46 70 555 12 34`; kiểm tra các dòng hàng và chọn đúng khách nếu có bước khớp CRM. |
| `excel/se-goteborg-materiallista.xlsx` | Thiếu tên; `+46 70 123 45 67` | Nhập `Bygg Väst AB`, sửa số lượng dòng 3 thành 25, xác nhận dòng hàng và chọn công trường Göteborg khi plan. |
| `pdf/dk-nordhavn-materialeliste.pdf` | Thiếu tên; `+45 31 24 56 78` | Nhập `Lars Byg ApS`, xác nhận các dòng hàng cần review. |

Không sửa mẫu/fixture trong phần việc này. Các ngày yêu cầu trong bộ demo là ngày cố định tháng 11/2026; ETA phụ thuộc ngày chạy. Trước Approve, cập nhật requested date hợp lệ cho buổi chạy thực tế nếu cần; nếu giữ ngày cũ để demo rủi ro trễ thì phải chủ động chấp nhận ở Confirm theo kịch bản. Cần đối chiếu thêm kịch bản Round 3 của Nghĩa sau khi bước khớp CRM được triển khai; hiện không coi màn hình CRM là chức năng đã chạy.
