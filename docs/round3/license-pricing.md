# Giá license CRM — Round 3

Ngày tra cứu: **17/11/2026** (Asia/Saigon). Giá niêm yết USD trên trang US,
trước thuế, chiết khấu, hỗ trợ và dịch vụ triển khai; 50 người dùng trong 12 tháng.
Đây là phép so sánh theo giả định Dynamics Enterprise đang trả đúng giá niêm yết,
chưa phải hóa đơn hay báo giá cho Company A tại Đan Mạch.

## Tỷ giá và cách tính

[ECB, USD theo EUR](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html),
tra ngày 17/11/2026, hiển thị ngày tỷ giá **17/11/2026: 1 EUR = 1,0989 USD**.
Dùng `EUR = USD / 1.0989`, tức 1 USD ≈ 0,91000091 EUR.
Tổng năm = giá USD/tháng × 50 × 12; quy đổi từ tổng gốc rồi làm tròn 2 chữ số.
Giá EUR dưới đây là quy đổi để lập kế hoạch, không phải giá bán EUR của hãng.

## Bảng giá

| Sản phẩm | Gói | USD/user/tháng, trả năm | EUR/user/tháng quy đổi | 50 user × 12 tháng (USD) | 50 user × 12 tháng (EUR) | Nguồn chính thức | Ngày tra cứu |
|---|---|---:|---:|---:|---:|---|---|
| Dynamics 365 Sales | Professional | 65 | 59,15 | 39.000 | 35.490,04 | [Microsoft](https://www.microsoft.com/en-us/dynamics-365/products/sales/pricing) | 17/11/2026 |
| Dynamics 365 Sales | Enterprise | 105 | 95,55 | 63.000 | 57.330,06 | [Microsoft](https://www.microsoft.com/en-us/dynamics-365/products/sales/pricing) | 17/11/2026 |
| Dynamics 365 Sales | Premium | 150 | 136,50 | 90.000 | 81.900,08 | [Microsoft](https://www.microsoft.com/en-us/dynamics-365/products/sales/pricing) | 17/11/2026 |
| Salesforce Sales Cloud | Starter Suite | 25 | 22,75 | 15.000 | 13.650,01 | [Salesforce](https://www.salesforce.com/sales/pricing/) | 17/11/2026 |
| Salesforce Sales Cloud | Pro Suite | 100 | 91,00 | 60.000 | 54.600,05 | [Salesforce](https://www.salesforce.com/sales/pricing/) | 17/11/2026 |
| Salesforce Sales Cloud | Core | 195 | 177,45 | 117.000 | 106.470,11 | [Salesforce](https://www.salesforce.com/sales/pricing/) | 17/11/2026 |
| Salesforce Sales Cloud | Advanced | 395 | 359,45 | 237.000 | 215.670,22 | [Salesforce](https://www.salesforce.com/sales/pricing/) | 17/11/2026 |
| Salesforce Sales Cloud | Max | 550 | 500,50 | 330.000 | 300.300,30 | [Salesforce](https://www.salesforce.com/sales/pricing/) | 17/11/2026 |

Starter cho phép trả tháng hoặc năm cùng mức niêm yết; bảng chọn trả năm.
Các gói Salesforce còn lại và ba gói Dynamics trên đều ghi trả theo năm.

**Kết luận theo license cơ bản:** Salesforce Pro Suite rẻ hơn Dynamics Enterprise
**3.000 USD ≈ 2.730,00 EUR/năm** cho 50 user (tính chênh lệch trước khi làm tròn).

## Phụ phí API ảnh hưởng trực tiếp đến OneOrder

OneOrder cần API để tìm khách và ghi đơn. [Bảng giá Salesforce](https://www.salesforce.com/sales/pricing/)
ghi Web Services API của Pro Suite là **thêm 25 USD/user/tháng**; [tài liệu add-on chính thức,
trang 7](https://www.salesforce.com/en-us/wp-content/uploads/sites/4/documents/pricing/all-add-ons.pdf?bc=OTH)
xác nhận REST/SOAP/Bulk/Streaming và trả theo năm (tra 17/11/2026).

Nếu áp phụ phí cho cả 50 user: API = 15.000 USD ≈ 13.650,01 EUR/năm;
Pro Suite + API = **75.000 USD ≈ 68.250,07 EUR/năm**, tức **đắt hơn Dynamics
Enterprise 12.000 USD ≈ 10.920,01 EUR/năm**. Cần báo giá xác nhận số license
chịu phụ phí, tài khoản tích hợp và quyền đối với đối tượng Order/External ID trước khi chốt gói;
Developer org dùng demo không chứng minh quyền license production.

Giả định lập ngân sách hiện tại: license CRM thuộc chi phí vận hành của DK;
€81k migration và €22,5k adapter là chi phí dự án. Nếu license cũng phải nằm trong
€535k, phải duyệt lại B3: phần dư €2k của kế hoạch €533k không đủ cho cả
€68,25k license/API hoặc phần tăng €10,92k. Không dùng tiết kiệm license cơ bản
để tuyên bố tích hợp đã được tài trợ.
