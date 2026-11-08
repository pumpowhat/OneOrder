import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import openpyxl
from PIL import Image, ImageDraw, ImageFont

from backend.services.intake.demo_client import DemoClient
from backend.services.intake.service import IntakeService
from backend.services.matching import CatalogueMatcher, load_catalog

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "samples"
PHOTOS_DIR = SAMPLES_DIR / "photos"
FIXTURES_DIR = SAMPLES_DIR / "fixtures"
EMAILS_DIR = SAMPLES_DIR / "emails"
EXCEL_DIR = SAMPLES_DIR / "excel"
EXPECTED_DIR = SAMPLES_DIR / "expected"

for d in [PHOTOS_DIR, FIXTURES_DIR, EMAILS_DIR, EXCEL_DIR, EXPECTED_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def draw_note_image(
    filename: str,
    title: str,
    header_lines: list[str],
    item_lines: list[str],
    messy: bool = False,
) -> Path:
    """Generate a realistic handwritten note on lined notepad paper."""
    width, height = 1000, 1300
    # Cream paper background
    bg_color = (252, 250, 242)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw faint blue horizontal lines
    line_spacing = 42
    start_y = 180
    for y in range(start_y, height - 60, line_spacing):
        draw.line([(60, y), (width - 60, y)], fill=(215, 228, 242), width=1)

    # Draw vertical red margin line
    draw.line([(140, 40), (140, height - 40)], fill=(240, 180, 180), width=2)

    # Header section
    font = ImageFont.load_default()
    ink_color = (30, 40, 60) if not messy else (35, 30, 50)

    # Draw title
    draw.text((160, 80), f"=== {title} ===", fill=(60, 60, 80), font=font)

    current_y = 120
    for hl in header_lines:
        draw.text((160, current_y), hl, fill=ink_color, font=font)
        current_y += 30

    current_y = 210
    for idx, item in enumerate(item_lines, 1):
        prefix = f"{idx}. "
        draw.text((110, current_y), prefix, fill=(100, 100, 120), font=font)
        if messy and idx in [2, 4]:
            # Draw with slight scratch/wobble for messy demo
            draw.text((160, current_y), item, fill=(80, 80, 100), font=font)
            # Add a slight underline / ink blot
            draw.line([(160, current_y + 14), (160 + len(item) * 6, current_y + 14)], fill=(120, 100, 100), width=1)
        else:
            draw.text((160, current_y), item, fill=ink_color, font=font)
        current_y += line_spacing

    target_path = PHOTOS_DIR / filename
    img.save(target_path, "JPEG", quality=88)
    print(f"Generated photo: {target_path} ({target_path.stat().st_size / 1024:.1f} KB)")
    return target_path


def create_photos_and_fixtures():
    # 1. Danish photo
    dk_items = [
        "50 stk Gipsplade standard 13mm 1200x2400",
        "20 stk Konstruktionstræ C24 45x145mm 4.2m",
        "10 pk Gipsskruer 3.9x40mm til træ",
        "25 sæk Portland cement standard 25kg",
        "30 m2 Rockwool flexibatts 100mm",
    ]
    dk_path = draw_note_image(
        "dk-handwritten-1.jpg",
        "BYGGEPLADS BESTILLING (DK)",
        [
            "Kunde: MT Højgaard",
            "Leveringsadresse: Sundkaj 7, 2150 Nordhavn, København",
            "Dato: 2026-11-10",
        ],
        dk_items,
        messy=False,
    )
    dk_bytes = dk_path.read_bytes()
    dk_hash = hashlib.sha256(dk_bytes).hexdigest()
    dk_payload = {
        "customer": "MT Højgaard",
        "customer_phone": None,
        "delivery_site": "Sundkaj 7, 2150 Nordhavn, København",
        "requested_date": "2026-11-10",
        "lines": [
            {
                "description": "Gipsplade standard 13mm 1200x2400",
                "quantity": 50.0,
                "unit": "stk",
                "confidence": 0.95,
                "source_text": "50 stk Gipsplade standard 13mm 1200x2400",
            },
            {
                "description": "Konstruktionstræ C24 45x145mm 4.2m",
                "quantity": 20.0,
                "unit": "stk",
                "confidence": 0.95,
                "source_text": "20 stk Konstruktionstræ C24 45x145mm 4.2m",
            },
            {
                "description": "Gipsskruer 3.9x40mm til træ",
                "quantity": 10.0,
                "unit": "pk",
                "confidence": 0.80,  # Below 0.85 to demo review
                "source_text": "10 pk Gipsskruer 3.9x40mm til træ",
            },
            {
                "description": "Portland cement standard 25kg",
                "quantity": 25.0,
                "unit": "sæk",
                "confidence": 0.95,
                "source_text": "25 sæk Portland cement standard 25kg",
            },
            {
                "description": "Rockwool flexibatts 100mm",
                "quantity": 30.0,
                "unit": "m2",
                "confidence": 0.95,
                "source_text": "30 m2 Rockwool flexibatts 100mm",
            },
        ],
    }
    fixture_dk = FIXTURES_DIR / f"{dk_hash}.json"
    fixture_dk.write_text(json.dumps({"source": "dk-handwritten-1.jpg", "payload": dk_payload}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Created fixture: {fixture_dk}")

    # 2. Swedish photo (messy handwriting demo)
    se_items = [
        "40 st Brandgipsskiva 15mm",
        "50 m2 Glasull isolering 100mm",
        "15 st Regel C24 45x145mm 4.8m",
        "10 pk Gipsskruv 3.9x40",
        "20 säck Cement standard 25kg",
    ]
    se_path = draw_note_image(
        "se-handwritten-1.jpg",
        "MATERIALBESTÄLLNING (SE - SNABBSKRIFT)",
        [
            "Kund: Skanska Sverige AB",
            "Leveransadress: Solnavägen 12, 113 65 Stockholm",
            "Datum: 2026-11-12",
        ],
        se_items,
        messy=True,
    )
    se_bytes = se_path.read_bytes()
    se_hash = hashlib.sha256(se_bytes).hexdigest()
    se_payload = {
        "customer": "Skanska Sverige AB",
        "customer_phone": None,
        "delivery_site": "Solnavägen 12, 113 65 Stockholm",
        "requested_date": "2026-11-12",
        "lines": [
            {
                "description": "Brandgipsskiva 15mm",
                "quantity": 40.0,
                "unit": "st",
                "confidence": 0.95,
                "source_text": "40 st Brandgipsskiva 15mm",
            },
            {
                "description": "Glasull isolering 100mm",
                "quantity": 50.0,
                "unit": "m2",
                "confidence": 0.72,  # Messy handwriting -> demo review
                "source_text": "50 m2 Glasull isolering 100mm",
            },
            {
                "description": "Regel C24 45x145mm 4.8m",
                "quantity": 15.0,
                "unit": "st",
                "confidence": 0.95,
                "source_text": "15 st Regel C24 45x145mm 4.8m",
            },
            {
                "description": "Gipsskruv 3.9x40",
                "quantity": 10.0,
                "unit": "pk",
                "confidence": 0.70,  # Messy handwriting -> demo review
                "source_text": "10 pk Gipsskruv 3.9x40",
            },
            {
                "description": "Cement standard 25kg",
                "quantity": 20.0,
                "unit": "säck",
                "confidence": 0.95,
                "source_text": "20 säck Cement standard 25kg",
            },
        ],
    }
    fixture_se = FIXTURES_DIR / f"{se_hash}.json"
    fixture_se.write_text(json.dumps({"source": "se-handwritten-1.jpg", "payload": se_payload}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Created fixture: {fixture_se}")

    # 3. Norwegian photo
    no_items = [
        "30 stk Brannplate gips 15mm",
        "25 m2 Rockwool flexibatts 100mm",
        "12 stk Konstruksjonsvirke 45x145 3.6m",
        "15 stk Portlandsement standard 25kg",
        "8 pk Gipsskruer 3.9x40mm",
    ]
    no_path = draw_note_image(
        "no-handwritten-1.jpg",
        "BYGGEPLASS ORDRE (NO)",
        [
            "Kunde: Veidekke Entreprenør AS",
            "Leveringsadresse: Dronning Eufemias gate 16, 0191 Oslo",
            "Dato: 2026-11-15",
        ],
        no_items,
        messy=False,
    )
    no_bytes = no_path.read_bytes()
    no_hash = hashlib.sha256(no_bytes).hexdigest()
    no_payload = {
        "customer": "Veidekke Entreprenør AS",
        "customer_phone": None,
        "delivery_site": "Dronning Eufemias gate 16, 0191 Oslo",
        "requested_date": "2026-11-15",
        "lines": [
            {
                "description": "Brannplate gips 15mm",
                "quantity": 30.0,
                "unit": "stk",
                "confidence": 0.95,
                "source_text": "30 stk Brannplate gips 15mm",
            },
            {
                "description": "Rockwool flexibatts 100mm",
                "quantity": 25.0,
                "unit": "m2",
                "confidence": 0.95,
                "source_text": "25 m2 Rockwool flexibatts 100mm",
            },
            {
                "description": "Konstruksjonsvirke 45x145 3.6m",
                "quantity": 12.0,
                "unit": "stk",
                "confidence": 0.95,
                "source_text": "12 stk Konstruksjonsvirke 45x145 3.6m",
            },
            {
                "description": "Portlandsement standard 25kg",
                "quantity": 15.0,
                "unit": "stk",
                "confidence": 0.80,  # Below 0.85 demo review
                "source_text": "15 stk Portlandsement standard 25kg",
            },
            {
                "description": "Gipsskruer 3.9x40mm",
                "quantity": 8.0,
                "unit": "pk",
                "confidence": 0.95,
                "source_text": "8 pk Gipsskruer 3.9x40mm",
            },
        ],
    }
    fixture_no = FIXTURES_DIR / f"{no_hash}.json"
    fixture_no.write_text(json.dumps({"source": "no-handwritten-1.jpg", "payload": no_payload}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Created fixture: {fixture_no}")


def create_emails():
    # DK Email
    dk_email = """Hej OneOrder,

Hermed bestilling til vores byggeplads i Nordhavn.

Kunde: MT Højgaard
Telefon: +45 00 00 00 01
Leveringsadresse: Sundkaj 7, 2150 Nordhavn, København
Leveringsdato: 2026-11-10

Materialer:
- 40 stk gipsplade standard 13mm 1200x2400
- Rockwool flexibatts 100mm - 20 m2
- Gipsskruer 3.9x40mm - 10 pk
- 15 stk Konstruktionstræ C24 45x145mm 4.2m
- Portland cement standard 25kg - 25 sæk

Venlig hilsen,
Lars Møller
"""
    (EMAILS_DIR / "dk_order.txt").write_text(dk_email, encoding="utf-8")

    # SE Email
    se_email = """Hej!

Vi behöver beställa följande material för Hagastaden-projektet.

Kund: Skanska Sverige AB
Telefon: +46 00 00 00 02
Leveransadress: Solnavägen 12, 113 65 Stockholm
Leveransdatum: 2026-11-12

Artiklar:
- 20 st Brandgipsskiva 15mm
- Glasull isolering 100mm - 30 m2
- Regel C24 45x145mm 4.8m - 12 st
- 15 st Akrylfog vit 300ml
- Cement standard 25kg - 10 sæk

Med vänlig hälsning,
Erik Lindqvist
"""
    (EMAILS_DIR / "se_order.txt").write_text(se_email, encoding="utf-8")

    # NO Email (with 1 missing quantity line)
    no_email = """Hei OneOrder,

Bestilling for prosjekt i Oslo sentrum.

Kunde: Veidekke Entreprenør AS
Telefon: +47 00 00 00 03
Leveringsadresse: Dronning Eufemias gate 16, 0191 Oslo
Leveringsdato: 2026-11-15

Materialliste:
- 30 stk Brannplate gips 15mm
- Rockwool flexibatts 100mm - 25 m2
- Konstruksjonsvirke 45x145 3.6m - 10 stk
- Våtromsplate 13mm
- Portlandsement standard 25kg - 20 stk
- 5 pk Gipsskruer 3.9x40mm

Mvh,
Olav Johansen
"""
    (EMAILS_DIR / "no_order.txt").write_text(no_email, encoding="utf-8")

    # EN Email
    en_email = """Dear OneOrder team,

Please find our purchase order for the Carlsberg Byen site.

Customer: NCC Construction Ltd
Phone: +45 00 00 00 04
Delivery: Pasteurs Vej 24, 1799 København V
Delivery date: 2026-11-18

Items:
- 50 pcs Fire resistant drywall 15mm 1200x2400
- Glass wool insulation 100mm - 40 m2
- Timber C24 spruce 45x145mm 4.2m - 15 pcs
- Standard drywall screws 3.9x40 - 12 pk
- 20 pcs White acrylic sealant 300ml

Best regards,
John Smith
"""
    (EMAILS_DIR / "en_order.txt").write_text(en_email, encoding="utf-8")
    print("Created 4 sample email files.")


def create_excels():
    # 1. DK materials
    wb_dk = openpyxl.Workbook()
    ws_dk = wb_dk.active
    ws_dk.title = "Materialer"
    ws_dk.append(["Beskrivelse", "Antal", "Enhed"])
    ws_dk.append(["Gipsplade standard 13mm 1200x2400", 60, "stk"])
    ws_dk.append(["Rockwool flexibatts 100mm", 30, "m2"])
    ws_dk.append(["Konstruktionstræ C24 45x145mm 4.2m", 20, "stk"])
    ws_dk.append(["Gipsskruer 3.9x40mm til træ", 10, "pk"])
    ws_dk.append(["Portland cement standard 25kg", 15, "stk"])
    ws_dk.cell(1, 4, "Telefon")
    for row in range(2, ws_dk.max_row + 1):
        if ws_dk.cell(row, 1).value is not None:
            ws_dk.cell(row, 4, "+45 00 00 00 01")
    wb_dk.save(EXCEL_DIR / "dk_materials.xlsx")

    # 2. SE materials
    wb_se = openpyxl.Workbook()
    ws_se = wb_se.active
    ws_se.title = "Artiklar"
    ws_se.append(["Artikel", "Antal", "Enhet"])
    ws_se.append(["Brandgipsskiva 15mm", 40, "st"])
    ws_se.append(["Glasull isolering 100mm", 50, "m2"])
    ws_se.append(["Regel C24 45x145mm 4.8m", 25, "st"])
    ws_se.append(["Gipsskruv 3.9x40", 15, "pk"])
    ws_se.append(["Cement standard 25kg", 30, "st"])
    ws_se.cell(1, 4, "Telefon")
    for row in range(2, ws_se.max_row + 1):
        if ws_se.cell(row, 1).value is not None:
            ws_se.cell(row, 4, "+46 00 00 00 02")
    wb_se.save(EXCEL_DIR / "se_material.xlsx")

    # 3. EN BOQ (with empty row and string quantity "12,5")
    wb_en = openpyxl.Workbook()
    ws_en = wb_en.active
    ws_en.title = "BOQ"
    ws_en.append(["Product", "Qty", "UOM"])
    ws_en.append(["Fire resistant drywall 15mm 1200x2400", 30, "pcs"])
    ws_en.append([None, None, None])  # Empty row
    ws_en.append(["Timber C24 spruce 45x145mm 4.2m", "12,5", "m"])  # String qty with comma
    ws_en.append(["Glass wool insulation 100mm", 45, "m2"])
    ws_en.append(["Standard drywall screws 3.9x40", 8, "pk"])
    ws_en.cell(1, 4, "Phone")
    for row in range(2, ws_en.max_row + 1):
        if ws_en.cell(row, 1).value is not None:
            ws_en.cell(row, 4, "+45 00 00 00 04")
    wb_en.save(EXCEL_DIR / "en_boq.xlsx")
    print("Created 3 sample excel files.")


def generate_expected():
    ai = DemoClient(FIXTURES_DIR)
    service = IntakeService(ai)
    catalog = load_catalog(str(ROOT / "data" / "catalog.json"))
    matcher = CatalogueMatcher(catalog, ai=ai)

    all_samples = [
        ("photos/dk-handwritten-1.jpg", "dk-handwritten-1.jpg"),
        ("photos/se-handwritten-1.jpg", "se-handwritten-1.jpg"),
        ("photos/no-handwritten-1.jpg", "no-handwritten-1.jpg"),
        ("emails/dk_order.txt", "dk_order.txt"),
        ("emails/se_order.txt", "se_order.txt"),
        ("emails/no_order.txt", "no_order.txt"),
        ("emails/en_order.txt", "en_order.txt"),
        ("excel/dk_materials.xlsx", "dk_materials.xlsx"),
        ("excel/se_material.xlsx", "se_material.xlsx"),
        ("excel/en_boq.xlsx", "en_boq.xlsx"),
    ]

    for rel_path, filename in all_samples:
        file_path = SAMPLES_DIR / rel_path
        content = file_path.read_bytes()
        order = service.process(filename, content)
        order = matcher.match_order(order)

        expected_data = {
            "source_file": filename,
            "line_count": len(order.lines),
            "customer": order.customer,
            "customer_phone": order.customer_phone,
            "delivery_site": order.delivery_site,
            "requested_date": str(order.requested_date) if order.requested_date else None,
            "lines": [
                {
                    "line_number": idx,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit": line.unit,
                    "matched_sku": line.matched_sku,
                    "needs_review": line.needs_review,
                }
                for idx, line in enumerate(order.lines, 1)
            ],
        }

        out_file = EXPECTED_DIR / f"{filename}.json"
        out_file.write_text(json.dumps(expected_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Generated expected for {filename}: {len(order.lines)} lines -> {out_file.name}")


if __name__ == "__main__":
    create_photos_and_fixtures()
    create_emails()
    create_excels()
    generate_expected()
