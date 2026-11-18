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

## API cho bước Review (E1)

| Endpoint | Mô tả |
| --- | --- |
| `GET /api/orders/{id}/customer-candidates?name=&phone=` | Gợi ý khách từ mọi nước đang bật CRM. Bỏ trống `name`/`phone` thì dùng giá trị đang lưu trên đơn. Trả `{crm, countries, candidates, ambiguous, error}`. |
| `PATCH /api/orders/{id}` có `crm_account_id`, `crm_contact_id` | Liên kết khách đã chọn, hoặc gửi `null` để bỏ liên kết. ID phải đúng dạng Salesforce (15 hoặc 18 ký tự). Gửi Contact mà không có Account thì trả 422. |

- `crm == "none"`: không nước nào bật CRM. Giao diện ẩn toàn bộ phần CRM.
- `ambiguous == false` chỉ khi có **đúng một** khách khớp số điện thoại. Chỉ khớp theo tên, hoặc nhiều khách dùng chung một số, thì là `true` để giao diện nhắc nhân viên kiểm tra kỹ.
- `error`: CRM lỗi thì endpoint vẫn trả 200, kèm lý do ở đây. Nhân viên nhập tay khách như bình thường.

**Khi nào liên kết bị bỏ tự động** (khi `PATCH` hoặc duyệt đơn mà không chọn lại khách):
- Tên khách đổi. Đổi chữ hoa/thường hay khoảng trắng không tính. Đổi hậu tố pháp nhân thì có tính, vì "A/S" và "ApS" là hai pháp nhân khác nhau.
- Số điện thoại đổi sang một số khác. Chỉ đổi định dạng (`+45 33 12 45 78` thành `+4533124578`) thì không tính.

Mỗi lần liên kết hoặc bỏ liên kết đều ghi audit log với action `link_crm_account` hoặc `unlink_crm_account`, kèm ID trước và sau.

## Đồng bộ đơn khi Confirm (D4)

Confirm luôn xác nhận đơn và giữ hàng trong ERP trước, trong một transaction riêng. Sau đó OneOrder mới ghi đơn lên CRM. **CRM lỗi không bao giờ làm Confirm thất bại.**

| `crm_sync.status` | Khi nào | Tiếp theo |
| --- | --- | --- |
| `not_applicable` | Nước của công trường không có CRM (`reason: crm_disabled`), hoặc đơn chưa liên kết khách CRM (`reason: no_account`) | Không làm gì thêm |
| `synced` | CRM đã nhận Order. `crm_record_id` là ID của Order trên Salesforce. | Xong |
| `pending` | Lỗi tạm thời (timeout, 429, 5xx) | Worker tự thử lại sau 30 giây, rồi sau 120 giây, hoặc sau `Retry-After` nếu Salesforce yêu cầu lâu hơn |
| `failed` | CRM từ chối Order (4xx), hoặc đã thử đủ 3 lần | Nhân viên bấm Retry |

- `POST /api/orders/{id}/crm-sync/retry` nhận đơn đang `pending` hoặc `failed`, bắt đầu lại một lượt 3 lần thử, và trả khối `crm_sync` mới. Các trạng thái khác trả 409.
- `GET /api/orders` có thêm `crm_sync_status` ở mỗi dòng, để Dashboard đếm số đơn đang chờ đồng bộ.
- Audit log ghi `crm_sync` khi thành công, `crm_sync_failed` khi lỗi (kèm lần thử và thời điểm thử lại), `crm_sync_retry` khi nhân viên bấm Retry. Trường hợp `not_applicable` không ghi audit, vì không có lần gọi CRM nào.
- Worker thử lại chạy cùng app. Tắt bằng `CRM_SYNC_WORKER=0`, đổi chu kỳ bằng `CRM_SYNC_INTERVAL` (mặc định 15 giây). Bộ test luôn tắt worker và ép `CRM_MODE=mock` (`tests/conftest.py`).

Order ghi lên Salesforce: `AccountId` (và `ShipToContactId` nếu có), `EffectiveDate` là ngày Confirm, `Status = Draft`, `OneOrder_Id__c` là mã đơn. `Description` gồm khách hàng, công trường, ngày yêu cầu, ngày dự kiến (P50), ngày cam kết (P90) và các dòng hàng.

## Giả lập Salesforce bị lỗi khi demo (`CRM_MOCK_FAIL`)

Chỉ dùng được với `CRM_MODE=mock`. Với org thật, endpoint trả 409, nên không thể giả lập lỗi trên CRM thật.

| Chế độ | Ảnh hưởng |
| --- | --- |
| `search` | Gợi ý khách ở bước Review báo lỗi (`error`). Nhân viên nhập tay khách. |
| `transient` | Ghi Order bị timeout: `crm_sync` chuyển `pending`, rồi tự thử lại khi hết lỗi. |
| `permanent` | Salesforce từ chối Order: `crm_sync` chuyển `failed`, phải bấm Retry. |

Có hai cách bật:
- **Lúc khởi động:** `CRM_MOCK_FAIL=transient ./run-oneorder.sh start`. Có thể ghép nhiều chế độ, ví dụ `search,transient`.
- **Lúc app đang chạy:** mở `http://localhost:8000/docs`, chọn `PUT /api/crm/mock-failure`, hoặc gọi `curl`:

  ```bash
  curl -X PUT localhost:8000/api/crm/mock-failure -H 'Content-Type: application/json' -d '{"modes": ["transient"]}'
  curl -X PUT localhost:8000/api/crm/mock-failure -H 'Content-Type: application/json' -d '{"modes": []}'   # hết lỗi
  curl localhost:8000/api/crm/status
  ```

**Kịch bản demo "CRM sập mà đơn vẫn chạy" (khoảng 1 phút):**
1. Bật `transient`.
2. Mở đơn email Hoffmann, chọn khách từ gợi ý, duyệt, lập kế hoạch, Confirm. Đơn ở trạng thái `confirmed`, đã giữ hàng, badge hiện *Pending sync*.
3. Tắt lỗi bằng `{"modes": []}`.
4. Bấm **Retry sync**: badge đổi thành *Synced to Salesforce*. Nếu không bấm, worker tự đồng bộ trong khoảng 30–45 giây (30 giây chờ sau lần lỗi đầu, cộng chu kỳ worker 15 giây).

Trạng thái lỗi giả lập chỉ lưu trong bộ nhớ của mock, khởi động lại app là mất. Giá trị ban đầu lấy lại từ `CRM_MOCK_FAIL`.
