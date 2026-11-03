# Đặc tả Định dạng Dữ liệu & ERP Giả lập (OneOrder MVP)

Tài liệu này mô tả chi tiết cấu trúc các file dữ liệu mẫu nằm trong thư mục `data/` và đặc tả tích hợp 3 hệ thống ERP giả lập tại Đan Mạch (DK), Thụy Điển (SE) và Na Uy (NO).

---

## 1. Tổng quan các tệp dữ liệu (`data/`)

| Tệp tin | Định dạng | Số lượng | Mục đích sử dụng |
|---|---|---|---|
| `data/catalog.json` | JSON | 221 sản phẩm | Danh mục sản phẩm chuẩn hóa toàn tập đoàn, dùng cho bộ đối khớp danh mục (RapidFuzz) và tính tải trọng/cẩu. |
| `data/warehouses.json` | JSON | 15 kho | Mạng lưới kho bãi (Central DC và Chi nhánh Proff) tại DK, SE, NO kèm tọa độ địa lý. |
| `data/sites.json` | JSON | 10 công trường | Danh sách các dự án/công trường xây dựng B2B mẫu tại Bắc Âu có tọa độ để tính ETA. |
| `data/inventory_dk.csv` | CSV | 1,105 dòng | Dữ liệu tồn kho ERP Đan Mạch (định dạng CSV truyền thống, tiêu đề cột tiếng Đan Mạch). |
| `data/inventory_se.json` | JSON | 1,105 bản ghi | Dữ liệu tồn kho ERP Thụy Điển (định dạng JSON, tên trường tiếng Thụy Điển). |
| `data/inventory_no.json` | JSON | 1,105 bản ghi | Dữ liệu tồn kho ERP Na Uy (định dạng JSON, tên trường tiếng Anh chuẩn). |

---

## 2. Chi tiết cấu trúc từng tệp

### 2.1. Danh mục sản phẩm (`data/catalog.json`)

Mỗi sản phẩm trong danh mục được thiết kế tương thích hoàn toàn với schema của [`backend/services/matching/catalog.py`](../backend/services/matching/catalog.py):

```json
{
  "sku": "GYP-13-2400",
  "name": "Gipsplade standard 13mm 1200x2400",
  "category": "drywall",
  "unit": "stk",
  "weight_kg": 25.5,
  "requires_crane": false,
  "aliases": [
    "gipsplade 13mm",
    "gipsskiva normal 13mm",
    "gipsplate standard 13mm",
    "standard plasterboard 13mm",
    "gipskarton 13mm"
  ]
}
```

- **`sku`** *(string)*: Mã định danh sản phẩm duy nhất.
- **`name`** *(string)*: Tên thương mại chính thức (thường bằng tiếng Đan Mạch / chuẩn Bắc Âu).
- **`category`** *(string)*: Phân loại ngành hàng (`drywall`, `timber`, `insulation`, `masonry`, `steel`, `roofing`, `fasteners`, `plumbing`, `chemicals`, `site_equipment`, `electrical`, `tools`).
- **`unit`** *(string)*: Đơn vị tính (`stk`, `m`, `m2`, `pk`, `sæk`, `rl`, `spand`, `dunk`, `sæt`, `pose`).
- **`weight_kg`** *(float)*: Trọng lượng một đơn vị (kg), dùng để tính tổng khối lượng đơn hàng và chọn phương tiện (xe tải nhỏ / xe tải lớn / xe cẩu).
- **`requires_crane`** *(boolean)*: `true` nếu mặt hàng cồng kềnh/nặng (dầm thép, bigbag cát 1 tấn, tấm rionet lớn) bắt buộc phải điều xe tải gắn cẩu (crane truck).
- **`aliases`** *(array of strings)*: Tập hợp các tên gọi thay thế bằng tiếng Đan Mạch, Thụy Điển, Na Uy và Anh để thuật toán fuzzy matching bắt được khi nhà thầu gõ sai chính tả hoặc gõ theo ngôn ngữ địa phương.

---

### 2.2. Mạng lưới kho bãi (`data/warehouses.json`)

Bao gồm 15 kho được phân bổ tại 3 quốc gia. Mỗi quốc gia gồm **1 Central DC** (kho tổng quy mô lớn) và **4 Chi nhánh Proff** (chi nhánh phục vụ nhà thầu địa phương):

- **Đan Mạch (DK)**:
  - `DK-DC-01`: Taastrup Central Logistics Hub (DC trung tâm vùng Copenhagen)
  - `DK-BR-01`: København Sydhavn Proff Branch
  - `DK-BR-02`: Aarhus Havn Byggecenter
  - `DK-BR-03`: Odense Erhvervsafdeling
  - `DK-BR-04`: Aalborg Syd Trælast
- **Thụy Điển (SE)**:
  - `SE-DC-01`: Jönköping Nordic Central Distribution Center (DC trung tâm Bắc Âu)
  - `SE-BR-01`: Stockholm Globen Proffscenter
  - `SE-BR-02`: Göteborg Hisingen Byggvaruhus
  - `SE-BR-03`: Malmö Hamn Proffsfilial
  - `SE-BR-04`: Uppsala Fyrislund Byggdepå
- **Na Uy (NO)**:
  - `NO-DC-01`: Vestby Central WMS Hub (DC trung tâm vùng Đông Na Uy)
  - `NO-BR-01`: Oslo Alnabru Proffsenter
  - `NO-BR-02`: Bergen Minde Byggevarehus
  - `NO-BR-03`: Trondheim Sluppen Proffavdeling
  - `NO-BR-04`: Stavanger Forus Byggsenter

**Cấu trúc một kho:**
```json
{
  "code": "DK-DC-01",
  "name": "Taastrup Central Logistics Hub",
  "country": "DK",
  "type": "dc",
  "address": "Kuldyssen 14, 2630 Taastrup",
  "latitude": 55.6521,
  "longitude": 12.3012,
  "contact_email": "dc-taastrup@oneorder.dk"
}
```

---

### 2.3. Công trường mẫu (`data/sites.json`)

Gồm 10 công trường xây dựng tiêu biểu (4 DK, 3 SE, 3 NO) có tọa độ GPS chính xác và cờ `crane_accessible` để kiểm tra khả năng vào bãi của xe cẩu:

- `SITE-DK-01`: Nordhavn Kronløbsøen Residential Tower (København)
- `SITE-DK-02`: Carlsberg Byen Karré 11 Boliger (København)
- `SITE-DK-03`: Aarhus Nyt Universitetshospital Udvidelse (Aarhus)
- `SITE-DK-04`: Odense Havnebad & Erhvervskvarter (Odense)
- `SITE-SE-01`: Hagastaden Life Science Kvarter (Stockholm)
- `SITE-SE-02`: Karlatornet Lindholmen Skyscraper (Göteborg)
- `SITE-SE-03`: Malmö Live Nyhavn Kvarteret (Malmö)
- `SITE-NO-01`: Bjørvika Barcode Finanssenter (Oslo)
- `SITE-NO-02`: Bergen Bybane Fyllingsdalen Verksted (Bergen)
- `SITE-NO-03`: Trondheim Solsiden Brygge Boliger (Trondheim)

---

## 3. Ba định dạng tồn kho gốc & Bảng ánh xạ Adapter

Nhằm phản ánh bài toán phân mảnh hệ thống do lịch sử M&A của Công ty A, dữ liệu tồn kho được lưu ở 3 định dạng hoàn toàn khác nhau:

### 3.1. Đan Mạch (`data/inventory_dk.csv`)
Định dạng **CSV**, phân cách bằng dấu phẩy, tiêu đề cột bằng tiếng Đan Mạch:
```csv
varenr,lager_kode,beholdning,reserveret,enhed
GYP-13-2400,DK-DC-01,2320,116,stk
GYP-13-2400,DK-BR-01,135,10,stk
```

### 3.2. Thụy Điển (`data/inventory_se.json`)
Định dạng **JSON**, tên thuộc tính tiếng Thụy Điển nguyên bản:
```json
[
  {
    "artikelnr": "GYP-13-2400",
    "lagerplats": "SE-DC-01",
    "saldo": 1477,
    "reserverat": 177,
    "enhet": "stk"
  }
]
```

### 3.3. Na Uy (`data/inventory_no.json`)
Định dạng **JSON**, tên thuộc tính tiếng Anh tiêu chuẩn:
```json
[
  {
    "sku": "GYP-13-2400",
    "warehouse_id": "NO-DC-01",
    "quantity_on_hand": 2912,
    "reserved_quantity": 203,
    "unit": "stk"
  }
]
```

### 3.4. Bảng ánh xạ về Mô hình Thống nhất OneOrder (`UnifiedStockItem`)

Lớp ERP Adapter tại [`backend/erp/adapters.py`](../backend/erp/adapters.py) chuẩn hóa cả 3 định dạng về schema nội bộ chung:

| Thuộc tính thống nhất | Kiểu | Mô tả | DK (CSV) | SE (JSON) | NO (JSON) |
|---|---|---|---|---|---|
| `sku` | `str` | Mã sản phẩm | `varenr` | `artikelnr` | `sku` |
| `warehouse_id` | `str` | Mã kho lưu trữ | `lager_kode` | `lagerplats` | `warehouse_id` |
| `country` | `str` | Quốc gia (`DK`, `SE`, `NO`) | Tách từ mã kho | Tách từ mã kho | Tách từ mã kho |
| `quantity_on_hand` | `int` | Tồn kho thực tế trong kho | `beholdning` | `saldo` | `quantity_on_hand` |
| `reserved_quantity` | `int` | Số lượng đã giữ cho đơn khác | `reserveret` | `reserverat` | `reserved_quantity` |
| `available_quantity` | `int` | Số lượng còn khả dụng để bán | `beholdning - reserveret` | `saldo - reserverat` | `quantity_on_hand - reserved_quantity` |
| `unit` | `str` | Đơn vị tính | `enhed` | `enhet` | `unit` |

---

## 4. Kịch bản Demo Giao hàng Xuyên Biên Giới (Cross-border)

Để phục vụ kịch bản điều phối thông minh của OneOrder khi đơn hàng cần vật liệu hiếm, 8 sản phẩm chuyên dụng được thiết lập **tồn kho bằng 0 tại 2 quốc gia còn lại**:

| Mã SKU | Tên sản phẩm | Quốc gia có hàng | Kho lưu trữ chính | Đặc tính / Lý do điều phối |
|---|---|:---:|---|---|
| `TIM-SE-PINE45` | Svensk Furu Kärnvirke Norrland 45x195mm C30 | **SE** | `SE-DC-01`, `SE-BR-01` | Gỗ thông lõi phương Bắc chất lượng cao của Thụy Điển; công trường DK/NO đặt mua sẽ kích hoạt cross-border từ SE. |
| `STO-SE-GRANITE` | Bohuslän Granit Kantsten 1000x300x150mm | **SE** | `SE-DC-01`, `SE-BR-01` | Đá granite Bohuslän Thụy Điển, nặng 122kg, yêu cầu xe cẩu (`requires_crane: true`). |
| `ARM-BEAM-HEA200` | Stålbjælke HEA 200 S355J2 6m | **SE** | `SE-DC-01` | Dầm thép kết cấu nặng 254kg, chỉ lưu trữ ở kho trung tâm Thụy Điển, yêu cầu xe cẩu. |
| `ROOF-NO-SLATE` | Alta Skifer Takstein naturkant 300x400mm | **NO** | `NO-DC-01` | Đá phiến lợp mái tự nhiên vùng Alta Na Uy; kho DK và SE có số lượng = 0. |
| `CHM-NO-ARCTIC` | Hey'di Frostsikker Arktisk Membran 20kg | **NO** | `NO-DC-01`, `NO-BR-01` | Hóa chất chống thấm chuyên dụng vùng băng giá của Na Uy. |
| `INS-NO-ECOWOOL` | Glava Proff 34 Norsk Miljø Glassull 150mm | **NO** | `NO-DC-01` | Bông thủy tinh hiệu suất cao của Na Uy. |
| `BRK-DK-CPHRED` | Flensborg Mursten Rød Håndstrøget Historisk | **DK** | `DK-DC-01`, `DK-BR-01` | Gạch cổ Flensborg làm thủ công Đan Mạch phục vụ trùng tu; kho SE và NO có số lượng = 0. |
| `WIN-DK-VELUX78` | Velux Tagvindue GGL MK08 3-lags thermo | **DK** | `DK-DC-01` | Cửa sổ mái cao cấp xuất xứ Đan Mạch. |

---

## 5. Hướng dẫn sử dụng cho Backend (Nghĩa)

Backend có thể xây dựng adapter đọc 3 nguồn dữ liệu theo mẫu:

```python
import csv
from dataclasses import dataclass
import json
from pathlib import Path

@dataclass(frozen=True)
class UnifiedStockItem:
    sku: str
    warehouse_id: str
    country: str
    quantity_on_hand: int
    reserved_quantity: int
    available_quantity: int
    unit: str

# 1. Đọc CSV Đan Mạch
def load_dk_inventory(path="data/inventory_dk.csv") -> list[UnifiedStockItem]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            on_hand = int(r["beholdning"])
            res = int(r["reserveret"])
            items.append(UnifiedStockItem(
                sku=r["varenr"], warehouse_id=r["lager_kode"], country="DK",
                quantity_on_hand=on_hand, reserved_quantity=res,
                available_quantity=max(0, on_hand - res), unit=r["enhed"]
            ))
    return items

# 2. Đọc JSON Thụy Điển
def load_se_inventory(path="data/inventory_se.json") -> list[UnifiedStockItem]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        UnifiedStockItem(
            sku=e["artikelnr"], warehouse_id=e["lagerplats"], country="SE",
            quantity_on_hand=e["saldo"], reserved_quantity=e["reserverat"],
            available_quantity=max(0, e["saldo"] - e["reserverat"]), unit=e["enhet"]
        ) for e in data
    ]

# 3. Đọc JSON Na Uy
def load_no_inventory(path="data/inventory_no.json") -> list[UnifiedStockItem]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        UnifiedStockItem(
            sku=e["sku"], warehouse_id=e["warehouse_id"], country="NO",
            quantity_on_hand=e["quantity_on_hand"], reserved_quantity=e["reserved_quantity"],
            available_quantity=max(0, e["quantity_on_hand"] - e["reserved_quantity"]), unit=e["unit"]
        ) for e in data
    ]
```

### Tái sinh dữ liệu khi cần
Nếu cần sinh lại hoặc thay đổi số lượng, chạy:
```bash
python scripts/generate_mock_data.py
```
