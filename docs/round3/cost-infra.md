# Round 3 · Chi phí cloud, AI và bản đồ

Ước tính đơn giá công khai ngày **18/11/2026**. Giá cloud tính bằng EUR. Giá AI và bản đồ tính theo **1 EUR = 1,0989 USD** theo ECB ngày 17/11/2026, cùng tỷ giá với bảng license của nhóm. Tất cả số tiền dưới đây chưa gồm thuế. [ECB](https://www.ecb.europa.eu/stats/exchange/eurofxref/shared/pdf/2026/11/20261117.pdf) · [Issue #31](https://github.com/pumpowhat/OneOrder/issues/31)

## Cloud trong 12 tháng

**Giả định dùng để review:** Azure **North Europe (Ireland)**, một vùng, giảm từ ba còn hai môi trường: production và staging. Đây là cấu hình ước tính cho MVP, cần đo tải trước khi chọn kích cỡ production. App và DB ở hai môi trường dùng tài nguyên tách riêng. [Danh sách vùng Azure](https://learn.microsoft.com/en-us/azure/reliability/regions-list)

Chọn pay-as-you-go, North Europe và các mức sử dụng dưới đây trong [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/). Calculator công khai tải bảng giá bằng JavaScript và chưa tạo được liên kết báo giá chia sẻ trong lần tra này. Bảng ghi đơn giá EUR đã đối chiếu từ [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices), lọc `armRegionName eq 'northeurope'`, `priceType eq 'Consumption'` và `currencyCode='EUR'`, để nhóm có thể nhập lại và kiểm tra từng dòng.

| Hạng mục | Đơn giá EUR và cấu hình | Prod €/tháng | Staging €/tháng |
| --- | --- | ---: | ---: |
| Azure Container Apps Consumption | €0,000022/vCPU-giây và €0,000003/GiB-giây (Standard Active). Prod 1 vCPU / 2 GiB × 730 giờ; staging 0,5 vCPU / 1 GiB × 160 giờ, scale về 0 ngoài giờ. Tính theo giờ active, chưa trừ quota compute miễn phí. Giả định tổng HTTP requests ≤ 2 triệu/tháng, nằm trong quota miễn phí. [Container Apps](https://azure.microsoft.com/en-us/pricing/details/container-apps/) | 73,58 | 8,06 |
| PostgreSQL Flexible Server | B2ms, €0,12927/giờ cho mỗi máy × 730 giờ. Storage €0,11356/GB-tháng, 64 GB prod và 32 GB staging. Backup tự động trong dung lượng được cấp; giả định dung lượng backup không vượt mức bao gồm. [PostgreSQL](https://azure.microsoft.com/en-us/pricing/details/postgresql/flexible-server/) | 101,63 | 98,00 |
| Blob Storage Hot LRS | Prod: 100 GB, 50.000 lượt ghi, 100.000 lượt đọc/tháng. Staging: 10 GB, 10.000 lượt ghi, 20.000 lượt đọc/tháng. Giá €0,01975/GB-tháng, €0,044885/10.000 ghi và €0,003591/10.000 đọc. [Blob Storage](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/) | 2,24 | 0,25 |
| Azure Monitor / Log Analytics | 20 GB prod và 5 GB staging mỗi tháng, dự trù toàn bộ ở mức €2,47767/GB Analytics Logs, chưa trừ lượng miễn phí. Dùng kỳ giữ log mặc định, cảnh báo cơ bản. [Azure Monitor](https://azure.microsoft.com/en-us/pricing/details/monitor/) | 49,55 | 12,39 |
| **Tổng (làm tròn từ số gốc)** | **Prod + staging: €345,71/tháng, €4.148,53/năm** | **227,01** | **118,70** |

Mức cơ sở **thấp hơn €18.000/năm khoảng €13.851**. Lý do chính là một vùng, staging chạy container theo giờ, DB nhỏ và giả định dữ liệu/log ở mức pilot. Tách riêng khỏi ước tính: HA đa vùng, egress vượt mức cơ sở, mạng riêng, hỗ trợ trả phí, công vận hành và phục hồi thảm họa. Giữ chênh lệch như dự phòng cho tới khi có đo tải, yêu cầu SLA và báo giá thực tế. DB staging chiếm gần hết chi phí môi trường này vì giả định chạy cả tháng.

**So sánh địa điểm pilot:** cùng cấu hình ở **Sweden Central** khoảng **€267,01/tháng, €3.204,07/năm**, thấp hơn North Europe khoảng €944/năm. B2ms ở Sweden Central là €0,071457/giờ, disk €0,122896/GB-tháng, Blob Hot LRS €0,016518/GB-tháng và Analytics Logs €2,684142/GB. Đơn giá container và lượt đọc/ghi Blob trong phép tính giữ nguyên. North Europe vẫn là vùng cơ sở của dự toán để review. [Azure Retail Prices API, vùng `swedencentral`](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)

## AI API và bản đồ

`AI_MODEL` để trống trong [`.env.example`](../../.env.example), nên code dùng `gemini-3.5-flash` nếu không có override. Cấu hình chạy và ghi fixture của demo đặt **`gemini-3.5-flash-lite`**. Bảng cơ sở dùng đúng model demo và thêm kịch bản dùng model mặc định để nhóm thấy mức chênh. Giá API chuẩn Flash-Lite là **$0,30/triệu token đầu vào** và **$2,50/triệu token đầu ra** (gồm token suy luận). Giá tham chiếu của Flash trên Google Cloud toàn cầu là **$1,50 / $9,00**. [Code chọn model](../../backend/services/intake/gemini_client.py) · [Giá Gemini API](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite) · [Giá tham chiếu Google Cloud](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing)

**Giả định cho một đơn:** 3.000 token đầu vào và 1.500 token đầu ra, theo quy mô mẫu email/PDF một trang, khoảng 5 dòng, cộng prompt, schema, suy luận và các lượt khớp SKU nếu phát sinh. Đây là mức dự trù. Đo đầu vào, đầu ra và số lượt gọi theo từng định dạng trong pilot để thay giả định. Công thức Flash-Lite: `số đơn × (3.000 × 0,30 + 1.500 × 2,50) / 1.000.000 / 1,0989`.

Code hiện tại tra bảng khoảng cách OSRM đã tính sẵn, nên đường chạy demo không tính bản đồ theo từng đơn. Để so cùng phạm vi với dự toán €12.000, bảng thêm một kịch bản dịch vụ bản đồ trả phí: **2 phần tử ma trận tuyến đường/đơn**, lưu lượng đều theo tháng, 10.000 phần tử miễn phí mỗi tháng và **$5/1.000** ở bậc kế tiếp. Chốt nhà cung cấp và số tuyến thật từ pilot. [Script OSRM](../../scripts/precompute_drive_times.py) · [Giá Google Route Matrix Essentials](https://developers.google.com/maps/billing-and-pricing/pricing)

| Đơn/năm | AI Flash-Lite €/năm | Maps €/năm | **Flash-Lite + Maps €/năm** | Flash + Maps €/năm (tham chiếu) |
| ---: | ---: | ---: | ---: | ---: |
| 20.000 | 84,63 | 0,00 | **84,63** | 327,60 |
| 50.000 | 211,58 | 0,00 | **211,58** | 819,00 |
| 100.000 | 423,15 | 364,00 | **787,15** | 2.002,00 |

Ở 100.000 đơn/năm, kịch bản Flash-Lite cộng Maps **thấp hơn €12.000 khoảng €11.213**. Chênh lệch đến từ token/đơn thấp, số tuyến tra ít và quota miễn phí bản đồ. Đơn nhiều trang, nhiều lượt khớp, retry hoặc tải dồn theo tháng sẽ nâng chi phí. Dùng mức €12.000 làm ngân sách đối chiếu của pitch cho tới khi nhóm duyệt lại dự toán chung.
