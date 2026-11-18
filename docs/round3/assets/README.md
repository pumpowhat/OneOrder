# Hình dùng cho slide Round 3

Đã chuẩn bị ngày **17/11/2026** từ số liệu trong phân công. Cả ba PNG có nền trắng, kích thước **1920 × 1080** (16:9), đã mở kiểm tra trực quan; có thể chèn trực tiếp vào slide của Nhật. Chưa có xác nhận B3 mới từ Nghĩa; nếu B3 thay đổi, cập nhật đầu vào và xuất lại hình trước buổi pitch.

| Hình | Nội dung | Nguồn chỉnh sửa |
|---|---|---|
| [budget-waterfall.png](budget-waterfall.png) | Cầu ngân sách, cắt đỏ nhạt, thêm xanh lá nhạt, tổng xám; đường nét đứt €535k | [CSV số liệu](budget-waterfall.csv), hàm `waterfall()` trong generator |
| [delivery-timeline.png](delivery-timeline.png) | Lộ trình T0–T12, hạng mục CRM màu xanh lá, mốc/đường T4, Na Uy sang năm 2 | [JSON số liệu](delivery-timeline.json), hàm `timeline()` trong generator |
| [architecture-before-after.png](architecture-before-after.png) | Trước và sau đặt cạnh nhau; viền xanh cho khớp khách/CRM adapter/Salesforce; Dynamics nét đứt, chỉ migration một lần | [Sơ đồ draw.io có thể chỉnh sửa](architecture-before-after.drawio) |

## Các số phải giữ nhất quán

Ngân sách tính bằng nghìn EUR:

```text
764,5 − 162 − 72 − 40,5 − 33,5 − 27 + 81 + 22,5 = 533
```

Các khoản cắt/hoãn cộng **€335k**; migration và adapter cộng **€103,5k**; giảm ròng **€231,5k**. Trần chính xác sau cắt 30% là `764,5 × 70% = 535,15`; theo đề bài hình dùng đường làm tròn **€535k**, dư **€2k** (so với trần chính xác dư €2,15k). Hai cột tổng đều bắt đầu ở 0, các cột thay đổi nối theo tổng lũy kế.

Timeline dùng tháng tương đối, chưa gắn ngày lịch: pilot SE T0–T3; go-live SE T3–T6; migration DK T1–T4; Salesforce DK hoạt động tại T4; adapter T4–T6; go-live DK T6–T12. Dòng Na Uy có gạch chéo và nhãn hoãn; không biểu thị một hạng mục đang triển khai trong năm 1.

Sơ đồ thể hiện **kiến trúc mục tiêu Round 3**, không phải xác nhận backend CRM đã được triển khai. ERP các nước vẫn là nguồn tồn kho/giữ hàng; rollout Na Uy hoãn sang năm 2. Tại Review, Salesforce chỉ gợi ý khách, nhân viên chốt; tại Confirm, CRM lỗi vẫn cho xác nhận thành công và chuyển Pending sync để gửi lại. OneOrder không kết nối Dynamics.

## Tạo lại hình

Từ thư mục gốc repository, dùng môi trường dành cho biên soạn:

```powershell
python -m pip install matplotlib pillow
python scripts/round3/visuals/generate_assets.py
```

Đã tạo biểu đồ bằng matplotlib 3.11.2, font Inter có sẵn tại `docs/report/fonts/`. Các thư viện vẽ chỉ phục vụ xuất tài liệu, không được thêm vào `requirements.txt` của ứng dụng. Generator xuất lại cả hai biểu đồ, dữ liệu đi kèm và nguồn draw.io; chỉnh số trong generator rồi chạy lại (CSV/JSON là đầu ra, không phải đầu vào).

PNG kiến trúc được xuất bằng **draw.io v32.6.10 thực**, chạy cục bộ từ gói `draw.war` của [release chính thức](https://github.com/jgraph/drawio/releases/tag/v32.6.10). File XML được tải vào renderer trên `127.0.0.1`, không được gửi tới dịch vụ export bên ngoài. Trình xuất Playwright chặn mọi request ngoài localhost; PNG chứa XML để có thể mở lại và chỉnh sửa bằng draw.io.

Cách xuất thủ công: mở `.drawio` bằng draw.io Desktop, chọn **File → Export as → PNG**, nền trắng, toàn trang 1920 × 1080, không có border. Cách xuất bằng script:

```powershell
# Giải nén draw.war như ZIP vào một thư mục riêng; trỏ tới nơi có index.html.
# Cài Playwright trong môi trường biên soạn, hoặc dùng Node packages có sẵn.
$env:DRAWIO_WEBAPP_DIR = 'C:\duong-dan\drawio-webapp'
node scripts/round3/visuals/export_drawio.cjs
```

Script dùng [giao thức embed/export chính thức của draw.io](https://www.drawio.com/docs/reference/embed-mode/#export), phục vụ renderer offline qua localhost. Có thể đặt `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` nếu dùng Chromium đã có trên máy.

Sau khi đổi số hoặc bố cục, mở lại cả ba PNG và kiểm tra: đủ nhãn/tiếng Việt, không chồng chữ, tổng €533k, trần €535k, đường T4 và mũi tên migration chỉ từ Dynamics sang Salesforce. Việc gửi hình cho Nhật chưa thực hiện; các file đã sẵn sàng để bàn giao qua PR.
