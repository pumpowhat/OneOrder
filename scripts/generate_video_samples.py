"""Build the demo-video inbox in samples/video-demo/ (one PDF, one Excel sheet, one photo, one email).

    python -m scripts.generate_video_samples

Each file covers different review cases, see samples/video-demo/README.md. Run the app with
INBOX_DIR=samples/video-demo to show only these files in the sample inbox. The PDF's demo fixture
is recorded separately with ``python -m scripts.record_fixture samples/video-demo/pdf/<name>.pdf``.
"""

import shutil
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "samples" / "video-demo"

PDF_NAME = "dk-nordhavn-materialeliste.pdf"
XLSX_NAME = "se-goteborg-materiallista.xlsx"


# --- PDF (text layer, Helvetica, WinAnsi) -----------------------------------------------------

def _esc(text: str) -> bytes:
    raw = text.encode("cp1252")
    return raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _pdf(ops: list[bytes]) -> bytes:
    stream = b"\n".join(ops)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Title (Materialeliste Sundkaj 7) /Producer (OneOrder sample generator) "
        b"/CreationDate (D:20261109000000Z) >>",
    ]
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for n, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R /Info 7 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


def build_pdf() -> bytes:
    ops: list[bytes] = []

    def text(x, y, s, size=10, bold=False):
        ops.append(b"BT /%s %d Tf %d %d Td (%s) Tj ET" % (b"F2" if bold else b"F1", size, x, y, _esc(s)))

    def line(x1, y1, x2, y2, width=0.6):
        ops.append(b"%.1f w %d %d m %d %d l S" % (width, x1, y1, x2, y2))

    text(50, 790, "MATERIALELISTE / BESTILLING", 16, bold=True)
    text(50, 772, "Byggeplads: Sundkaj 7 - etape 2, tagkonstruktion", 10)
    line(50, 762, 545, 762, 1.2)

    fields = [
        ("Kunde / firma:", ""),
        ("Kontaktperson:", "Lars (formand)"),
        ("Telefon:", "+45 31 24 56 78"),
        ("Leveringsadresse:", "Sundkaj 7, 2150 Nordhavn, København"),
        ("Ønsket levering:", "2026-11-12 (senest kl. 07:00)"),
    ]
    y = 740
    for label, value in fields:
        text(50, y, label, 10, bold=True)
        text(170, y, value, 10)
        line(170, y - 3, 545, y - 3, 0.3)
        y -= 20

    y -= 14
    cols = [(50, "Pos."), (90, "Beskrivelse"), (390, "Antal"), (450, "Enhed")]
    for x, head in cols:
        text(x, y, head, 10, bold=True)
    line(50, y - 5, 545, y - 5, 0.8)
    rows = [
        ("1", "Gipsplade standard 13mm 1200x2400", "40", "stk"),
        ("2", "Rockwool flexibatts 100mm", "30", "m2"),
        ("3", "Svensk furu kärnvirke 45x195 C30 (Norrland)", "60", "m"),
        ("4", "Stålbjælke HEA 200, 6 m - kran nødvendig", "4", "stk"),
        ("5", "Skruer til gips, ca. 40 mm", "10", "pk"),
    ]
    y -= 22
    for row in rows:
        for (x, _), value in zip(cols, row):
            text(x, y, value, 10)
        line(50, y - 6, 545, y - 6, 0.3)
        y -= 22

    y -= 16
    text(50, y, "Bemærk: bjælkerne skal løftes direkte op på dækket, kranbil påkrævet.", 9)
    text(50, y - 14, "Ring til Lars på pladsen ved ankomst.", 9)
    text(50, 60, "Udfyldt på pladsen 09.11.2026", 8)
    return _pdf(ops)


# --- Excel ---------------------------------------------------------------------------------------

def build_xlsx(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Material"
    ws.append(["Artikel", "Antal", "Enhet", "Telefon", "Kommentar"])
    rows = [
        ("Brandgipsskiva 15mm", 40, "st", "+46 70 123 45 67", None),
        ("Glasull isolering 100mm", "12,5", "m2", "+46 70 123 45 67", "decimal med komma"),
        ("Regel C24 45x145mm 4.8m", None, "st", "+46 70 123 45 67", "antal saknas"),
        ("Ljuddämpande golvmatta 5mm", 20, "m2", "+46 70 123 45 67", None),
        ("Gipsskruv 3.9x40", 15, "pk", "+46 70 123 45 67", None),
    ]
    for row in rows:
        ws.append(list(row))
    for cell in ws["D"]:
        cell.number_format = "@"
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["D"].width = 20
    ws.column_dimensions["E"].width = 22
    wb.properties.creator = "OneOrder sample generator"
    wb.save(path)


def main() -> None:
    for sub in ("pdf", "excel", "photos", "emails"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    (OUT / "pdf" / PDF_NAME).write_bytes(build_pdf())
    build_xlsx(OUT / "excel" / XLSX_NAME)
    # Reused as-is so their recorded demo fixtures still match (fixtures are keyed by SHA-256).
    shutil.copyfile(ROOT / "samples/photos/se-handwritten-1.jpg", OUT / "photos/se-handwritten-1.jpg")
    shutil.copyfile(ROOT / "samples/emails/en_order.txt", OUT / "emails/en_order.txt")
    print(f"Wrote demo inbox to {OUT}")


if __name__ == "__main__":
    main()
