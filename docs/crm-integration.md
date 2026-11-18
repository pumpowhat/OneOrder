# Tích hợp CRM (Round 3)

OneOrder đọc khách hàng từ CRM ở bước Review và ghi đơn đã xác nhận lên CRM khi Confirm. Mỗi nước dùng CRM nào được khai báo trong `data/rules.json`:

```json
"crm": { "DK": "salesforce", "SE": "none", "NO": "none" }
```

- `salesforce`: dùng Salesforce adapter.
- `none`: nước không có CRM. Nhân viên nhập tay tên và số điện thoại như trước, không có gì được đồng bộ.
- Nước không có trong danh sách cũng được coi là `none`.

**OneOrder không kết nối với Microsoft Dynamics 365.** Dữ liệu CRM của Đan Mạch được chuyển một lần từ Dynamics 365 sang Salesforce, tách riêng khỏi OneOrder (xem issue #31).

## Kiến trúc

| Thành phần | File | Vai trò |
| --- | --- | --- |
| Interface | `backend/crm/base.py` | `CustomerDirectory` gồm `find_customers(name, phone)` và `push_order(order)`. Có hai loại lỗi: `CrmTransientError` (nên thử lại) và `CrmPermanentError` (không nên thử lại). |
| Chấm điểm khớp khách | `backend/crm/matching.py` | Mọi adapter dùng chung phần này, nên cùng dữ liệu thì cho cùng gợi ý. |
| Mock | `backend/crm/mock.py` | Đọc `samples/crm/accounts.csv` và `contacts.csv`. Hai file này dùng tên cột của Data Import Wizard, nên cũng nạp thẳng được vào org thật. |
| Salesforce thật | `backend/crm/salesforce.py` | REST API, đăng nhập bằng OAuth 2.0 client credentials. |
| Chọn adapter theo nước | `backend/crm/registry.py` | `CrmRegistry.for_country("DK")`. Trong test, dùng `app.dependency_overrides[get_crm_registry]` để thay adapter. |

### Cách chấm điểm khớp khách

| Trường hợp | Điểm | `matched_on` |
| --- | --- | --- |
| Số điện thoại trùng với số của Account hoặc của một Contact | 0,90–1,00. Càng cao nếu tên cũng giống. | `phone` |
| Chỉ tên giống (token sort ratio ≥ 75, không tính hậu tố A/S, ApS, AB…) | Tối đa 0,85 | `name` |

- Số điện thoại vẫn được coi là trùng khi một bên thiếu mã nước (`33 12 45 78` khớp với `+45 33 12 45 78`).
- Kết quả chỉ là gợi ý. **Nhân viên luôn là người chọn khách**; OneOrder không tự liên kết khách và không tự tạo khách mới.

## Chạy ở chế độ mock (mặc định)

```bash
CRM_MODE=mock ./run-oneorder.sh start
```

Mock giữ các đơn đã ghi trong bộ nhớ cho đến khi tắt app. Muốn giả lập Salesforce bị lỗi khi test, thêm lỗi vào hàng đợi `failures` của adapter:

```python
directory.failures = [CrmTransientError("timeout")]
```

## Kết nối Salesforce Developer org thật

1. Tạo một Developer Edition org (miễn phí).
2. Trên đối tượng **Order**, tạo field `OneOrder_Id__c`: kiểu Text(36), bật **External ID** và **Unique**. Khi Confirm, OneOrder ghi Order theo kiểu upsert trên field này, nên gửi lại nhiều lần cũng không tạo bản ghi trùng.
3. Bật Orders cho org: Setup → Order Settings → Enable Orders.
4. Tạo **External Client App** (hoặc Connected App):
   - Bật OAuth, chọn scope `api`.
   - Bật **Client Credentials Flow** và chọn một Run As user có quyền đọc Account/Contact và ghi Order.
5. Nạp dữ liệu khách mẫu: Setup → Data Import Wizard → nạp `samples/crm/accounts.csv`, rồi nạp `contacts.csv` (liên kết theo cột `AccountName`).
6. Điền vào `.env` (không commit file này):

   ```bash
   CRM_MODE=live
   SF_LOGIN_URL=https://<my-domain>.my.salesforce.com
   SF_CLIENT_ID=...
   SF_CLIENT_SECRET=...
   ```

Ở chế độ live, adapter tìm theo số điện thoại bằng **SOQL `LIKE`** trên `Account.Phone`, `Contact.Phone` và `Contact.MobilePhone`. Mẫu tìm là 8 chữ số cuối, cho phép ký tự phân cách giữa các chữ số (`%3%3%1%2%4%5%7%8`). Tìm theo tên thì dùng SOSL trên các trường name. Sau đó điểm vẫn được chấm lại bằng `backend/crm/matching.py`.

Đã chạy thử trên Developer org ngày 18/11/2026: SOSL `IN PHONE FIELDS` không tìm ra số nào, dù viết theo định dạng nào, nên phần tìm theo số dùng SOQL. Mẫu `LIKE` có ký tự đại diện ở đầu sẽ quét toàn bảng; với org nhiều khách hàng cần đánh giá lại hiệu năng.

## Xử lý lỗi

| Lỗi từ Salesforce | Adapter trả về | Ý nghĩa |
| --- | --- | --- |
| Timeout, mất mạng | `CrmTransientError` | Thử lại sau |
| HTTP 429, 5xx | `CrmTransientError` (kèm `retry_after` nếu có header `Retry-After`) | Thử lại sau |
| HTTP 401 | Đăng nhập lại và thử thêm một lần. Vẫn lỗi thì `CrmPermanentError` | Sai thông tin xác thực |
| HTTP 400, 403, 404 | `CrmPermanentError` (kèm `errorCode`) | Dữ liệu hoặc cấu hình sai, thử lại cũng không được |

Khi Confirm, CRM lỗi không được chặn việc xác nhận đơn: đơn vẫn chuyển sang `confirmed`, còn phần đồng bộ được xử lý riêng (task D4).
