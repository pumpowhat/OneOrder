"""Script to generate complete, realistic mock datasets for OneOrder MVP.

Generates:
  - data/catalog.json: 160+ construction products with multilingual aliases, weights, and crane flags.
  - data/warehouses.json: 15 warehouses across Denmark, Sweden, and Norway (Central DCs and Regional Branches).
  - data/sites.json: 10 realistic Nordic construction project sites with geo-coordinates.
  - data/inventory_dk.csv: Danish ERP native inventory export (CSV format).
  - data/inventory_se.json: Swedish ERP native inventory export (Swedish field names).
  - data/inventory_no.json: Norwegian ERP native inventory export (English field names).
"""

import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

# 1. CATALOG ITEMS DEFINITION
BASE_SAMPLE_ITEMS = [
    {
        "sku": "GYP-13-2400",
        "name": "Gipsplade standard 13mm 1200x2400",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 25.5,
        "requires_crane": False,
        "aliases": ["gipsplade 13mm", "gipsskiva normal 13mm", "gipsplate standard 13mm", "standard plasterboard 13mm", "gipskarton 13mm"],
    },
    {
        "sku": "GYP-15-FIRE",
        "name": "Gipsplade brand 15mm 1200x2400",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 32.0,
        "requires_crane": False,
        "aliases": ["brandgipsskiva 15mm", "brannplate gips 15mm", "fire rated plasterboard 15mm", "brandgips 15mm"],
    },
    {
        "sku": "ISO-GLAS-100",
        "name": "Isolering glasuld 100mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 2.2,
        "requires_crane": False,
        "aliases": ["isolering 100mm", "glasull isolering 100mm", "glassull isolasjon 100mm", "glass wool insulation 100mm"],
    },
    {
        "sku": "ISO-ROCK-150",
        "name": "Rockwool stenuld flexibatts 150mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 4.5,
        "requires_crane": False,
        "aliases": ["stenull isolering 150mm", "steinull isolasjon 150mm", "stone wool insulation 150mm", "stenuld 150mm"],
    },
    {
        "sku": "SCR-GIP-40",
        "name": "Gipsskruer 3.9x40mm til træ/stål",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 1.1,
        "requires_crane": False,
        "aliases": ["skruer 4x40", "gipsskruer 4x40", "gipsskruv 3.9x40", "drywall screws 40mm", "skruv 4x40"],
    },
    {
        "sku": "SCR-TER-55",
        "name": "Terrasseskrue rustfri A4 4.8x55mm",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 1.4,
        "requires_crane": False,
        "aliases": ["trallskruv rostfri 55mm", "terrasseskrue syrefast 55mm", "decking screws stainless 55mm"],
    },
    {
        "sku": "TIM-SPRU-45145",
        "name": "Konstruktionstræ C24 45x145mm ru",
        "category": "timber",
        "unit": "m",
        "weight_kg": 3.2,
        "requires_crane": False,
        "aliases": ["spærtræ 45x145", "regel virke 45x145", "konstruksjonsvirke 45x145", "structural timber 45x145", "regel 45x145"],
    },
    {
        "sku": "TIM-SPRU-45095",
        "name": "Konstruktionstræ C24 45x95mm høvlet",
        "category": "timber",
        "unit": "m",
        "weight_kg": 2.1,
        "requires_crane": False,
        "aliases": ["spærtræ 45x95", "regel 45x95", "konstruksjonsvirke 45x95", "structural timber 45x95"],
    },
    {
        "sku": "PLY-SPRU-18",
        "name": "Krydsfiner konstruktion 18mm",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 31.0,
        "requires_crane": False,
        "aliases": ["plywood konstruktion 18mm", "kryssfinér konstruksjon 18mm", "structural plywood 18mm"],
    },
    {
        "sku": "CEM-PORT-25",
        "name": "Portland cement standard 25kg",
        "category": "masonry",
        "unit": "sæk",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["cement standard 25kg", "sement 25kg", "portland cement 25kg", "cement 25kg"],
    },
    {
        "sku": "BET-TORR-25",
        "name": "Tørmørtel KC 50/50/700 25kg",
        "category": "masonry",
        "unit": "sæk",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["murbruk 25kg", "murmørtel 25kg", "dry mortar 25kg", "mørtel 25kg"],
    },
    {
        "sku": "ARM-JERN-12",
        "name": "Armeringsjern kamstål B500B Ø12mm 6m",
        "category": "steel",
        "unit": "stk",
        "weight_kg": 5.3,
        "requires_crane": False,
        "aliases": ["kamstål 12mm", "armeringsstål 12mm", "rebar 12mm", "armeringsjern 12mm"],
    },
    {
        "sku": "PIP-PVC-110",
        "name": "Afløbsrør PVC grå Ø110mm 2m",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 2.8,
        "requires_crane": False,
        "aliases": ["avloppsrör pvc 110mm", "avløpsrør pvc 110mm", "drainage pipe pvc 110mm", "pvc rør 110mm"],
    },
    {
        "sku": "FUG-ACR-300",
        "name": "Akrylfugemasse hvid 300ml",
        "category": "chemicals",
        "unit": "stk",
        "weight_kg": 0.5,
        "requires_crane": False,
        "aliases": ["akrylfog vit 300ml", "akrylfugemasse hvit 300ml", "acrylic sealant white 300ml", "fugemasse 300ml"],
    },
    {
        "sku": "MEM-RAD-04",
        "name": "Radonspærre membran 0.4mm 4x25m",
        "category": "membranes",
        "unit": "rl",
        "weight_kg": 38.0,
        "requires_crane": False,
        "aliases": ["radonspärr 0.4mm", "radonsperre 0.4mm", "radon barrier membrane 0.4mm", "radonspærre 0.4mm"],
    },
]

ADDITIONAL_ITEMS = [
    # --- Drywall & Boards ---
    {
        "sku": "GYP-13-3000",
        "name": "Gipsplade standard 13mm 1200x3000",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 32.0,
        "requires_crane": False,
        "aliases": ["gipsplade 3m", "gipsskiva 3000mm", "gipsplate 3m lang", "drywall board 3000mm"],
    },
    {
        "sku": "GYP-09-2400",
        "name": "Gipsplade renovering 9mm 1200x2400",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 18.0,
        "requires_crane": False,
        "aliases": ["renoveringsgips 9mm", "rehabgipsskiva 9mm", "rehabiliteringsgips 9mm", "renovation plasterboard 9mm"],
    },
    {
        "sku": "GYP-13-WATH",
        "name": "Gipsplade vådrum imprægneret 13mm 1200x2400",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 27.0,
        "requires_crane": False,
        "aliases": ["vådrumsgips 13mm", "våtrumsskiva 13mm", "våtromsplate 13mm", "moisture resistant drywall 13mm"],
    },
    {
        "sku": "GYP-15-ACOUS",
        "name": "Akustikgips perforeret 12.5mm 1200x2400",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 24.0,
        "requires_crane": False,
        "aliases": ["akustikgipsplade", "akustikskiva gips", "lyddempende gipsplate", "acoustic plasterboard"],
    },
    {
        "sku": "GYP-09-WIND",
        "name": "Vindgips udvendig 9.5mm 1200x2700",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 22.0,
        "requires_crane": False,
        "aliases": ["vindgips 9mm", "utvändig gipsskiva", "vindtett gipsplate", "exterior weatherboard gypsum"],
    },
    {
        "sku": "GYP-FIB-13",
        "name": "Fiberarmeret gipsplade Fermacell 12.5mm 1200x2400",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 43.5,
        "requires_crane": False,
        "aliases": ["fermacell 12.5mm", "fibergipsskiva 12.5mm", "fibergipsplate fermacell", "fiber gypsum board"],
    },
    {
        "sku": "GYP-PROF-U70",
        "name": "Stålprofil U-skinne 70mm 3000mm",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 2.4,
        "requires_crane": False,
        "aliases": ["u-skinne 70mm", "stålregel u70", "styreskinne u70", "steel track u70 3m"],
    },
    {
        "sku": "GYP-PROF-C70",
        "name": "Stålprofil C-stolpe 70mm 3000mm",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 2.7,
        "requires_crane": False,
        "aliases": ["c-stolpe 70mm", "stålregel c70", "stender c70", "steel stud c70 3m"],
    },
    {
        "sku": "GYP-PROF-U95",
        "name": "Stålprofil U-skinne 95mm 3000mm",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 3.1,
        "requires_crane": False,
        "aliases": ["u-skinne 95mm", "stålregel u95", "styreskinne u95", "steel track u95"],
    },
    {
        "sku": "GYP-PROF-C95",
        "name": "Stålprofil C-stolpe 95mm 3000mm",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 3.4,
        "requires_crane": False,
        "aliases": ["c-stolpe 95mm", "stålregel c95", "stender c95", "steel stud c95"],
    },
    {
        "sku": "GYP-TAPE-PAP",
        "name": "Armeringsbånd papir til gips 50mm 75m",
        "category": "drywall",
        "unit": "rl",
        "weight_kg": 0.6,
        "requires_crane": False,
        "aliases": ["papirbånd gips", "pappersremsa gips", "skjøtebånd papir", "paper joint tape 75m"],
    },
    {
        "sku": "GYP-TAPE-GLAS",
        "name": "Glasfiberarmering selvklæbende 50mm 90m",
        "category": "drywall",
        "unit": "rl",
        "weight_kg": 0.5,
        "requires_crane": False,
        "aliases": ["glasfiberbånd 50mm", "glasfiberremsa självhäftande", "glassfiberteip gips", "fiberglass joint tape"],
    },
    {
        "sku": "GYP-FILL-JNT",
        "name": "Gipsspartelmasse medium 15L spand",
        "category": "drywall",
        "unit": "spand",
        "weight_kg": 18.5,
        "requires_crane": False,
        "aliases": ["spartelmasse medium 15l", "sandspackel medium 15l", "skjøtesparkel medium", "joint filler ready mix 15l"],
    },
    {
        "sku": "GYP-FILL-FIN",
        "name": "Gipsspartelmasse fin finish 15L",
        "category": "drywall",
        "unit": "spand",
        "weight_kg": 18.0,
        "requires_crane": False,
        "aliases": ["finspartel 15l", "finspackel 15l", "finsparkel 15l", "fine finish filler 15l"],
    },
    {
        "sku": "GYP-COR-ALU",
        "name": "Hjørneprofil aluminium 25x25mm 3000mm",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 0.4,
        "requires_crane": False,
        "aliases": ["hjørneprofil alu 3m", "hörnprofil aluminium", "hjørnelist gips alu", "aluminum corner bead 3m"],
    },
    {
        "sku": "GYP-INSP-40",
        "name": "Inspektionslem gips 400x400mm hvid",
        "category": "drywall",
        "unit": "stk",
        "weight_kg": 3.2,
        "requires_crane": False,
        "aliases": ["inspektionslem 400x400", "inspektionslucka 400x400", "inspeksjonsluke 400x400", "inspection hatch 400x400"],
    },

    # --- Structural Timber & Sheet Wood ---
    {
        "sku": "TIM-SPRU-45195",
        "name": "Konstruktionstræ C24 45x195mm spærtræ",
        "category": "timber",
        "unit": "m",
        "weight_kg": 4.3,
        "requires_crane": False,
        "aliases": ["spærtræ 45x195", "regel virke 45x195", "konstruksjonsvirke 45x195", "structural timber 45x195"],
    },
    {
        "sku": "TIM-SPRU-45220",
        "name": "Konstruktionstræ C24 45x220mm spærtræ",
        "category": "timber",
        "unit": "m",
        "weight_kg": 4.9,
        "requires_crane": False,
        "aliases": ["spærtræ 45x220", "regel virke 45x220", "konstruksjonsvirke 45x220", "structural timber 45x220"],
    },
    {
        "sku": "TIM-SPRU-45070",
        "name": "Konstruktionstræ C24 45x70mm høvlet",
        "category": "timber",
        "unit": "m",
        "weight_kg": 1.6,
        "requires_crane": False,
        "aliases": ["regel 45x70", "konstruktionstræ 45x70", "stender 45x70", "structural timber 45x70"],
    },
    {
        "sku": "TIM-LATH-3857",
        "name": "Taglægter T1 godkendt 38x57mm 4200mm",
        "category": "timber",
        "unit": "m",
        "weight_kg": 1.1,
        "requires_crane": False,
        "aliases": ["taglægte 38x57", "takläkt 38x57", "taklekt t1 38x57", "roof batten 38x57"],
    },
    {
        "sku": "TIM-LATH-2550",
        "name": "Forskallingsbrædder 25x50mm ru",
        "category": "timber",
        "unit": "m",
        "weight_kg": 0.6,
        "requires_crane": False,
        "aliases": ["forskalling 25x50", "glespanel 25x50", "sløyfelekt 25x50", "lath 25x50"],
    },
    {
        "sku": "TIM-BATT-25100",
        "name": "Forskallingsbrædder 25x100mm ru",
        "category": "timber",
        "unit": "m",
        "weight_kg": 1.2,
        "requires_crane": False,
        "aliases": ["forskalling 25x100", "råspont 25x100", "underpanel 25x100", "battens 25x100"],
    },
    {
        "sku": "TIM-TERR-28120",
        "name": "Terrassebrædder imprægneret fyr NTR/AB 28x120mm",
        "category": "timber",
        "unit": "m",
        "weight_kg": 1.9,
        "requires_crane": False,
        "aliases": ["terrassebrædder 28x120", "trall tryckimpregnerad 28x120", "terrassebord impregnert 28x120", "decking treated pine 28x120"],
    },
    {
        "sku": "TIM-TERR-LARCH",
        "name": "Terrassebrædder sibirisk lærk 28x145mm",
        "category": "timber",
        "unit": "m",
        "weight_kg": 2.4,
        "requires_crane": False,
        "aliases": ["lærk terrasse 28x145", "lärktrall 28x145", "lerk terrassebord 28x145", "siberian larch decking 28x145"],
    },
    {
        "sku": "TIM-FASC-22150",
        "name": "Sternbrædder trykimprægneret 22x150mm",
        "category": "timber",
        "unit": "m",
        "weight_kg": 1.7,
        "requires_crane": False,
        "aliases": ["sternbræt 22x150", "vindskivebräda 22x150", "vindski 22x150", "fascia board treated 22x150"],
    },
    {
        "sku": "TIM-FASC-22200",
        "name": "Sternbrædder trykimprægneret 22x200mm",
        "category": "timber",
        "unit": "m",
        "weight_kg": 2.3,
        "requires_crane": False,
        "aliases": ["sternbræt 22x200", "vindskivebräda 22x200", "vindski 22x200", "fascia board treated 22x200"],
    },
    {
        "sku": "TIM-CLAD-22145",
        "name": "Klinkbeklædning gran grundet hvid 22x145mm",
        "category": "timber",
        "unit": "m",
        "weight_kg": 1.6,
        "requires_crane": False,
        "aliases": ["klinkbeklædning hvid", "ytterpanel grundmålad vit", "kledning hvit grunnet 22x145", "primed weatherboard 22x145"],
    },
    {
        "sku": "TIM-BEAM-GLULAM",
        "name": "Limtræsbjælke GL30c 115x360mm 6m",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 115.0,
        "requires_crane": True,
        "aliases": ["limtræ 115x360 6m", "limträbalk 115x360", "limtrebjelke gl30c 6m", "glulam beam 115x360 6m"],
    },
    {
        "sku": "TIM-BEAM-GLU2",
        "name": "Limtræsbjælke GL30c 140x400mm 8m",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 205.0,
        "requires_crane": True,
        "aliases": ["limtræ 140x400 8m", "limträbalk 140x400 8m", "limtrebjelke 140x400 8m", "glulam beam 140x400 8m"],
    },
    {
        "sku": "PLY-SPRU-12",
        "name": "Krydsfiner konstruktion 12mm 1220x2440",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 20.5,
        "requires_crane": False,
        "aliases": ["plywood 12mm", "kryssfinér 12mm", "structural plywood 12mm", "krydsfiner 12mm"],
    },
    {
        "sku": "PLY-SPRU-21",
        "name": "Krydsfiner konstruktion 21mm 1220x2440",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 36.5,
        "requires_crane": False,
        "aliases": ["plywood 21mm", "kryssfinér 21mm", "structural plywood 21mm", "krydsfiner 21mm"],
    },
    {
        "sku": "PLY-FILM-18",
        "name": "Støbekrydsfiner med film 18mm 1250x2500",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 34.0,
        "requires_crane": False,
        "aliases": ["støbekrydsfiner 18mm", "formplywood 18mm", "forskaling kryssfinér 18mm", "film faced formwork plywood 18mm"],
    },
    {
        "sku": "PLY-TRAIL-15",
        "name": "Trailerbund skridsikker wire mesh 15mm 1250x2500",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 30.0,
        "requires_crane": False,
        "aliases": ["trailerbund 15mm", "slitskiva halkfri 15mm", "tilhengerbunn sklisikker 15mm", "wire mesh plywood 15mm"],
    },
    {
        "sku": "OSB-3-12",
        "name": "OSB/3 plade TG2 fer og not 12mm 1220x2440",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 21.0,
        "requires_crane": False,
        "aliases": ["osb plade 12mm", "osb3 skiva 12mm", "osb plate 12mm", "osb 3 board 12mm"],
    },
    {
        "sku": "OSB-3-18",
        "name": "OSB/3 plade TG4 fer og not 18mm 1220x2440",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 32.0,
        "requires_crane": False,
        "aliases": ["osb plade 18mm tg4", "osb3 skiva 18mm spontad", "osb plate 18mm not og fjær", "osb 3 t&g 18mm"],
    },
    {
        "sku": "OSB-3-22",
        "name": "OSB/3 plade TG4 gulvplade 22mm 1220x2440",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 39.0,
        "requires_crane": False,
        "aliases": ["osb gulvplade 22mm", "osb golvskiva 22mm", "osb gulvplate 22mm", "osb 3 floor board 22mm"],
    },
    {
        "sku": "MDF-STD-16",
        "name": "MDF plade standard 16mm 1220x2440",
        "category": "timber",
        "unit": "stk",
        "weight_kg": 36.0,
        "requires_crane": False,
        "aliases": ["mdf plade 16mm", "mdf board 16mm", "mdf plate 16mm standard"],
    },

    # --- Insulation ---
    {
        "sku": "ISO-GLAS-050",
        "name": "Isolering glasuld rulle 50mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 1.2,
        "requires_crane": False,
        "aliases": ["glasuld 50mm", "glasull rulle 50mm", "glassull rull 50mm", "glass wool roll 50mm"],
    },
    {
        "sku": "ISO-GLAS-150",
        "name": "Isolering glasuld rulle 150mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 3.1,
        "requires_crane": False,
        "aliases": ["glasuld 150mm", "glasull rulle 150mm", "glassull rull 150mm", "glass wool roll 150mm"],
    },
    {
        "sku": "ISO-GLAS-200",
        "name": "Isolering glasuld rulle 200mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 4.1,
        "requires_crane": False,
        "aliases": ["glasuld 200mm", "glasull 200mm", "glassull rull 200mm", "glass wool 200mm"],
    },
    {
        "sku": "ISO-ROCK-050",
        "name": "Rockwool flexibatts 50mm 565x970mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 1.8,
        "requires_crane": False,
        "aliases": ["stenuld 50mm", "rockwool 50mm batts", "steinull 50mm", "rockwool flexibatts 50mm"],
    },
    {
        "sku": "ISO-ROCK-100",
        "name": "Rockwool flexibatts 100mm 565x970mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 3.2,
        "requires_crane": False,
        "aliases": ["stenuld 100mm", "rockwool 100mm flexibatts", "steinull batts 100mm", "rockwool insulation 100mm"],
    },
    {
        "sku": "ISO-ROCK-200",
        "name": "Rockwool flexibatts 200mm 565x970mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 6.2,
        "requires_crane": False,
        "aliases": ["stenuld 200mm", "rockwool 200mm", "steinull 200mm", "rockwool flexibatts 200mm"],
    },
    {
        "sku": "ISO-TERR-100",
        "name": "Terrænbatts hård stenuld 100mm 600x1000mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 8.5,
        "requires_crane": False,
        "aliases": ["terrænbatts 100mm", "markskiva stenull 100mm", "markplate steinull 100mm", "ground insulation slab 100mm"],
    },
    {
        "sku": "ISO-TERR-150",
        "name": "Terrænbatts hård stenuld 150mm 600x1000mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 12.8,
        "requires_crane": False,
        "aliases": ["terrænbatts 150mm", "markskiva 150mm", "markplate steinull 150mm", "ground slab insulation 150mm"],
    },
    {
        "sku": "ISO-EPS-80",
        "name": "Sundolitt EPS S80 isolering 100mm 1200x1200mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 1.6,
        "requires_crane": False,
        "aliases": ["flamingo 100mm eps", "cellplast eps s80 100mm", "isopor 100mm s80", "eps styrofoam slab 100mm"],
    },
    {
        "sku": "ISO-EPS-150",
        "name": "Sundolitt EPS S80 isolering 150mm 1200x1200mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 2.4,
        "requires_crane": False,
        "aliases": ["flamingo 150mm", "cellplast eps s80 150mm", "isopor 150mm", "eps styrofoam 150mm"],
    },
    {
        "sku": "ISO-XPS-300",
        "name": "Jackofoam XPS 300 50mm ekstruderet polystyren",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 1.8,
        "requires_crane": False,
        "aliases": ["xps 50mm", "cellplast xps 300 50mm", "jackofoam xps 50mm", "extruded polystyrene xps 50mm"],
    },
    {
        "sku": "ISO-PIPE-42",
        "name": "Rørisolering mineraluld 42mm med alufolie 1m",
        "category": "insulation",
        "unit": "m",
        "weight_kg": 0.4,
        "requires_crane": False,
        "aliases": ["rørskål mineraluld 42mm", "rörskål med alu 42mm", "rørisolasjon mineralull 42mm", "pipe insulation mineral wool 42mm"],
    },
    {
        "sku": "ISO-PIPE-28",
        "name": "Rørisolering cellegummi Armaflex 28mm 2m",
        "category": "insulation",
        "unit": "m",
        "weight_kg": 0.3,
        "requires_crane": False,
        "aliases": ["cellegummi rør 28mm", "armaflex rörisolering 28mm", "cellegummi isolasjon 28mm", "flexible rubber pipe insulation 28mm"],
    },
    {
        "sku": "ISO-SOUND-45",
        "name": "Lydisoleringsplade trinlyd 45mm 600x1000mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 4.8,
        "requires_crane": False,
        "aliases": ["trinlydisolering 45mm", "stegljudsisolering 45mm", "trinnlydplate 45mm", "sound acoustic insulation slab 45mm"],
    },
    {
        "sku": "ISO-FIRE-60",
        "name": "Brandisolering Conlit stenuld 60mm 600x1000mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 9.5,
        "requires_crane": False,
        "aliases": ["brandbatts conlit 60mm", "brandisolering stenull 60mm", "brannplate steinull 60mm", "fire protective rockwool 60mm"],
    },

    # --- Masonry, Cement, Mortar & Aggregates ---
    {
        "sku": "BET-FIN-25",
        "name": "Finbeton 0-4mm 25kg sæk",
        "category": "masonry",
        "unit": "sæk",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["finbeton 25kg", "finbetong 25kg", "finbetong sekk 25kg", "fine concrete dry mix 25kg"],
    },
    {
        "sku": "BET-GROV-25",
        "name": "Grovbeton 0-8mm 25kg sæk",
        "category": "masonry",
        "unit": "sæk",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["grovbeton 25kg", "grovbetong 25kg", "grovbetong sekk 25kg", "coarse concrete dry mix 25kg"],
    },
    {
        "sku": "BET-RAPID-25",
        "name": "Stolpebeton hurtighærdende 25kg sæk",
        "category": "masonry",
        "unit": "sæk",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["stolpebeton 25kg", "plintbetong snabb 25kg", "stolpebetong hurtig 25kg", "post concrete fast set 25kg"],
    },
    {
        "sku": "BET-STRAND-25",
        "name": "Strandmørtel 7.7% kalkmørtel 25kg sæk",
        "category": "masonry",
        "unit": "sæk",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["strandmørtel 25kg", "kalkbruk 25kg", "kalkmørtel 25kg", "sand lime mortar 25kg"],
    },
    {
        "sku": "BET-BAKKE-25",
        "name": "Bakkemørtel 5.1% opmuringsmørtel 25kg sæk",
        "category": "masonry",
        "unit": "sæk",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["bakkemørtel 25kg", "murbruk klass c 25kg", "muremørtel 25kg", "masonry mortar 25kg"],
    },
    {
        "sku": "BET-SEL-25",
        "name": "Selvnivellerende gulvspartel fiber 25kg sæk",
        "category": "masonry",
        "unit": "sæk",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["selvnivellerende spartel 25kg", "avjämningsmassa fiber 25kg", "avrettingsmasse fiber 25kg", "self levelling screed 25kg"],
    },
    {
        "sku": "BET-EXP-25",
        "name": "Ekspanderende undermuringstørtel 25kg",
        "category": "masonry",
        "unit": "sæk",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["undermuring 25kg", "expanderbruk 25kg", "ekspanderende mørtel 25kg", "non shrink grout 25kg"],
    },
    {
        "sku": "BRK-RED-MASSIV",
        "name": "Mursten blødstrøgen rød massiv 228x108x54mm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 2.5,
        "requires_crane": False,
        "aliases": ["rød mursten massiv", "tegel röd massiv", "rød teglstein massiv", "red clay solid brick"],
    },
    {
        "sku": "BRK-YEL-MASSIV",
        "name": "Mursten blødstrøgen gul massiv 228x108x54mm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 2.5,
        "requires_crane": False,
        "aliases": ["gul mursten massiv", "tegel gul massiv", "gul teglstein massiv", "yellow clay solid brick"],
    },
    {
        "sku": "BRK-GAS-100",
        "name": "Gasbeton porebetonblok 100x200x600mm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 7.5,
        "requires_crane": False,
        "aliases": ["gasbeton 100mm", "lättbetongblock 100mm", "porebetong 100mm", "aerated concrete block 100mm"],
    },
    {
        "sku": "BRK-GAS-150",
        "name": "Gasbeton porebetonblok 150x200x600mm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 11.2,
        "requires_crane": False,
        "aliases": ["gasbeton 150mm", "lättbetongblock 150mm", "porebetong 150mm", "aerated concrete block 150mm"],
    },
    {
        "sku": "BRK-LECA-10",
        "name": "Leca blok standard 10x19x49cm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 8.0,
        "requires_crane": False,
        "aliases": ["leca blok 10cm", "lättklinkerblock 10cm", "leca blokk 10cm", "lightweight aggregate block 10cm"],
    },
    {
        "sku": "BRK-LECA-15",
        "name": "Leca blok standard 15x19x49cm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 11.5,
        "requires_crane": False,
        "aliases": ["leca blok 15cm", "lättklinkerblock 15cm", "leca blokk 15cm", "lightweight aggregate block 15cm"],
    },
    {
        "sku": "BRK-LECA-20",
        "name": "Leca termblok isoleret 20x19x49cm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 13.0,
        "requires_crane": False,
        "aliases": ["leca termblok 20cm", "isoblock lättklinker 20cm", "isoblokk leca 20cm", "insulated leca block 20cm"],
    },
    {
        "sku": "AGG-SAND-BIG",
        "name": "Støbesand 0-4mm Bigbag 1000kg",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 1000.0,
        "requires_crane": True,
        "aliases": ["støbesand bigbag 1t", "gjutsand storsäck 1000kg", "støpesand storsekk 1000kg", "concrete sand big bag 1 ton"],
    },
    {
        "sku": "AGG-GRAV-BIG",
        "name": "Støbemix 0-16mm Bigbag 1000kg",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 1000.0,
        "requires_crane": True,
        "aliases": ["støbemix bigbag", "gjutgrus storsäck 1000kg", "støpemiks storsekk 1000kg", "all in aggregate ballast big bag 1000kg"],
    },
    {
        "sku": "AGG-SKÆRV-BIG",
        "name": "Granitskærver sort 11-16mm Bigbag 1000kg",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 1000.0,
        "requires_crane": True,
        "aliases": ["sorte granitskærver 1000kg", "svart granitskärv storsäck", "granittskjerv sort storsekk", "black granite chippings big bag 1000kg"],
    },

    # --- Reinforcement, Steel & Paving ---
    {
        "sku": "ARM-JERN-08",
        "name": "Armeringsjern kamstål B500B Ø8mm 6m",
        "category": "steel",
        "unit": "stk",
        "weight_kg": 2.4,
        "requires_crane": False,
        "aliases": ["kamstål 8mm", "armeringsstål 8mm", "rebar 8mm 6m", "armeringsjern 8mm"],
    },
    {
        "sku": "ARM-JERN-10",
        "name": "Armeringsjern kamstål B500B Ø10mm 6m",
        "category": "steel",
        "unit": "stk",
        "weight_kg": 3.7,
        "requires_crane": False,
        "aliases": ["kamstål 10mm", "armeringsstål 10mm", "rebar 10mm 6m", "armeringsjern 10mm"],
    },
    {
        "sku": "ARM-JERN-16",
        "name": "Armeringsjern kamstål B500B Ø16mm 6m",
        "category": "steel",
        "unit": "stk",
        "weight_kg": 9.5,
        "requires_crane": False,
        "aliases": ["kamstål 16mm", "armeringsstål 16mm", "rebar 16mm 6m", "armeringsjern 16mm"],
    },
    {
        "sku": "ARM-NET-0615",
        "name": "Rionet armeringsnet Ø6mm 150x150mm 2.15x5.0m",
        "category": "steel",
        "unit": "stk",
        "weight_kg": 24.0,
        "requires_crane": True,
        "aliases": ["rionet 6mm 150x150", "armeringsnät 6mm", "armeringsnett 6mm", "reinforcement steel mesh 6mm"],
    },
    {
        "sku": "ARM-NET-0815",
        "name": "Rionet armeringsnet Ø8mm 150x150mm 2.15x5.0m",
        "category": "steel",
        "unit": "stk",
        "weight_kg": 42.5,
        "requires_crane": True,
        "aliases": ["rionet 8mm 150x150", "armeringsnät 8mm", "armeringsnett 8mm", "reinforcement mesh 8mm"],
    },
    {
        "sku": "ARM-DIST-30",
        "name": "Afstandsholder plastik til armering 30mm pose á 100",
        "category": "steel",
        "unit": "pose",
        "weight_kg": 1.2,
        "requires_crane": False,
        "aliases": ["afstandsholder 30mm", "distanskloss armering 30mm", "avstandsholder armering 30mm", "rebar spacer chairs 30mm"],
    },
    {
        "sku": "ARM-BIND-TRD",
        "name": "Bindetråd glødet 1.2mm 200m rulle",
        "category": "steel",
        "unit": "rl",
        "weight_kg": 1.8,
        "requires_crane": False,
        "aliases": ["bindetråd 1.2mm", "najtråd 1.2mm", "bindetråd armering", "tie wire annealed 1.2mm"],
    },
    {
        "sku": "ARM-BEAM-IPE180",
        "name": "Stålbjælke IPE 180 S275JR længde 6m",
        "category": "steel",
        "unit": "stk",
        "weight_kg": 113.0,
        "requires_crane": True,
        "aliases": ["stålbjælke ipe 180 6m", "stålbalk ipe 180 6m", "stålbjelke ipe 180", "steel i-beam ipe 180 6m"],
    },
    {
        "sku": "STO-FLIS-30",
        "name": "Fortovsflise grå beton 30x30x5cm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 10.2,
        "requires_crane": False,
        "aliases": ["betonflise 30x30", "betongplatta 30x30x5", "helle grå betong 30x30", "concrete paving slab 30x30"],
    },
    {
        "sku": "STO-FLIS-40",
        "name": "Haveflise grå beton 40x40x5cm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 18.0,
        "requires_crane": False,
        "aliases": ["haveflise 40x40", "trädgårdsplatta 40x40", "hagehelle grå 40x40", "paving flag 40x40x5"],
    },
    {
        "sku": "STO-HERR-GRY",
        "name": "Herregårdssten grå 14x21x5.5cm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 3.6,
        "requires_crane": False,
        "aliases": ["herregårdssten", "marksten rustik grå", "belegningsstein grå", "interlocking paving stone gray"],
    },

    # --- Roofing, Cladding & Windows ---
    {
        "sku": "ROOF-TAG-BK",
        "name": "B&C Danflock betontagsten sortglaseret",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 4.2,
        "requires_crane": False,
        "aliases": ["tagsten sortglaseret", "betongpanna svart", "takstein betong sort", "black glazed concrete roof tile"],
    },
    {
        "sku": "ROOF-TAG-RED",
        "name": "B&C Danflock betontagsten teglrød",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 4.2,
        "requires_crane": False,
        "aliases": ["tagsten teglrød", "betongpanna tegelröd", "takstein rød betong", "red concrete roof tile"],
    },
    {
        "sku": "ROOF-RIDGE-BK",
        "name": "Rygningssten sortglaseret betontag",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 4.6,
        "requires_crane": False,
        "aliases": ["rygningssten sort", "nockpanna svart", "mønestein betong sort", "ridge tile black glazed"],
    },
    {
        "sku": "ROOF-PAP-UND",
        "name": "Tagpap underpap selvklæbende PF3500 1x7m",
        "category": "roofing",
        "unit": "rl",
        "weight_kg": 25.0,
        "requires_crane": False,
        "aliases": ["underpap selvklæbende", "underlagsduk underlagspapp 1x7m", "underlagsbelegg sbs 1x7m", "underlay bitumen roofing membrane"],
    },
    {
        "sku": "ROOF-PAP-TOP",
        "name": "Tagpap overpap SBS med skifergrus sort 1x5m",
        "category": "roofing",
        "unit": "rl",
        "weight_kg": 24.5,
        "requires_crane": False,
        "aliases": ["overpap skifergrus", "ytskiktspapp sbs skiffer", "overlagsbelegg skifer 1x5m", "top layer mineral bitumen membrane"],
    },
    {
        "sku": "ROOF-GUT-ZINC",
        "name": "Zink tagrende halvrund 11 tommer 3m",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 3.8,
        "requires_crane": False,
        "aliases": ["zink tagrende 3m", "zinkhängränna 11 tum 3m", "sink takrenne 3m", "zinc gutter half round 3m"],
    },
    {
        "sku": "ROOF-GUT-PLAS",
        "name": "Plastmo tagrende hvid plast nr 11 3m",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 1.4,
        "requires_crane": False,
        "aliases": ["plastmo tagrende hvid 3m", "hängränna vit plast 3m", "plast takrenne hvit 3m", "pvc white gutter 3m"],
    },
    {
        "sku": "ROOF-GUT-BRK",
        "name": "Rendejern zink 11 tommer kort",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 0.4,
        "requires_crane": False,
        "aliases": ["rendejern zink", "rännkrok zink", "rennekrok sink", "zinc gutter bracket short"],
    },
    {
        "sku": "FAC-FIB-BOARD",
        "name": "HardiePlank fibercement facadebeklædning sort 8x180x3600mm",
        "category": "facade",
        "unit": "stk",
        "weight_kg": 7.4,
        "requires_crane": False,
        "aliases": ["hardieplank sort", "fibercementskiva svart fasad", "fibercement kledning sort", "hardieplank facade plank black"],
    },
    {
        "sku": "FAC-CEDAR-18",
        "name": "Western Red Cedar facadebeklædning 18x145mm",
        "category": "facade",
        "unit": "m",
        "weight_kg": 1.2,
        "requires_crane": False,
        "aliases": ["cedertræ beklædning", "cederpanel fasad", "sedertre kledning", "western red cedar cladding"],
    },
    {
        "sku": "WIN-FLASH-78",
        "name": "Velux Inddækning EDW MK08 til bølget tag",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 5.2,
        "requires_crane": False,
        "aliases": ["velux inddækning edw mk08", "intäckningsplåt velux mk08", "inndekning velux edw mk08", "velux flashing edw mk08"],
    },
    {
        "sku": "ROOF-HATCH-60",
        "name": "Tagadgangslem isoleret 60x60cm",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 14.5,
        "requires_crane": False,
        "aliases": ["taglem 60x60", "taktillträdeslucka 60x60", "takkrokluke isolert 60x60", "insulated roof access hatch 60x60"],
    },

    # --- Fasteners, Screws, Anchors & Fittings ---
    {
        "sku": "SCR-GIP-25",
        "name": "Gipsskruer 3.9x25mm til stålprofil",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 0.8,
        "requires_crane": False,
        "aliases": ["gipsskruer 25mm stål", "gipsskruv för stålregel 25mm", "gipsskrue stål 25mm", "drywall screws steel 25mm"],
    },
    {
        "sku": "SCR-GIP-55",
        "name": "Gipsskruer 3.9x55mm til dobbelt lag gips",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 1.5,
        "requires_crane": False,
        "aliases": ["gipsskruer 55mm", "gipsskruv två lag 55mm", "gipsskrue dobbeltlag 55mm", "drywall screws double layer 55mm"],
    },
    {
        "sku": "SCR-TER-75",
        "name": "Terrasseskrue rustfri A4 4.8x75mm",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 1.9,
        "requires_crane": False,
        "aliases": ["trallskruv rostfri a4 75mm", "terrasseskrue a4 75mm", "decking screws stainless 75mm"],
    },
    {
        "sku": "SCR-WOOD-580",
        "name": "Træskrue undersænket TX20 5.0x80mm gulforzinket",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 1.2,
        "requires_crane": False,
        "aliases": ["træskrue 5x80", "träskruv tx20 5x80", "treskrue forsenket 5x80", "wood screw tx20 5x80"],
    },
    {
        "sku": "SCR-WOOD-5100",
        "name": "Træskrue delgevind TX25 5.0x100mm",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 1.6,
        "requires_crane": False,
        "aliases": ["træskruer 5x100", "träskruv delgängad 5x100", "treskrue delgjenget 5x100", "wood screws partial thread 5x100"],
    },
    {
        "sku": "SCR-WOOD-6120",
        "name": "Konstruktionsskrue fladhoved TX30 6.0x120mm",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 2.2,
        "requires_crane": False,
        "aliases": ["konstruktionsskrue 6x120", "tallrikskrruv 6x120", "konstruksjonsskrue 6x120", "structural timber screw washer head 6x120"],
    },
    {
        "sku": "SCR-FAC-48",
        "name": "Facadeskrue lakeret sort TX20 4.8x38mm",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 0.9,
        "requires_crane": False,
        "aliases": ["facadeskrue sort 38mm", "fasadskruv lackerad svart", "fasadeskrue sort lakkert", "black painted facade screw 4.8x38"],
    },
    {
        "sku": "SCR-BET-75",
        "name": "Betonskrue fladhoved uden plug 7.5x72mm",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 1.8,
        "requires_crane": False,
        "aliases": ["betonskrue 7.5x72", "betongskruv 7.5x72", "betongskrue pluggfri 7.5x72", "concrete screw anchor 7.5x72"],
    },
    {
        "sku": "NAI-GUN-34",
        "name": "Pistolsøm 34 grader ringsøm 2.8x75mm varmgalv",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 6.8,
        "requires_crane": False,
        "aliases": ["pistolsøm 34 gr 2.8x75", "spikstav 34 grader galv 75mm", "stavspiker 34 grader 75mm", "collated framing nails 34 deg 75mm"],
    },
    {
        "sku": "NAI-GUN-90",
        "name": "Pistolsøm 34 grader ringsøm 3.1x90mm blank",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 8.4,
        "requires_crane": False,
        "aliases": ["pistolsøm 90mm", "spikstav 90mm blank", "stavspiker 90mm ugalvanisert", "framing nails 34 deg 90mm"],
    },
    {
        "sku": "FIT-ANG-90",
        "name": "Vinkelbeslag med ribbe forstærket 90x90x65mm",
        "category": "fasteners",
        "unit": "stk",
        "weight_kg": 0.2,
        "requires_crane": False,
        "aliases": ["vinkelbeslag med ribbe 90mm", "vinkelbeslag förstärkt 90x90", "vinkelbeslag forsterket 90x90", "reinforced angle bracket 90x90"],
    },
    {
        "sku": "FIT-ANG-70",
        "name": "Vinkelbeslag standard uden ribbe 70x70x55mm",
        "category": "fasteners",
        "unit": "stk",
        "weight_kg": 0.15,
        "requires_crane": False,
        "aliases": ["vinkelbeslag 70x70", "vinkeljärn 70x70", "vinkelbeslag 70mm", "angle bracket 70x70"],
    },
    {
        "sku": "FIT-PLT-100",
        "name": "Hulplade forzinket 2.0mm 100x240mm",
        "category": "fasteners",
        "unit": "stk",
        "weight_kg": 0.35,
        "requires_crane": False,
        "aliases": ["hulplade 100x240", "spikplåt 100x240", "hullplate galv 100x240", "flat mending tie plate 100x240"],
    },
    {
        "sku": "FIT-BEAM-51",
        "name": "Bjælkesko udvendige flige 51x135mm",
        "category": "fasteners",
        "unit": "stk",
        "weight_kg": 0.45,
        "requires_crane": False,
        "aliases": ["bjælkesko 51mm", "balksko utvändiga flikar 51x135", "bjelkesko utvendig 51x135", "joist hanger 51x135"],
    },
    {
        "sku": "FIT-BEAM-45",
        "name": "Bjælkesko indvendige flige 45x137mm",
        "category": "fasteners",
        "unit": "stk",
        "weight_kg": 0.42,
        "requires_crane": False,
        "aliases": ["bjælkesko indvendig 45mm", "balksko invändiga flikar 45mm", "bjelkesko innvendig 45mm", "joist hanger concealed flange 45mm"],
    },
    {
        "sku": "ANC-EXP-10",
        "name": "Ekspansionsbolt M10 10x90mm elforzinket",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 1.2,
        "requires_crane": False,
        "aliases": ["ekspansionsbolt m10", "expanderbult m10x90", "ekspansjonsbolt m10", "wedge expansion anchor bolt m10x90"],
    },
    {
        "sku": "ANC-NYL-8",
        "name": "Fischer Duopower universalplugs 8x40mm pk á 100",
        "category": "fasteners",
        "unit": "pk",
        "weight_kg": 0.3,
        "requires_crane": False,
        "aliases": ["fischer duopower 8mm", "universalplugg 8x40", "dybel ficher 8x40", "nylon wall plugs duopower 8x40"],
    },
    {
        "sku": "ANC-CHEM-300",
        "name": "Injektionsmørtel klæbeanker kemisk anker 300ml",
        "category": "fasteners",
        "unit": "stk",
        "weight_kg": 0.6,
        "requires_crane": False,
        "aliases": ["kemisk anker 300ml", "ankarmassa 300ml", "injeksjonsmørtel 300ml", "chemical injection mortar resin 300ml"],
    },

    # --- Plumbing, Drainage & MEP ---
    {
        "sku": "PIP-PVC-110-3M",
        "name": "Afløbsrør PVC grå Ø110mm 3m med muffe",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 4.1,
        "requires_crane": False,
        "aliases": ["afløbsrør 110mm 3m", "avloppsrör grå 110 3m", "avløpsrør 110 3m muffe", "pvc drainage pipe 110mm 3m"],
    },
    {
        "sku": "PIP-PVC-75",
        "name": "Afløbsrør PVC grå Ø75mm 2m med muffe",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 1.9,
        "requires_crane": False,
        "aliases": ["afløbsrør 75mm 2m", "avloppsrör 75mm 2m", "avløpsrør 75mm muffe", "pvc drainage pipe 75mm 2m"],
    },
    {
        "sku": "PIP-PVC-50",
        "name": "Afløbsrør PVC grå Ø50mm 2m med muffe",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 1.2,
        "requires_crane": False,
        "aliases": ["afløbsrør 50mm 2m", "avloppsrör 50mm 2m", "avløpsrør 50mm", "pvc drainage pipe 50mm 2m"],
    },
    {
        "sku": "PIP-BEN-110-45",
        "name": "Afløbsbøjning PVC Ø110mm 45 grader",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 0.45,
        "requires_crane": False,
        "aliases": ["afløbsbøjning 110mm 45 gr", "avloppsböj 110mm 45 grader", "avløpsbend 110 45 grader", "pvc pipe bend 110mm 45 deg"],
    },
    {
        "sku": "PIP-BEN-110-88",
        "name": "Afløbsbøjning PVC Ø110mm 88.5 grader",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 0.52,
        "requires_crane": False,
        "aliases": ["afløbsbøjning 110mm 90 gr", "avloppsböj 110mm 88 grader", "avløpsbend 110 88 grader", "pvc pipe elbow 110mm 88 deg"],
    },
    {
        "sku": "PIP-PEX-15",
        "name": "PEX rør-i-rør til brugsvand 15mm 50m rulle",
        "category": "plumbing",
        "unit": "rl",
        "weight_kg": 6.8,
        "requires_crane": False,
        "aliases": ["pex rør i rør 15mm", "pex rör-i-rör 15mm 50m", "pex rør i varerør 15mm", "pex pipe in pipe potable water 15mm 50m"],
    },
    {
        "sku": "PIP-PEX-20",
        "name": "PEX rør gulvvarme 20x2.0mm 120m rulle",
        "category": "plumbing",
        "unit": "rl",
        "weight_kg": 18.5,
        "requires_crane": False,
        "aliases": ["gulvvarmerør 20mm 120m", "golvvärmerör pex 20mm 120m", "gulvvarmerør pex 20mm", "underfloor heating pex pipe 20mm 120m"],
    },
    {
        "sku": "DRA-WELL-315",
        "name": "Tagnedløbsbrønd med sandfang plast Ø315mm",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 8.5,
        "requires_crane": False,
        "aliases": ["sandfangsbrønd 315mm", "dagvattenbrunn med sandfång 315", "sandfangskumme 315mm", "gully storm drainage well with silt bucket 315mm"],
    },
    {
        "sku": "DRA-CORR-110",
        "name": "Drænrør korrugeret med geotekstilfilter Ø110mm 50m",
        "category": "plumbing",
        "unit": "rl",
        "weight_kg": 14.0,
        "requires_crane": False,
        "aliases": ["drænrør med filter 110mm", "dräneringsrör med geotextil 110mm", "drensrør med filter 110mm", "perforated geotextile drainage pipe 110mm 50m"],
    },
    {
        "sku": "DRA-CHAN-1M",
        "name": "Linjedræn polymerbeton med galvaniseret rist 1m",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 7.8,
        "requires_crane": False,
        "aliases": ["linjedræn 1m", "avvattningsränna 1m galv galler", "drenskanal linjedren 1m", "trench channel drain polymer concrete 1m"],
    },
    {
        "sku": "DRA-GULLY-150",
        "name": "Gulvafløb plast med rustfri rist 150x150mm",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 1.1,
        "requires_crane": False,
        "aliases": ["gulvafløb 150x150", "golvbrunn med rostfri sil 150x150", "sluk med rustfri rist 150x150", "floor drain gully stainless grate 150x150"],
    },
    {
        "sku": "PIP-ISOF-32",
        "name": "Isoleret vandstikledning PE Ø32mm 50m",
        "category": "plumbing",
        "unit": "rl",
        "weight_kg": 26.0,
        "requires_crane": False,
        "aliases": ["isoleret pel rør 32mm", "isolerat pe rör 32mm", "isolert vannledning pe 32mm", "pre-insulated ground water pipe 32mm 50m"],
    },
    {
        "sku": "PIP-VALV-BALL",
        "name": "Kuglehane med greb messing 3/4 tomme",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 0.45,
        "requires_crane": False,
        "aliases": ["kuglehane 3/4", "kulventil mässing 3/4 tum", "kuleventil messing 3/4", "brass ball valve full bore 3/4 inch"],
    },
    {
        "sku": "PIP-MANIF-4",
        "name": "Gulvvarmemanifold 4 kredse med flowmåler",
        "category": "plumbing",
        "unit": "stk",
        "weight_kg": 3.8,
        "requires_crane": False,
        "aliases": ["gulvvarmeshunt manifold 4 kredse", "golvvärmefördelare 4 slingor", "gulvvarme samlestokk 4 kurser", "underfloor heating manifold 4 port with flow meters"],
    },

    # --- Paints, Membranes, Sealants & Chemicals ---
    {
        "sku": "FUG-SIL-SAN",
        "name": "Sanitets silikone fugemasse mugresistent klar 300ml",
        "category": "chemicals",
        "unit": "stk",
        "weight_kg": 0.4,
        "requires_crane": False,
        "aliases": ["sanitetssilikone klar 300ml", "våtrumssilikon transparent", "våtromssilikon klar 300ml", "sanitary silicone sealant clear 300ml"],
    },
    {
        "sku": "FUG-MS-POLY",
        "name": "MS Polymer montagelim hybrid sort 290ml",
        "category": "chemicals",
        "unit": "stk",
        "weight_kg": 0.55,
        "requires_crane": False,
        "aliases": ["montagelim sort 290ml", "monteringslim ms polymer svart", "monteringslim hybrid sort", "ms polymer high tack adhesive black 290ml"],
    },
    {
        "sku": "FUG-PU-FOAM",
        "name": "PU Pistolskum helårs isoleringsskum 750ml",
        "category": "chemicals",
        "unit": "stk",
        "weight_kg": 0.95,
        "requires_crane": False,
        "aliases": ["pistolskum helår 750ml", "fogskum pistol allround 750ml", "fugeskum pistol helårs", "expanding pu foam gun grade 750ml"],
    },
    {
        "sku": "MEM-VAP-02",
        "name": "Dampspærre folie godkendt 0.20mm 2x50m 100m2",
        "category": "membranes",
        "unit": "rl",
        "weight_kg": 18.5,
        "requires_crane": False,
        "aliases": ["dampspærre 0.20mm", "ångspärr plastfolie 0.20mm 2x50m", "dampsperre pe-folie 0.20mm", "vapor barrier pe foil 0.20mm 100m2"],
    },
    {
        "sku": "MEM-WATH-1K",
        "name": "Vådrumsmembran 1-komponent smøremembran 15kg",
        "category": "membranes",
        "unit": "spand",
        "weight_kg": 15.0,
        "requires_crane": False,
        "aliases": ["vådrumsmembran 15kg", "tätskikt våtrumsmembran 15kg", "smøremembran våtrom 15kg", "liquid waterproofing membrane bathroom 15kg"],
    },
    {
        "sku": "MEM-BAND-120",
        "name": "Vådrumsbånd tætningsbånd elastisk 120mm 50m",
        "category": "membranes",
        "unit": "rl",
        "weight_kg": 2.2,
        "requires_crane": False,
        "aliases": ["vådrumsbånd 50m", "tätningsband våtrum 120mm", "tetningsbånd våtrom 120mm", "sealing strip waterproof tape 120mm 50m"],
    },
    {
        "sku": "PAI-WALL-10",
        "name": "Vægmaling glans 10 råhvid 10L spand",
        "category": "chemicals",
        "unit": "spand",
        "weight_kg": 14.5,
        "requires_crane": False,
        "aliases": ["vægmaling glans 10 10l", "väggfärg glans 10 råvit 10l", "veggmaling glans 10 10l", "interior wall paint silk matt off-white 10l"],
    },
    {
        "sku": "PAI-CEIL-02",
        "name": "Loftmaling helmat refleksfri glans 2 hvid 10L",
        "category": "chemicals",
        "unit": "spand",
        "weight_kg": 15.0,
        "requires_crane": False,
        "aliases": ["loftmaling glans 2 10l", "takfärg helmatt vit 10l", "takmaling helmatt hvit 10l", "ceiling paint dead matt white 10l"],
    },
    {
        "sku": "PAI-EXT-FAC",
        "name": "Facademaling silikoneharpiks hvid 10L",
        "category": "chemicals",
        "unit": "spand",
        "weight_kg": 14.8,
        "requires_crane": False,
        "aliases": ["facademaling hvid 10l", "fasadfärg silikonharts vit 10l", "fasademaling hvit 10l", "exterior silicone facade paint white 10l"],
    },
    {
        "sku": "PAI-WOOD-OIL",
        "name": "Træbeskyttelse oliebaseret nøddebrun 5L",
        "category": "chemicals",
        "unit": "dunk",
        "weight_kg": 5.2,
        "requires_crane": False,
        "aliases": ["træbeskyttelse nøddebrun 5l", "trälasyr brun 5l", "trebeskyttelse nøttebrun 5l", "wood stain oil solvent based walnut 5l"],
    },
    {
        "sku": "CHM-CONC-SEAL",
        "name": "Betonforsegler og støvbinder vandbaseret 5L",
        "category": "chemicals",
        "unit": "dunk",
        "weight_kg": 5.1,
        "requires_crane": False,
        "aliases": ["støvbinder beton 5l", "dammbindare betong 5l", "støvbinder betong 5l", "concrete sealer dustproofer 5l"],
    },
    {
        "sku": "CHM-PRIM-UNIV",
        "name": "Primer universal hæftegrunder 5L",
        "category": "chemicals",
        "unit": "dunk",
        "weight_kg": 5.2,
        "requires_crane": False,
        "aliases": ["primer universal 5l", "fästprimer universell 5l", "hefteprimer 5l", "universal bonding primer 5l"],
    },

    # --- Safety, Site Equipment & Electrical ---
    {
        "sku": "SAF-FENC-MOB",
        "name": "Byggepladshegn mobilt galvaniseret 3.5x2.0m",
        "category": "site_equipment",
        "unit": "stk",
        "weight_kg": 14.5,
        "requires_crane": True,
        "aliases": ["byggepladshegn mobil 3.5m", "byggstängsel mobilt 3.5x2.0", "byggegjerde mobilt 3.5m", "temporary mobile construction fence 3.5x2.0m"],
    },
    {
        "sku": "SAF-BASE-CON",
        "name": "Betonfod til byggepladshegn 28kg",
        "category": "site_equipment",
        "unit": "stk",
        "weight_kg": 28.0,
        "requires_crane": False,
        "aliases": ["betonfod hegn", "betongfot byggstängsel 28kg", "betongfot byggegjerde 28kg", "concrete fence base foot 28kg"],
    },
    {
        "sku": "SAF-COV-FLOR",
        "name": "Afdækningspap tung kvalitet 1x30m 180g/m2",
        "category": "site_equipment",
        "unit": "rl",
        "weight_kg": 5.4,
        "requires_crane": False,
        "aliases": ["afdækningspap 30m", "täckpapp golvskydd 30m", "gulvpapp 1x30m", "heavy floor protection cardboard roll 1x30m"],
    },
    {
        "sku": "SAF-COV-PLAS",
        "name": "Afdækningsfolie klar LDPE 4x25m 80my",
        "category": "site_equipment",
        "unit": "rl",
        "weight_kg": 7.4,
        "requires_crane": False,
        "aliases": ["afdækningsfolie 4x25m", "täckfolie plast 4x25m", "bygningsfolie 4x25m", "protective polythene sheet 4x25m 80mu"],
    },
    {
        "sku": "SAF-DUST-SHE",
        "name": "Støvvæg teleskopstang sæt á 4 stænger",
        "category": "site_equipment",
        "unit": "sæt",
        "weight_kg": 8.0,
        "requires_crane": False,
        "aliases": ["støvvæg stænger", "dammvägg teleskopstänger set", "støvvegg teleskopstenger", "zipwall dust barrier poles kit 4-pack"],
    },
    {
        "sku": "ELE-CAB-3G15",
        "name": "Installationskabel NOIKX 3G1.5mm2 100m tromle",
        "category": "electrical",
        "unit": "rl",
        "weight_kg": 11.2,
        "requires_crane": False,
        "aliases": ["installationskabel 3g1.5 100m", "installationskabel eklk 3g1.5", "installasjonskabel 3g1.5 100m", "electrical installation cable 3g1.5mm2 100m"],
    },
    {
        "sku": "ELE-CAB-5G25",
        "name": "Kraftkabel NOIKX 5G2.5mm2 50m tromle",
        "category": "electrical",
        "unit": "rl",
        "weight_kg": 14.8,
        "requires_crane": False,
        "aliases": ["kraftkabel 5g2.5 50m", "kraftkabel eklk 5g2.5", "installasjonskabel 5g2.5 50m", "power cable 5g2.5mm2 50m"],
    },
    {
        "sku": "ELE-CON-FLEX",
        "name": "Flexrør korrugeret tomrør Ø16mm 100m",
        "category": "electrical",
        "unit": "rl",
        "weight_kg": 4.5,
        "requires_crane": False,
        "aliases": ["flexrør 16mm 100m", "flexrör korrugerat 16mm", "k-rør trekkerør 16mm 100m", "corrugated conduit flexible pipe 16mm 100m"],
    },
    {
        "sku": "TOO-DIAM-230",
        "name": "Diamantskæreskive beton Ø230x22.2mm",
        "category": "tools",
        "unit": "stk",
        "weight_kg": 0.8,
        "requires_crane": False,
        "aliases": ["diamantskive 230mm beton", "diamantklinga betong 230mm", "diamantblad betong 230mm", "diamond blade concrete 230mm"],
    },
    {
        "sku": "TOO-SAW-BLAD",
        "name": "Rundsavsklinge hårdmetal Ø190x30mm 40T",
        "category": "tools",
        "unit": "stk",
        "weight_kg": 0.45,
        "requires_crane": False,
        "aliases": ["rundsavsklinge 190mm", "cirkelsågklinga 190x30", "sirkelsagblad 190mm 40t", "circular saw blade carbide 190mm"],
    },

    # --- CROSS-BORDER RARE ITEMS (Special Nordic stock exclusive to single countries) ---
    {
        "sku": "TIM-SE-PINE45",
        "name": "Svensk Furu Kärnvirke Norrland 45x195mm C30",
        "category": "timber",
        "unit": "m",
        "weight_kg": 4.6,
        "requires_crane": False,
        "aliases": ["svensk furu 45x195", "norrländsk kärnfuru 45x195", "svensk kjernefuru 45x195", "swedish norrland heartwood pine 45x195"],
    },
    {
        "sku": "STO-SE-GRANITE",
        "name": "Bohuslän Granit Kantsten grå råhugget 1000x300x150mm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 122.0,
        "requires_crane": True,
        "aliases": ["bohus granit kantsten 1m", "bohuslän kantsten granit råhuggen", "bohus granitt kantstein 100cm", "bohus swedish granite kerbstone 1m"],
    },
    {
        "sku": "ARM-BEAM-HEA200",
        "name": "Stålbjælke HEA 200 S355J2 6m bjælke",
        "category": "steel",
        "unit": "stk",
        "weight_kg": 254.0,
        "requires_crane": True,
        "aliases": ["hea 200 stålbjælke 6m", "stålbalk hea 200 6m", "hea 200 stålbjelke 6m", "structural steel beam hea 200 6m"],
    },
    {
        "sku": "ROOF-NO-SLATE",
        "name": "Alta Skifer Takstein naturkant 300x400mm Norsk",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 5.8,
        "requires_crane": False,
        "aliases": ["alta skifer tagsten 30x40", "alta skiffer takplatta", "alta skifertakstein 300x400", "norwegian alta natural slate roof tile 300x400"],
    },
    {
        "sku": "CHM-NO-ARCTIC",
        "name": "Hey'di Frostsikker Arktisk Membran 20kg",
        "category": "chemicals",
        "unit": "spand",
        "weight_kg": 20.0,
        "requires_crane": False,
        "aliases": ["heydi frostsikker membran 20kg", "arktisk membran heydi", "frostsikker tetningsmembran 20kg", "arctic frostproof waterproofing membrane 20kg"],
    },
    {
        "sku": "INS-NO-ECOWOOL",
        "name": "Glava Proff 34 Norsk Miljø Glassull Rull 150mm",
        "category": "insulation",
        "unit": "m2",
        "weight_kg": 3.4,
        "requires_crane": False,
        "aliases": ["glava proff 34 150mm", "glava glassull norge 150mm", "norsk glava isolasjon 150mm", "glava proff 34 insulation roll 150mm"],
    },
    {
        "sku": "BRK-DK-CPHRED",
        "name": "Flensborg Mursten Rød Håndstrøget Historisk 228x108x54mm",
        "category": "masonry",
        "unit": "stk",
        "weight_kg": 2.6,
        "requires_crane": False,
        "aliases": ["flensborgsten rød håndstrøget", "dansk rött handslaget tegel", "flensburger rød håndstrøket tegl", "danish handmade flensburg red facing brick"],
    },
    {
        "sku": "WIN-DK-VELUX78",
        "name": "Velux Tagvindue GGL MK08 2070 3-lags thermo 78x140cm",
        "category": "roofing",
        "unit": "stk",
        "weight_kg": 38.0,
        "requires_crane": False,
        "aliases": ["velux ggl mk08 78x140", "takfönster velux mk08 3-glas", "velux takvindu 78x140 3-lags", "velux roof window ggl mk08 triple glazed 78x140"],
    },
]

# Expand to reach 160+ items by generating systematic variants of standard profiles/timbers
def generate_systematic_variants():
    variants = []
    
    # 1. Structural timber lengths: C24 Spruce in standard lengths (3.6m, 4.2m, 4.8m, 5.4m)
    timber_sizes = [
        ("45x95", "TIM-SPRU-45095", 2.1),
        ("45x120", "TIM-SPRU-45120", 2.6),
        ("45x145", "TIM-SPRU-45145", 3.2),
        ("45x170", "TIM-SPRU-45170", 3.7),
        ("45x195", "TIM-SPRU-45195", 4.3),
        ("45x220", "TIM-SPRU-45220", 4.9),
        ("45x245", "TIM-SPRU-45245", 5.5),
        ("70x195", "TIM-SPRU-70195", 6.8),
    ]
    lengths = [(36, "3.6m"), (42, "4.2m"), (48, "4.8m"), (54, "5.4m")]
    for dim, code_prefix, unit_wt in timber_sizes:
        for l_code, l_label in lengths:
            sku = f"{code_prefix}-{l_code}"
            name = f"Konstruktionstræ C24 {dim}mm høvlet {l_label}"
            aliases = [
                f"spærtræ {dim} {l_label}",
                f"regel {dim} {l_label}",
                f"konstruksjonsvirke {dim} {l_label}",
                f"c24 timber {dim} {l_label}",
            ]
            wt = round(unit_wt * (l_code / 10), 1)
            variants.append({
                "sku": sku,
                "name": name,
                "category": "timber",
                "unit": "stk",
                "weight_kg": wt,
                "requires_crane": False,
                "aliases": aliases,
            })

    # 2. Rebar lengths & mesh variants
    mesh_variants = [
        ("ARM-NET-0515", "Rionet armeringsnet Ø5mm 150x150mm 2.15x5.0m", 16.5, True, ["rionet 5mm", "armeringsnät 5mm", "armeringsnett 5mm"]),
        ("ARM-NET-1015", "Rionet armeringsnet Ø10mm 150x150mm 2.15x5.0m", 66.0, True, ["rionet 10mm tung", "armeringsnät 10mm grov", "armeringsnett 10mm"]),
        ("ARM-NET-1215", "Rionet armeringsnet Ø12mm 150x150mm 2.15x5.0m", 95.0, True, ["rionet 12mm ekstra tung", "armeringsnät 12mm", "armeringsnett 12mm"]),
    ]
    for sku, name, wt, req_crane, aliases in mesh_variants:
        variants.append({
            "sku": sku,
            "name": name,
            "category": "steel",
            "unit": "stk",
            "weight_kg": wt,
            "requires_crane": req_crane,
            "aliases": aliases,
        })

    # 3. Steel profile length variants (4000mm)
    steel_profs = [
        ("GYP-PROF-U70-4M", "Stålprofil U-skinne 70mm 4000mm", 3.2, ["u-skinne 70mm 4m", "stålregel u70 4m"]),
        ("GYP-PROF-C70-4M", "Stålprofil C-stolpe 70mm 4000mm", 3.6, ["c-stolpe 70mm 4m", "stålregel c70 4m"]),
        ("GYP-PROF-U95-4M", "Stålprofil U-skinne 95mm 4000mm", 4.1, ["u-skinne 95mm 4m", "stålregel u95 4m"]),
        ("GYP-PROF-C95-4M", "Stålprofil C-stolpe 95mm 4000mm", 4.5, ["c-stolpe 95mm 4m", "stålregel c95 4m"]),
        ("GYP-PROF-U120", "Stålprofil U-skinne 120mm 3000mm", 3.8, ["u-skinne 120mm", "stålregel u120"]),
        ("GYP-PROF-C120", "Stålprofil C-stolpe 120mm 3000mm", 4.3, ["c-stolpe 120mm", "stålregel c120"]),
    ]
    for sku, name, wt, aliases in steel_profs:
        variants.append({
            "sku": sku,
            "name": name,
            "category": "drywall",
            "unit": "stk",
            "weight_kg": wt,
            "requires_crane": False,
            "aliases": aliases,
        })

    # 4. Drainage pipe lengths & junctions
    pipes = [
        ("PIP-PVC-160-2M", "Afløbsrør PVC grå Ø160mm 2m med muffe", 5.8, ["afløbsrør 160mm 2m", "avloppsrör 160mm 2m"]),
        ("PIP-PVC-160-3M", "Afløbsrør PVC grå Ø160mm 3m med muffe", 8.6, ["afløbsrør 160mm 3m", "avloppsrör 160mm 3m"]),
        ("PIP-BEN-160-45", "Afløbsbøjning PVC Ø160mm 45 grader", 1.2, ["afløbsbøjning 160 45 gr", "avloppsböj 160mm 45 grader"]),
        ("PIP-BEN-160-88", "Afløbsbøjning PVC Ø160mm 88.5 grader", 1.5, ["afløbsbøjning 160 88 gr", "avloppsböj 160mm 88 grader"]),
        ("PIP-RED-160110", "Afløbsreduktion PVC Ø160/110mm excentrisk", 0.8, ["afløbsreduktion 160 110", "övergångsrör 160 110"]),
    ]
    for sku, name, wt, aliases in pipes:
        variants.append({
            "sku": sku,
            "name": name,
            "category": "plumbing",
            "unit": "stk",
            "weight_kg": wt,
            "requires_crane": False,
            "aliases": aliases,
        })

    # 5. Fastener pack size variants
    screws = [
        ("SCR-WOOD-440", "Træskrue undersænket TX20 4.0x40mm pk á 500", 1.1, ["træskrue 4x40", "träskruv 4x40"]),
        ("SCR-WOOD-450", "Træskrue undersænket TX20 4.0x50mm pk á 500", 1.3, ["træskrue 4x50", "träskruv 4x50"]),
        ("SCR-WOOD-460", "Træskrue undersænket TX20 4.0x60mm pk á 500", 1.5, ["træskrue 4x60", "träskruv 4x60"]),
        ("SCR-WOOD-560", "Træskrue undersænket TX20 5.0x60mm pk á 200", 1.0, ["træskrue 5x60", "träskruv 5x60"]),
        ("SCR-WOOD-570", "Træskrue undersænket TX20 5.0x70mm pk á 200", 1.1, ["træskrue 5x70", "träskruv 5x70"]),
        ("SCR-ROOF-48", "Tagskrue selvborende med skive 4.8x35mm pk á 250", 1.2, ["tagskrue 4.8x35", "farmarskruv 4.8x35"]),
    ]
    for sku, name, wt, aliases in screws:
        variants.append({
            "sku": sku,
            "name": name,
            "category": "fasteners",
            "unit": "pk",
            "weight_kg": wt,
            "requires_crane": False,
            "aliases": aliases,
        })

    return variants


# 2. WAREHOUSES DEFINITION (15 Warehouses: 5 in DK, 5 in SE, 5 in NO)
WAREHOUSES = [
    # Denmark (DK)
    {
        "code": "DK-DC-01",
        "name": "Taastrup Central Logistics Hub",
        "country": "DK",
        "type": "dc",
        "address": "Kuldyssen 14, 2630 Taastrup",
        "latitude": 55.6521,
        "longitude": 12.3012,
        "contact_email": "dc-taastrup@oneorder.dk",
    },
    {
        "code": "DK-BR-01",
        "name": "København Sydhavn Proff Branch",
        "country": "DK",
        "type": "branch",
        "address": "Bådehavnsgade 44, 2450 København SV",
        "latitude": 55.6514,
        "longitude": 12.5378,
        "contact_email": "cph-sydhavn@oneorder.dk",
    },
    {
        "code": "DK-BR-02",
        "name": "Aarhus Havn Byggecenter",
        "country": "DK",
        "type": "branch",
        "address": "Sverigesgade 12, 8000 Aarhus C",
        "latitude": 56.1524,
        "longitude": 10.2229,
        "contact_email": "aarhus-havn@oneorder.dk",
    },
    {
        "code": "DK-BR-03",
        "name": "Odense Erhvervsafdeling",
        "country": "DK",
        "type": "branch",
        "address": "Havnegade 98, 5000 Odense C",
        "latitude": 55.4038,
        "longitude": 10.3883,
        "contact_email": "odense-proff@oneorder.dk",
    },
    {
        "code": "DK-BR-04",
        "name": "Aalborg Syd Trælast",
        "country": "DK",
        "type": "branch",
        "address": "Hobrovej 340, 9200 Aalborg SV",
        "latitude": 57.0189,
        "longitude": 9.9197,
        "contact_email": "aalborg-syd@oneorder.dk",
    },

    # Sweden (SE)
    {
        "code": "SE-DC-01",
        "name": "Jönköping Nordic Central Distribution Center",
        "country": "SE",
        "type": "dc",
        "address": "Torsviks Industriområde 12, 556 52 Jönköping",
        "latitude": 57.7826,
        "longitude": 14.1618,
        "contact_email": "dc-jonkoping@oneorder.se",
    },
    {
        "code": "SE-BR-01",
        "name": "Stockholm Globen Proffscenter",
        "country": "SE",
        "type": "branch",
        "address": "Arenavägen 33, 121 77 Johanneshov, Stockholm",
        "latitude": 59.2936,
        "longitude": 18.0831,
        "contact_email": "sthlm-globen@oneorder.se",
    },
    {
        "code": "SE-BR-02",
        "name": "Göteborg Hisingen Byggvaruhus",
        "country": "SE",
        "type": "branch",
        "address": "Tagenevägen 21, 425 37 Hisings Kärra, Göteborg",
        "latitude": 57.7210,
        "longitude": 11.9447,
        "contact_email": "goteborg-hisingen@oneorder.se",
    },
    {
        "code": "SE-BR-03",
        "name": "Malmö Hamn Proffsfilial",
        "country": "SE",
        "type": "branch",
        "address": "Hans Michelsensgatan 10, 211 20 Malmö",
        "latitude": 55.6180,
        "longitude": 12.9981,
        "contact_email": "malmo-hamn@oneorder.se",
    },
    {
        "code": "SE-BR-04",
        "name": "Uppsala Fyrislund Byggdepå",
        "country": "SE",
        "type": "branch",
        "address": "Rapsgatan 8, 753 23 Uppsala",
        "latitude": 59.8732,
        "longitude": 17.6534,
        "contact_email": "uppsala-nord@oneorder.se",
    },

    # Norway (NO)
    {
        "code": "NO-DC-01",
        "name": "Vestby Central WMS Hub",
        "country": "NO",
        "type": "dc",
        "address": "Stormåsan 16, 1540 Vestby",
        "latitude": 59.6053,
        "longitude": 10.7481,
        "contact_email": "dc-vestby@oneorder.no",
    },
    {
        "code": "NO-BR-01",
        "name": "Oslo Alnabru Proffsenter",
        "country": "NO",
        "type": "branch",
        "address": "Strømsveien 314, 0666 Oslo",
        "latitude": 59.9315,
        "longitude": 10.8458,
        "contact_email": "oslo-alnabru@oneorder.no",
    },
    {
        "code": "NO-BR-02",
        "name": "Bergen Minde Byggevarehus",
        "country": "NO",
        "type": "branch",
        "address": "Kanalveien 64, 5068 Bergen",
        "latitude": 60.3642,
        "longitude": 5.3486,
        "contact_email": "bergen-minde@oneorder.no",
    },
    {
        "code": "NO-BR-03",
        "name": "Trondheim Sluppen Proffavdeling",
        "country": "NO",
        "type": "branch",
        "address": "Bratsbergvegen 22, 7037 Trondheim",
        "latitude": 63.4022,
        "longitude": 10.3951,
        "contact_email": "trondheim-sluppen@oneorder.no",
    },
    {
        "code": "NO-BR-04",
        "name": "Stavanger Forus Byggsenter",
        "country": "NO",
        "type": "branch",
        "address": "Lagerveien 15, 4033 Stavanger",
        "latitude": 58.8872,
        "longitude": 5.7275,
        "contact_email": "stavanger-forus@oneorder.no",
    },
]

# 3. CONSTRUCTION SITES DEFINITION (10 Realistic Nordic Project Sites)
SITES = [
    # Denmark
    {
        "id": "SITE-DK-01",
        "name": "Nordhavn Kronløbsøen Residential Tower",
        "country": "DK",
        "address": "Sundkaj 7, 2150 Nordhavn, København",
        "latitude": 55.7077,
        "longitude": 12.5985,
        "contact_person": "Lars Møller (NCC Denmark)",
        "phone": "+45 20 12 34 56",
        "crane_accessible": True,
    },
    {
        "id": "SITE-DK-02",
        "name": "Carlsberg Byen Karré 11 Boliger",
        "country": "DK",
        "address": "Pasteurs Vej 24, 1799 København V",
        "latitude": 55.6667,
        "longitude": 12.5333,
        "contact_person": "Henrik Nielsen (Per Aarsleff A/S)",
        "phone": "+45 21 98 76 54",
        "crane_accessible": True,
    },
    {
        "id": "SITE-DK-03",
        "name": "Aarhus Nyt Universitetshospital Udvidelse",
        "country": "DK",
        "address": "Palle Juul-Jensens Boulevard 99, 8200 Aarhus N",
        "latitude": 56.1915,
        "longitude": 10.1650,
        "contact_person": "Morten Jensen (MT Højgaard)",
        "phone": "+45 22 45 67 89",
        "crane_accessible": True,
    },
    {
        "id": "SITE-DK-04",
        "name": "Odense Havnebad & Erhvervskvarter",
        "country": "DK",
        "address": "Havnegade 45, 5000 Odense C",
        "latitude": 55.4120,
        "longitude": 10.3790,
        "contact_person": "Søren Poulsen (Jens Møller Byg)",
        "phone": "+45 23 11 22 33",
        "crane_accessible": False,
    },

    # Sweden
    {
        "id": "SITE-SE-01",
        "name": "Hagastaden Life Science Kvarter",
        "country": "SE",
        "address": "Solnavägen 12, 113 65 Stockholm",
        "latitude": 59.3467,
        "longitude": 18.0354,
        "contact_person": "Johan Lindqvist (Skanska Sverige)",
        "phone": "+46 8 504 350 00",
        "crane_accessible": True,
    },
    {
        "id": "SITE-SE-02",
        "name": "Karlatornet Lindholmen Skyscraper",
        "country": "SE",
        "address": "Lindholmsallén 34, 417 56 Göteborg",
        "latitude": 57.7103,
        "longitude": 11.9388,
        "contact_person": "Erik Bergström (Serneke Bygg)",
        "phone": "+46 31 712 97 00",
        "crane_accessible": True,
    },
    {
        "id": "SITE-SE-03",
        "name": "Malmö Live Nyhavn Kvarteret",
        "country": "SE",
        "address": "Gibraltargatan 2, 211 18 Malmö",
        "latitude": 55.6074,
        "longitude": 12.9934,
        "contact_person": "Sara Holm (Peab Malmö)",
        "phone": "+46 40 16 70 00",
        "crane_accessible": False,
    },

    # Norway
    {
        "id": "SITE-NO-01",
        "name": "Bjørvika Barcode Finanssenter",
        "country": "NO",
        "address": "Dronning Eufemias gate 16, 0191 Oslo",
        "latitude": 59.9075,
        "longitude": 10.7584,
        "contact_person": "Knut Haug (Veidekke Entreprenør)",
        "phone": "+47 21 05 50 00",
        "crane_accessible": True,
    },
    {
        "id": "SITE-NO-02",
        "name": "Bergen Bybane Fyllingsdalen Verksted",
        "country": "NO",
        "address": "Folke Bernadottes vei 50, 5147 Fyllingsdalen, Bergen",
        "latitude": 60.3700,
        "longitude": 5.3400,
        "contact_person": "Ole Bakke (AF Gruppen Vest)",
        "phone": "+47 55 59 70 00",
        "crane_accessible": True,
    },
    {
        "id": "SITE-NO-03",
        "name": "Trondheim Solsiden Brygge Boliger",
        "country": "NO",
        "address": "Beddingen 8, 7014 Trondheim",
        "latitude": 63.4350,
        "longitude": 10.4130,
        "contact_person": "Trond Solberg (Hent AS)",
        "phone": "+47 72 89 80 00",
        "crane_accessible": False,
    },
]

# RARE ITEMS MATRIX (Cross-border demo)
# Keys: SKU -> Dict with Country Availability:
#   'SE': Only in Sweden
#   'NO': Only in Norway
#   'DK': Only in Denmark
COUNTRIES = ["DK", "SE", "NO"]

RARE_CROSS_BORDER_MAP = {
    # Exclusive to Sweden
    "TIM-SE-PINE45": "SE",
    "STO-SE-GRANITE": "SE",
    "ARM-BEAM-HEA200": "SE",
    # Exclusive to Norway
    "ROOF-NO-SLATE": "NO",
    "CHM-NO-ARCTIC": "NO",
    "INS-NO-ECOWOOL": "NO",
    # Exclusive to Denmark
    "BRK-DK-CPHRED": "DK",
    "WIN-DK-VELUX78": "DK",
}


def _alias_tokens(text):
    text = text.lower().translate(str.maketrans({"æ": "ae", "ø": "oe", "å": "aa", "ä": "ae", "ö": "oe"}))
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    text = re.sub(r"(\d+)(mm|cm|m|kg|pk|stk)", r"\1 \2", text)
    text = re.sub(r"(\d+)x(\d+)", r"\1 \2", text)
    return set(re.sub(r"[^\w\s]", " ", text).split())


def drop_ambiguous_aliases(items):
    """Remove aliases that are too generic: all their tokens also appear in another SKU's name or alias.

    Such an alias would exact-match one SKU and be auto-selected although sibling SKUs
    (other lengths, grades, variants) fit it just as well.
    """
    token_sets = [(it["sku"], _alias_tokens(t)) for it in items for t in [it["name"], *it.get("aliases", [])]]
    for it in items:
        it["aliases"] = [
            a for a in it.get("aliases", [])
            if not any(sku != it["sku"] and _alias_tokens(a) <= tokens for sku, tokens in token_sets)
        ]
    return items


def build_catalog():
    items = []
    # Deduplicate by SKU while preserving order
    seen_skus = set()
    for item in BASE_SAMPLE_ITEMS + ADDITIONAL_ITEMS + generate_systematic_variants():
        sku = item["sku"]
        if sku not in seen_skus:
            seen_skus.add(sku)
            items.append(item)
    return drop_ambiguous_aliases(items)


def generate_inventory_for_country(catalog, country_code, warehouses):
    """Generate realistic inventory records for a specific country's warehouses.
    
    Rules:
      - If SKU is in RARE_CROSS_BORDER_MAP and origin != country_code -> stock is strictly 0.
      - If SKU is rare to this country: Central DC has abundant stock, 1-2 key branches have moderate stock.
      - Normal items:
          - Central DC has high stock (e.g. 500 - 3500)
          - Regional branches carry ~55% of items with moderate local stock (e.g. 20 - 450)
          - ~12% of items are DC-only; ~7% are nearly out of stock in one country
      - Reserved quantity is realistic (e.g. 5% - 15% of on-hand).
    """
    country_whs = [w for w in warehouses if w["country"] == country_code]
    dc = [w for w in country_whs if w["type"] == "dc"][0]
    branches = [w for w in country_whs if w["type"] == "branch"]

    records = []

    for idx, item in enumerate(catalog):
        sku = item["sku"]
        unit = item["unit"]
        rare_origin = RARE_CROSS_BORDER_MAP.get(sku)

        # Check if item is forbidden/unavailable in this country
        if rare_origin is not None and rare_origin != country_code:
            # 0 stock across all warehouses in this country
            for wh in country_whs:
                records.append({
                    "sku": sku,
                    "warehouse_code": wh["code"],
                    "on_hand": 0,
                    "reserved": 0,
                    "unit": unit,
                })
            continue

        # If it's a rare item native to this country
        if rare_origin == country_code:
            # Plentiful at DC, limited at first branch, 0 at others
            records.append({
                "sku": sku,
                "warehouse_code": dc["code"],
                "on_hand": 850 if unit != "m" else 3500,
                "reserved": 45,
                "unit": unit,
            })
            for b_idx, br in enumerate(branches):
                on_hand = 120 if b_idx == 0 else 0
                res = 10 if on_hand > 0 else 0
                records.append({
                    "sku": sku,
                    "warehouse_code": br["code"],
                    "on_hand": on_hand,
                    "reserved": res,
                    "unit": unit,
                })
            continue

        # Deterministic pseudo-random generation based on SKU hash
        h = int(hashlib.md5(f"{sku}_{country_code}".encode()).hexdigest(), 16)
        sku_hash = int(hashlib.md5(f"{sku}_range".encode()).hexdigest(), 16)
        # ~12% of items are kept at the Central DC only (branches hold nothing)
        dc_only = sku_hash % 8 == 0
        # ~7% of items are nearly out of stock in one country, so another country must supply them
        short_country = COUNTRIES[(sku_hash // 14) % len(COUNTRIES)] if sku_hash % 14 == 1 else None

        if short_country == country_code:
            on_hand = h % 25
            records.append({
                "sku": sku,
                "warehouse_code": dc["code"],
                "on_hand": on_hand,
                "reserved": min(on_hand, 2),
                "unit": unit,
            })
            for br in branches:
                records.append({"sku": sku, "warehouse_code": br["code"], "on_hand": 0, "reserved": 0, "unit": unit})
            continue
        
        # DC Stock
        base_dc = 400 + (h % 2600)
        if unit == "m":
            base_dc *= 3
        elif unit == "pk" or unit == "stk" and item.get("category") == "fasteners":
            base_dc = 300 + (h % 1500)
        elif item.get("requires_crane"):
            base_dc = 50 + (h % 250)

        dc_reserved = int(base_dc * (0.05 + (h % 10) / 100.0))
        records.append({
            "sku": sku,
            "warehouse_code": dc["code"],
            "on_hand": base_dc,
            "reserved": dc_reserved,
            "unit": unit,
        })

        # Branch Stocks
        for b_idx, br in enumerate(branches):
            b_hash = int(hashlib.md5(f"{sku}_{br['code']}".encode()).hexdigest(), 16)
            is_stocked = not dc_only and (b_hash % 100) >= 45  # ~55% chance a branch carries the item
            if is_stocked:
                base_br = 20 + (b_hash % 180)
                if unit == "m":
                    base_br = 150 + (b_hash % 600)
                elif item.get("requires_crane"):
                    base_br = 5 + (b_hash % 25)
                br_reserved = int(base_br * (0.04 + (b_hash % 8) / 100.0))
            else:
                base_br = 0
                br_reserved = 0

            records.append({
                "sku": sku,
                "warehouse_code": br["code"],
                "on_hand": base_br,
                "reserved": br_reserved,
                "unit": unit,
            })

    return records


def write_catalog(catalog, path: Path):
    path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {len(catalog)} items to {path}")


def write_warehouses(warehouses, path: Path):
    path.write_text(json.dumps(warehouses, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {len(warehouses)} warehouses to {path}")


def write_sites(sites, path: Path):
    path.write_text(json.dumps(sites, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {len(sites)} sites to {path}")


def write_inventory_dk_csv(records, path: Path):
    """Format: CSV, Danish field headers: varenr, lager_kode, beholdning, reserveret, enhed"""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["varenr", "lager_kode", "beholdning", "reserveret", "enhed"])
        for r in records:
            writer.writerow([r["sku"], r["warehouse_code"], r["on_hand"], r["reserved"], r["unit"]])
    print(f"[OK] Wrote {len(records)} DK stock rows (CSV) to {path}")


def write_inventory_se_json(records, path: Path):
    """Format: JSON, Swedish field names: artikelnr, lagerplats, saldo, reserverat, enhet"""
    se_data = []
    for r in records:
        se_data.append({
            "artikelnr": r["sku"],
            "lagerplats": r["warehouse_code"],
            "saldo": r["on_hand"],
            "reserverat": r["reserved"],
            "enhet": r["unit"],
        })
    path.write_text(json.dumps(se_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {len(records)} SE stock entries (Swedish JSON) to {path}")


def write_inventory_no_json(records, path: Path):
    """Format: JSON, English standard field names: sku, warehouse_id, quantity_on_hand, reserved_quantity, unit"""
    no_data = []
    for r in records:
        no_data.append({
            "sku": r["sku"],
            "warehouse_id": r["warehouse_code"],
            "quantity_on_hand": r["on_hand"],
            "reserved_quantity": r["reserved"],
            "unit": r["unit"],
        })
    path.write_text(json.dumps(no_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {len(records)} NO stock entries (English JSON) to {path}")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    catalog = build_catalog()
    write_catalog(catalog, DATA_DIR / "catalog.json")

    write_warehouses(WAREHOUSES, DATA_DIR / "warehouses.json")
    write_sites(SITES, DATA_DIR / "sites.json")

    # Generate inventories
    dk_records = generate_inventory_for_country(catalog, "DK", WAREHOUSES)
    se_records = generate_inventory_for_country(catalog, "SE", WAREHOUSES)
    no_records = generate_inventory_for_country(catalog, "NO", WAREHOUSES)

    write_inventory_dk_csv(dk_records, DATA_DIR / "inventory_dk.csv")
    write_inventory_se_json(se_records, DATA_DIR / "inventory_se.json")
    write_inventory_no_json(no_records, DATA_DIR / "inventory_no.json")

    print("\n--- Summary ---")
    print(f"Catalog items count: {len(catalog)}")
    print(f"Warehouses count:    {len(WAREHOUSES)}")
    print(f"Sites count:         {len(SITES)}")
    print(f"DK ERP records:      {len(dk_records)} in CSV")
    print(f"SE ERP records:      {len(se_records)} in JSON")
    print(f"NO ERP records:      {len(no_records)} in JSON")
    print(f"Cross-border items:  {len(RARE_CROSS_BORDER_MAP)} specialized items configured")


if __name__ == "__main__":
    main()

