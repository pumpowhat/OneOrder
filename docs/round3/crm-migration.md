# Chuyển CRM Đan Mạch từ Dynamics 365 sang Salesforce

Phương án Round 3 giả định Đan Mạch (DK) là nước đang dùng Dynamics 365. Chuyển dữ liệu một lần trong T1–T4 và đưa Salesforce vào sử dụng ở T4. OneOrder tra khách và ghi đơn qua Salesforce sau khi adapter sẵn sàng. Dynamics chỉ tham gia luồng xuất dữ liệu migration. [Issue #31](https://github.com/pumpowhat/OneOrder/issues/31)

## C1. Dữ liệu đưa qua Salesforce

**Giả định để dự trù khối lượng:** chuyển lịch sử liên hệ trong **24 tháng tính lùi từ ngày cutover**. Lịch sử cũ hơn chuyển vào kho lưu trữ chỉ đọc. Xác nhận lại cửa sổ này với chủ dữ liệu DK sau khi đếm theo tháng. Các cột bên dưới là ánh xạ đề xuất, cần đối chiếu metadata của hai org trước khi khóa schema.

| Dynamics → Salesforce | Trường chính (nguồn → đích) | Quyết định và lý do |
| --- | --- | --- |
| `account` → `Account` | `accountid` → `Legacy_Account_ID__c`, `name` → `Name`, `telephone1` → `Phone`, `address1_line1` → `BillingStreet`, `address1_city` → `BillingCity`, `address1_country` → `BillingCountry`, `ownerid` → `OwnerId`, `parentaccountid` → `ParentId` | Chuyển doanh nghiệp và quan hệ giữa các doanh nghiệp. [Dataverse Account](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/reference/entities/account) · [Salesforce Account](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_account.htm) |
| `contact` → `Contact` | `contactid` → `Legacy_Contact_ID__c`, `firstname` → `FirstName`, `lastname` → `LastName`, `telephone1` → `Phone`, `mobilephone` → `MobilePhone`, `emailaddress1` → `Email`, `parentcustomerid` → `AccountId` nếu cha là Account, `ownerid` → `OwnerId` | Chuyển người liên hệ và nối lại Account theo bảng ID. Đưa trường hợp cha khác loại hoặc họ trống vào danh sách cần xác minh. [Dataverse Contact](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/reference/entities/contact) · [Salesforce Contact](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contact.htm) |
| `opportunity` đang mở → `Opportunity` | `opportunityid` → `Legacy_Opportunity_ID__c`, `name` → `Name`, `parentaccountid` → `AccountId`, `estimatedvalue` → `Amount`, `estimatedclosedate` → `CloseDate`, giai đoạn bán hàng theo quy trình DK → `StageName`, `transactioncurrencyid` → `CurrencyIsoCode` nếu bật đa tiền tệ, `ownerid` → `OwnerId` | Chuyển cơ hội đang mở để đội bán hàng tiếp tục xử lý. Lưu chỉ đọc cơ hội đã đóng. Ngày đóng thiếu cần người phụ trách xác nhận trước khi nhập. [Dataverse Opportunity](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/reference/entities/opportunity) · [Salesforce Opportunity](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunity.htm) |
| `phonecall`, `email`, `task`, `appointment` → `Task` / `Event` | `activityid` → khóa đối soát ngoài Salesforce, `subject` → `Subject`, `description` → `Description`, `regardingobjectid` và bên liên hệ → `WhatId` / `WhoId`, `ownerid` → `OwnerId`, `scheduledstart` → `StartDateTime` (Event), `scheduledend` → `ActivityDate` (Task) / `EndDateTime` (Event), `statecode` / `statuscode` → `Status` (Task) | Chuyển lịch sử liên hệ đủ điều kiện trong 24 tháng. Đưa cuộc hẹn có giờ bắt đầu/kết thúc vào Event, ghi nhận cuộc gọi/email thành Task. Lấy ngày thực tế cho hoạt động đã kết thúc nếu có, quy đổi múi giờ trước khi phân theo cửa sổ. [Dataverse ActivityPointer](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/reference/entities/activitypointer) · [Salesforce Task và Event qua Data Loader](https://help.salesforce.com/s/articleView?id=000005178&language=en_US&type=1) |
| Plugin, workflow, báo cáo tùy biến | Kiểm kê tên, chủ sở hữu, mục đích và phụ thuộc | Giữ bản kiểm kê. Đội bán hàng chọn những quy trình thực sự cần dựng lại như công việc riêng. |
| Lịch sử cũ hơn 24 tháng | Giữ ID gốc, thời gian, nội dung và liên kết có thể tra cứu | Lưu chỉ đọc, giới hạn quyền truy cập và xác nhận thời hạn lưu với chủ dữ liệu. |

**Các điểm dễ sai khi nhập:**

- **Option set → picklist.** Chuyển mã nguồn qua bảng quy đổi đã được sales DK duyệt. Đối chiếu Opportunity Stage theo business process của org đích, đưa mã lạ vào danh sách lỗi.
- **Quan hệ và chủ sở hữu.** Nhập Account trước, gắn Account cha ở lượt sau, rồi nhập Contact, Opportunity và hoạt động. Dùng mã Dynamics để nối sang ID Salesforce. Lập bảng user/team nguồn → user Salesforce có quyền, phân công người chịu trách nhiệm cho hồ sơ của user đã nghỉ hoặc thiếu ánh xạ. Các trường `Legacy_*__c` là External ID đề xuất, cần cấu hình trong org đích; chạy lại theo khóa này hoặc theo sổ đối soát với Activity.
- **Khách trùng.** Chuẩn hóa số theo [quy tắc OneOrder](../customer-phone.md), so cùng tên, địa chỉ hoặc mã doanh nghiệp. Số giống nhau là tín hiệu để rà soát vì nhiều công ty có thể dùng chung tổng đài. Khi sales DK xác nhận gộp, ánh xạ tất cả ID cũ về Account giữ lại để Contact và lịch sử vẫn đi đúng khách. [Chuẩn bị CSV và quan hệ Salesforce](https://help.salesforce.com/s/articleView?id=Considerations-to-prepare-csv-file-to-import-update-in-Salesforce&language=en_US&type=1)

## C2. Công cụ và định dạng

| Hướng | Công cụ | Định dạng và trường hợp dùng |
| --- | --- | --- |
| Xuất Dynamics | Dataverse Web API | OData v4, JSON. Dùng phân trang và lọc cột/phạm vi, lưu raw extract và chuẩn hóa thành CSV cho lượt nhập. Phù hợp với trích xuất lặp được và bản thay đổi cuối. [Microsoft Learn](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/overview) |
| Xuất Dynamics | Export to Excel | `.xlsx`, hữu ích cho sales DK rà mẫu/ánh xạ thủ công. [Microsoft Learn](https://learn.microsoft.com/en-us/power-apps/user/export-excel-static-worksheet) |
| Xuất Dynamics | Azure Synapse Link for Dataverse | Đồng bộ bảng ra Azure Data Lake; chọn cấu hình xuất CSV cho bộ dữ liệu lớn, kiểm tra chế độ xuất và kiểu bảng của môi trường DK. [Microsoft Learn](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/azure-synapse-link-data-lake) |
| Nạp Salesforce | Data Import Wizard | CSV, tối đa **50.000 bản ghi/lần**, phù hợp thử Account/Contact. Phạm vi đối tượng cần kiểm tra cho mỗi lượt. [Salesforce](https://help.salesforce.com/s/articleView?id=import_which_data_import_tool.htm&type=5) |
| Nạp Salesforce | Data Loader | CSV, cấu hình Bulk API 2.0 được. Có kết quả thành công/lỗi để đối soát, dùng được cho Task/Event. [Salesforce Data Loader](https://developer.salesforce.com/tools/data-loader) · [Cấu hình Data Loader](https://help.salesforce.com/s/articleView?id=configuring_the_data_loader.htm&type=0) |
| Nạp Salesforce | Bulk API 2.0 | Job nhập CSV bất đồng bộ. Tạo job theo đối tượng, lưu job ID và file kết quả thành công/lỗi để chạy lại có kiểm soát. [Salesforce](https://developer.salesforce.com/docs/platform/api-asynch/guide/bulk-api-2-0-ingest.html) |

- **Dataverse:** mặc định **6.000 request/5 phút/người dùng/máy chủ web** theo cửa sổ trượt, còn có giới hạn thời gian xử lý và số request đồng thời. Web API trả `429` kèm `Retry-After` tính bằng giây. Giảm song song và dùng thời gian chờ đó cho lần thử lại. [Microsoft Learn](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/api-limits)
- **Salesforce:** nguồn chính thức xác nhận hạn mức là tổng của cả org trong cửa sổ trượt **24 giờ**. Ví dụ Enterprise có mức cơ sở **100.000** cộng phần tăng theo loại/số license và add-on. Developer Edition có **15.000**. Kiểm tra `DailyApiRequests` và hạn riêng của Bulk API 2.0 trên org trước mỗi đợt nạp. [Hạn mức API Salesforce](https://developer.salesforce.com/docs/platform/salesforce-app-limits-cheatsheet/guide/salesforce-app-limits-platform-api.html) · [Giám sát mức dùng](https://developer.salesforce.com/blogs/2024/11/api-limits-and-monitoring-your-api-usage) · [Hạn mức Bulk](https://developer.salesforce.com/docs/platform/api-asynch/guide/bulk-common-limits.html)

**Chọn công cụ:** dùng Excel/Wizard cho lượt thử Account/Contact trong giới hạn 50.000; dùng Dataverse Web API → CSV → Data Loader chạy Bulk API 2.0 cho migration nhiều đối tượng và bản cuối; nếu khảo sát cho thấy extract đầy đủ vượt cửa sổ chạy thử, dùng Synapse Link cho bản đầy đủ rồi giữ Web API cho phần phát sinh. Con số thực tế sẽ có sau khảo sát.

## C3. Lộ trình từ T1 tới T4

T là tháng tính từ ngày khởi động. T4 là mốc Salesforce dùng chính thức ở DK. Salesforce adapter của OneOrder là phần triển khai tiếp theo trong T4–T6. [Lộ trình Round 3](https://github.com/pumpowhat/OneOrder/issues/31)

| Bước và thời gian | Người chịu trách nhiệm | Đầu ra | Kiểm tra trước khi đi tiếp |
| --- | --- | --- | --- |
| 1. Khảo sát · đầu T1 | Admin Dynamics, chủ dữ liệu DK | Kiểm kê bảng, khối lượng theo trạng thái/tháng, deadline tắt hệ thống, quyền xuất | Xác nhận tổng bản ghi theo đối tượng, mẫu dữ liệu và thời điểm trích xuất |
| 2. Ánh xạ · cuối T1 | Admin Salesforce, sales DK, kỹ sư dữ liệu | Bảng trường, mã picklist, owner, thứ tự nạp, tiêu chí đưa vào lưu trữ | Sales DK duyệt mẫu từng đối tượng, kiểm tra trường bắt buộc và các ID tham chiếu |
| 3. Làm sạch · T2 | Kỹ sư dữ liệu, sales DK | CSV chuẩn hóa, bảng ID hợp nhất, danh sách lỗi và người xử lý | Đối soát tổng nguồn = chuyển + lưu trữ + lỗi + số dòng gộp, kiểm tra số điện thoại và cha-con |
| 4. Chạy thử sandbox · T3 | Admin Salesforce, QA, sales DK | Báo cáo nhập từng đối tượng, thời lượng, danh sách lỗi, runbook cutover | Kiểm tra truy xuất khách theo số, owner, Contact dưới Account, cơ hội mở và activity. Thử chạy lại một job và đối chiếu không phát sinh trùng |
| 5. Chuyển hẳn · trước mốc T4 | Chủ dự án DK, hai admin, sales lead | Dynamics chỉ đọc, snapshot cuối, nạp delta kể cả các thay đổi/xóa theo runbook, biên bản go/no-go | Đối chiếu số lượng và cấu hình quyền, thử nghiệp vụ bán hàng với người dùng. Nếu không đạt, dừng mở quyền ghi đích và dùng phương án quay lui đã duyệt trong cửa sổ chuyển đổi |
| 6. Lưu trữ và tắt Dynamics · T4 | Chủ dữ liệu DK, IT vận hành | Kho chỉ đọc, danh mục dữ liệu, quyền truy cập và biên bản ngừng Dynamics | Mở thử bản lưu, đối chiếu checksum và quyền, có xác nhận của đội bán hàng trước khi tắt |

| Rủi ro | Cách xử lý |
| --- | --- |
| Dữ liệu bẩn hoặc gộp nhầm khách | Duyệt mẫu với sales DK, giữ dấu vết các ID đã gộp, xử lý ngoại lệ trước cutover và đối soát sau nhập. |
| Dynamics tắt sớm | Chốt lịch ngừng với admin từ T1. Xuất snapshot đầy đủ và thử đọc lại ngay sau khảo sát; lưu ngoài Dynamics để có bản khôi phục. |
| Gián đoạn bán hàng ở cutover | Chạy thử, chọn thời điểm ít đơn, khóa ghi ngắn để lấy delta, chuẩn bị kênh nhận đơn tạm và giao một người quyết định go/no-go. Nếu buộc quay lui, giữ và đối soát các đơn nhận trong cửa sổ chuyển đổi. |
