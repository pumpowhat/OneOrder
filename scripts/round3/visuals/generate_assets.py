"""Regenerate Round 3 charts and editable draw.io architecture source.

Authoring only: python -m pip install matplotlib pillow
Run from the repository root: python scripts/round3/visuals/generate_assets.py
The architecture PNG is exported separately through draw.io (see export_drawio.cjs).
"""

from pathlib import Path
import csv
import json
import os
import tempfile
import xml.etree.ElementTree as ET

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "oneorder-round3-matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "round3" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
for font in (ROOT / "docs" / "report" / "fonts").glob("Inter-*.ttf"):
    font_manager.fontManager.addfont(str(font))
plt.rcParams.update({"font.family": "Inter", "font.size": 14, "text.color": "#243445", "axes.labelcolor": "#526273", "xtick.color": "#526273", "ytick.color": "#526273", "axes.edgecolor": "#D5DDE4", "savefig.facecolor": "white"})


def figure():
    return plt.subplots(figsize=(19.2, 10.8), dpi=100, facecolor="white")


def waterfall():
    data = [
        ("Kế hoạch cũ", 764.5, "total"),
        ("Hoãn\nNa Uy", -162, "cut"),
        ("Tách\ngiai đoạn 2", -72, "cut"),
        ("Pilot SE\ngọn hơn", -40.5, "cut"),
        ("Giảm\ndự phòng", -33.5, "cut"),
        ("Cloud, AI,\nđào tạo", -27, "cut"),
        ("Migration\nCRM DK", 81, "add"),
        ("Salesforce\nadapter", 22.5, "add"),
        ("Kế hoạch mới", 533, "total"),
    ]
    assert round(data[0][1] + sum(x[1] for x in data[1:-1]), 1) == data[-1][1]
    fig, ax = figure()
    fig.subplots_adjust(left=.07, right=.97, bottom=.21, top=.76)
    fig.text(.055, .936, "ROUND 3  /  NGÂN SÁCH 12 THÁNG", fontsize=15, weight="bold", color="#607182")
    fig.text(.055, .875, "Hoãn Na Uy và làm gọn đủ bù CRM:", fontsize=30, weight="bold")
    fig.text(.055, .823, "kế hoạch mới €533k, vừa ngân sách", fontsize=30, weight="bold")
    colors = {"cut": "#F0B5B3", "add": "#ABD9B5", "total": "#AEB8C2"}
    current = 0
    previous = None
    rows = []
    for i, (label, value, kind) in enumerate(data):
        if kind == "total":
            bottom, height, current = 0, value, value
        else:
            bottom, height = min(current, current + value), abs(value)
            current += value
        if previous is not None and kind != "total":
            ax.plot([i - .65, i - .35], [previous, previous], color="#AAB5BF", linewidth=1.2, zorder=1)
        ax.bar(i, height, bottom=bottom, width=.68, color=colors[kind], edgecolor="white", linewidth=1.2, zorder=3)
        amount = f"{abs(value):g}".replace(".", ",")
        amount = ("−" if value < 0 else "+" if kind == "add" else "") + amount
        top = bottom + height
        ax.text(i, top + 13, amount, ha="center", va="bottom", fontsize=20, weight="bold")
        previous = current
        rows.append({"step": label.replace("\n", " "), "change_k_eur": value, "kind": kind, "running_total_k_eur": current})
    ax.axhline(535, color="#4B5B6B", linestyle=(0, (6, 4)), linewidth=1.6, zorder=2)
    ax.annotate("Trần ngân sách €535k", xy=(8.45, 535), xytext=(8.5, 635), ha="right", fontsize=15, color="#4B5B6B", arrowprops={"arrowstyle": "-", "color": "#7E8D9C", "linewidth": 1.1}, bbox={"facecolor": "white", "edgecolor": "none", "pad": 4})
    ax.set_xlim(-.6, 8.6)
    ax.set_ylim(0, 825)
    ax.set_yticks(range(0, 801, 100))
    ax.set_ylabel("Nghìn EUR", loc="top", fontsize=16, labelpad=15)
    ax.set_xticks(range(len(data)), [x[0] for x in data], fontsize=15)
    ax.tick_params(axis="both", length=0, pad=12)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#E8EDF1", linewidth=.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.legend(handles=[Patch(color=colors[k], label=l) for k, l in [("cut", "Cắt / hoãn phạm vi"), ("add", "Bổ sung CRM"), ("total", "Tổng kế hoạch")]], loc="lower left", bbox_to_anchor=(.055, .062), ncol=3, frameon=False, fontsize=15)
    fig.text(.965, .09, "Tiết kiệm €231,5k  •  Dư €2k so với trần làm tròn", ha="right", fontsize=15, color="#526273")
    fig.text(.055, .028, "Nguồn: số liệu phân công Round 3. 764,5 × 70% = 535,15; đường ngân sách dùng mức làm tròn 535 theo đề bài.", fontsize=12, color="#6B7C8C")
    fig.savefig(OUT / "budget-waterfall.png", dpi=100)
    plt.close(fig)
    with (OUT / "budget-waterfall.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def timeline():
    fig, ax = figure()
    fig.subplots_adjust(left=.285, right=.955, bottom=.19, top=.77)
    fig.text(.055, .93, "ROUND 3  /  LỘ TRÌNH TRIỂN KHAI", fontsize=15, weight="bold", color="#607182")
    fig.text(.055, .86, "12 tháng: Thụy Điển trước, Đan Mạch trên Salesforce", fontsize=30, weight="bold")
    fig.text(.055, .808, "T4 là mốc chuyển CRM; Na Uy được hoãn sang năm 2", fontsize=18, color="#526273")
    rows = [
        ("Pilot Thụy Điển", 0, 3, "se"),
        ("Go-live Thụy Điển", 3, 6, "se"),
        ("Migration CRM Đan Mạch", 1, 4, "crm"),
        ("Salesforce chạy ở DK", 4, 4, "milestone"),
        ("Salesforce adapter", 4, 6, "crm"),
        ("Go-live DK trên Salesforce", 6, 12, "crm"),
        ("Na Uy", None, None, "deferred"),
    ]
    colors = {"se": "#9FBFDA", "crm": "#A7D8B6", "milestone": "#32805B", "deferred": "#E5E9ED"}
    for i, (_, start, end, kind) in enumerate(rows):
        if kind == "milestone":
            ax.scatter([start], [i], marker="D", s=220, color=colors[kind], edgecolor="white", linewidth=1.8, zorder=4)
            ax.text(4.3, i, "T4  •  Salesforce hoạt động tại DK", va="center", fontsize=15, color="#2D7352", weight="bold")
        elif kind == "deferred":
            ax.barh(i, 12, left=0, height=.57, color=colors[kind], edgecolor="#B7C2CB", hatch="///", linewidth=.5)
            ax.text(6, i, "HOÃN SANG NĂM 2", va="center", ha="center", fontsize=15, weight="bold", bbox={"facecolor": "#F6F8FA", "edgecolor": "none", "pad": 6})
        else:
            ax.barh(i, end-start, left=start, height=.57, color=colors[kind], edgecolor="white", linewidth=1.4, zorder=3)
            ax.text((start+end)/2, i, f"T{start}–T{end}", va="center", ha="center", fontsize=16, weight="bold")
    ax.axvline(4, color="#3A775A", linestyle=(0, (5, 4)), linewidth=1.7, zorder=2)
    ax.text(4, -0.68, "T4", color="#2D7352", fontsize=15, weight="bold", ha="center")
    ax.set_xlim(0, 12)
    ax.set_ylim(6.65, -.85)
    ax.set_xticks(range(13), [f"T{x}" for x in range(13)], fontsize=14)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=16)
    ax.tick_params(axis="both", length=0, pad=15)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#E5EBEF", linewidth=.9)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.legend(handles=[Patch(color=colors[k], label=l) for k, l in [("se", "Triển khai Thụy Điển"), ("crm", "Hạng mục CRM / Salesforce DK")]], loc="lower left", bbox_to_anchor=(.055, .065), ncol=2, frameon=False, fontsize=16)
    fig.text(.055, .028, "T0 là ngày khởi động dự án; mốc thời gian tương đối theo kế hoạch Round 3, chưa gắn ngày lịch.", fontsize=13, color="#6B7C8C")
    fig.savefig(OUT / "delivery-timeline.png", dpi=100)
    plt.close(fig)
    (OUT / "delivery-timeline.json").write_text(json.dumps([{"workstream": n, "from_month": a, "to_month": b, "kind": k} for n,a,b,k in rows], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def architecture():
    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device"})
    diagram = ET.SubElement(mxfile, "diagram", {"id": "round3-architecture", "name": "Trước và sau", "alt": "Kiến trúc OneOrder trước và sau: thêm khớp khách hàng và Salesforce adapter cho DK; Dynamics chỉ dùng cho migration một lần."})
    model = ET.SubElement(diagram, "mxGraphModel", {"dx": "1920", "dy": "1080", "grid": "0", "page": "1", "pageScale": "1", "pageWidth": "1920", "pageHeight": "1080", "background": "#FFFFFF", "math": "0", "shadow": "0"})
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    base = "rounded=1;whiteSpace=wrap;html=0;fontFamily=Arial;fontSize=25;fontColor=#243445;fillColor=#F2F5F8;strokeColor=#98A8B8;strokeWidth=2;spacing=10;"

    def box(id, text, x,y,w,h, extra="", style=base):
        cell = ET.SubElement(root, "mxCell", {"id": id, "value": text, "style": style + extra, "vertex": "1", "parent": "1"})
        ET.SubElement(cell, "mxGeometry", {"x":str(x), "y":str(y), "width":str(w), "height":str(h), "as":"geometry"})
        return cell

    def text(id,value,x,y,w,h,size=24,color="#243445",bold=False,align="left"):
        return box(id,value,x,y,w,h,style=f"text;html=0;whiteSpace=wrap;strokeColor=none;fillColor=none;align={align};verticalAlign=middle;spacing=0;fontFamily=Arial;fontSize={size};fontColor={color};fontStyle={1 if bold else 0};")

    def edge(id, source, target, label="", extra="", points=None):
        cell = ET.SubElement(root, "mxCell", {"id":id,"value":label,"style":"edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;endArrow=block;endFill=1;strokeColor=#64788A;strokeWidth=2;fontFamily=Arial;fontSize=20;fontColor=#526273;labelBackgroundColor=#FFFFFF;"+extra,"edge":"1","source":source,"target":target,"parent":"1"})
        geom=ET.SubElement(cell,"mxGeometry",{"relative":"1","as":"geometry"})
        if points:
            arr=ET.SubElement(geom,"Array",{"as":"points"})
            for x,y in points: ET.SubElement(arr,"mxPoint",{"x":str(x),"y":str(y)})
        return cell

    # The white page rectangle fixes the exported bounds at exactly 16:9.
    box("page","",0,0,1920,1080,"",style="rounded=0;strokeColor=none;fillColor=#FFFFFF;")
    text("eyebrow","ROUND 3  /  KIẾN TRÚC TRƯỚC → SAU",70,30,1700,35,20,"#607182",True)
    text("title","Giữ lõi điều phối, thêm Salesforce tại Đan Mạch",70,85,1780,65,40,bold=True)
    text("before","TRƯỚC",110,170,760,45,28,"#526273",True)
    text("after","SAU",1030,170,800,45,28,"#2D7352",True)
    box("before-core","",110,375,760,330,"fillColor=#FAFBFC;strokeColor=#CAD3DC;",style=base)
    box("after-core","",1030,375,800,385,"fillColor=#FAFBFC;strokeColor=#CAD3DC;",style=base)
    text("before-name","OneOrder",135,390,300,35,25,bold=True)
    text("after-name","OneOrder",1055,390,300,35,25,bold=True)
    box("before-sales","Nhân viên bán hàng",140,250,310,78)
    box("before-ai","AI model API",580,250,260,78)
    box("before-intake","Intake + Review",145,465,255,80)
    box("before-plan","Plan · ETA · Confirm",445,465,385,80)
    box("before-erp-adapters","ERP adapters",310,600,345,65)
    box("before-erp","ERP các nước\nDK · SE · NO",215,805,550,95)
    edge("b-sales-intake","before-sales","before-intake","","exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    edge("b-intake-ai","before-intake","before-ai","trích xuất","exitX=1;exitY=0;entryX=0.5;entryY=1;",[(430,355),(710,355)])
    edge("b-intake-plan","before-intake","before-plan")
    edge("b-plan-adapter","before-plan","before-erp-adapters","","exitX=0.5;exitY=1;entryX=0.8;entryY=0;")
    edge("b-adapter-erp","before-erp-adapters","before-erp","tồn kho / giữ hàng","exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    green="strokeColor=#37815B;strokeWidth=3;fillColor=#EAF5ED;"
    box("after-sales","Nhân viên bán hàng",1065,250,310,78)
    box("after-ai","AI model API",1510,250,260,78)
    box("after-intake","Intake + Review",1065,445,245,78)
    box("after-match","Khớp khách hàng\nNhân viên chốt",1350,445,410,78,green)
    box("after-plan","Plan · ETA · Confirm",1065,575,360,78)
    box("after-crm-adapter","CRM adapter",1490,575,270,78,green)
    box("after-erp-adapters","ERP adapters",1085,685,320,52)
    box("after-erp","ERP các nước\nDK · SE · NO",1065,815,360,85)
    box("salesforce","Salesforce CRM (DK)",1490,815,300,85,green)
    box("dynamics","Dynamics 365 (DK)",1490,970,300,60,"dashed=1;dashPattern=8 5;fillColor=#FFFFFF;strokeColor=#8D9BA8;")
    edge("a-sales-intake","after-sales","after-intake","","exitX=0.4;exitY=1;entryX=0.5;entryY=0;")
    edge("a-intake-ai","after-intake","after-ai","trích xuất","exitX=1;exitY=0;entryX=0.5;entryY=1;",[(1330,355),(1640,355)])
    edge("a-intake-match","after-intake","after-match","","strokeColor=#37815B;")
    edge("a-intake-plan","after-intake","after-plan","","exitX=0.5;exitY=1;entryX=0.35;entryY=0;")
    edge("a-match-crm","after-match","after-crm-adapter","tra cứu","strokeColor=#37815B;exitX=0.67;exitY=1;entryX=0.67;entryY=0;")
    commit_edge = edge("a-plan-crm","after-plan","after-crm-adapter","ghi Order","strokeColor=#37815B;exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    ET.SubElement(commit_edge.find("mxGeometry"), "mxPoint", {"x": "0", "y": "-57", "as": "offset"})
    edge("a-plan-erp","after-plan","after-erp-adapters","","exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    edge("a-adapter-erp","after-erp-adapters","after-erp","","exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    edge("a-crm-salesforce","after-crm-adapter","salesforce","","strokeColor=#37815B;exitX=1;exitY=0.5;entryX=1;entryY=0.5;",[(1805,614),(1805,857)])
    edge("a-migration","dynamics","salesforce","migration 1 lần","dashed=1;dashPattern=8 5;strokeColor=#8D9BA8;exitX=0.5;exitY=0;entryX=0.5;entryY=1;")
    text("pending","CRM lỗi: Confirm vẫn thành công\nPending sync → retry",1450,686,345,66,20,"#2D7352",align="center")
    text("note","Viền xanh: phần bổ sung cho CRM DK.\nDynamics chỉ là nguồn migration một lần;\nOneOrder không kết nối Dynamics.",110,950,780,93,24,"#526273")
    text("rollout-note","NO: rollout hoãn sang năm 2",1065,922,360,35,19,"#607182",align="center")
    ET.indent(mxfile, space="  ")
    (OUT / "architecture-before-after.drawio").write_text(ET.tostring(mxfile,encoding="unicode")+"\n",encoding="utf-8")


if __name__ == "__main__":
    waterfall()
    timeline()
    architecture()
    print(f"Wrote charts and draw.io source to {OUT}")
