import type { InboxItem } from "../types/api";

export const MOCK_INBOX_ITEMS: InboxItem[] = [
  {
    id: "INB-1041",
    orderId: "ord-dk-1041",
    receivedAt: "2026-11-03T08:24:00Z",
    sourceType: "image",
    sourceName: "handwritten_site_note_aarhus.jpg",
    customer: "NCC Danmark A/S",
    deliverySite: "Aarhus Havn Kontorhus, Dokk 1, 8000 Aarhus",
    country: "DK",
    requestedDate: "2026-11-06",
    lineCount: 7,
    flaggedCount: 2,
    status: "draft",
    rawPreviewTitle: "OCR Transcript: Site Foreman Pad (Site 4B)",
    rawPreviewBody: `[BILLED-SCAN: handwritten_site_note_aarhus.jpg]
Formand: Mads Poulsen // Mobil: +45 28 44 91 02
Byggeplads: Aarhus Havn Etape 2 (Dokk 1 vest)

Materialer haster til torsdag 06-11:
1. 140 stk Fermacell fibergips 12.5 x 900 x 2400
2. 80 pk Rockwool Flexibatts 37 95mm (OBS: tjek om lager i Roskilde el Odense)
3. 24 stk HEB 160 stålbjælker L=6m skåret [ULÆSELIG BLÆK-PLET: ~24 el 28?]
4. 450 lbm Knauf reglar stål 70mm
5. 12 rlr Dampspærre 0.20mm folie 2x50m
6. 35 ps Aalborg Portland Basis Cement 25kg
7. ~15 pk Skruer til fibergips 3.9x30 [SKREVET I KANTEN: husk levering m kranbil!]`,
  },
  {
    id: "INB-1042",
    orderId: "ord-se-1042",
    receivedAt: "2026-11-03T09:12:00Z",
    sourceType: "email",
    sourceName: "bestallning_slussen_etapp4.eml",
    customer: "Skanska Sverige AB",
    deliverySite: "Slussen Projektkontor, Södermalmstorg 8, 118 20 Stockholm",
    country: "SE",
    requestedDate: "2026-11-05",
    lineCount: 5,
    flaggedCount: 1,
    status: "draft",
    rawPreviewTitle: "Email: bestallning_slussen_etapp4.eml",
    rawPreviewBody: `Från: johan.lindqvist@skanska.se
Till: order@oneorder-nordic.com
Ämne: Avrop Slussen Etapp 4 - Stål och isolering v45

Hej teamet,

Här kommer avrop för Slussen brofäste etapp 4 med leverans senast torsdag 5 nov kl 07:00:

- Gyproc Normalgips GN 13 1200x2400 mm: 220 skivor
- Isover Piano Ljudisolering 45 mm: 45 balar
- HEA 200 stålbalk S355J2, Längd 12.0m: 16 st (kräver tung kranbil på kajen!)
- Bultset M24 varmförzinkad 8.8: 80 st
- Tätningslist T-Flex 50mm: 14 rullar

Vänligen bekräfta om stålbalkarna kan sampackas från Jönköping eller om de tas från Roskilde.

Med vänlig hälsning,
Johan Lindqvist | Inköpsledare Stora Projekt | Skanska Sverige AB`,
  },
  {
    id: "INB-1043",
    orderId: "ord-no-1043",
    receivedAt: "2026-11-03T07:45:00Z",
    sourceType: "excel",
    sourceName: "Veidekke_BOQ_Fornebu_Nov2026.xlsx",
    customer: "Veidekke Entreprenør AS",
    deliverySite: "Fornebubanen Stasjon Flytårnet, 1360 Fornebu",
    country: "NO",
    requestedDate: "2026-11-07",
    lineCount: 6,
    flaggedCount: 0,
    status: "approved",
    rawPreviewTitle: "Parsed Sheet: Sheet1 (BOQ_Import)",
    rawPreviewBody: `| Kundenr | Prosjekt-ID | Varebeskrivelse                     | Antall | Enhet | Merknad          |
|---------|-------------|-------------------------------------|--------|-------|------------------|
| NO-8821 | FBN-2026-03 | Glava Proff 34 Plate 100mm         | 110    | PK    | Levering port B  |
| NO-8821 | FBN-2026-03 | Norgips Standard A 13 1200x2400     | 300    | STK   | Palletert        |
| NO-8821 | FBN-2026-03 | Armeringsnett K131 5000x2150 mm    | 40     | STK   | Utvendig lagring |
| NO-8821 | FBN-2026-03 | Norcem Standard Sement FA 25kg     | 60     | SK    | Tørt lager       |
| NO-8821 | FBN-2026-03 | Stender Stål C60/40 3000mm         | 350    | LBM   |                  |
| NO-8821 | FBN-2026-03 | Isola Svillemembran 100mm x 15m     | 18     | RLL   |                  |`,
  },
  {
    id: "INB-1044",
    orderId: "ord-dk-1044",
    receivedAt: "2026-11-02T16:30:00Z",
    sourceType: "email",
    sourceName: "ordre_ouh_fase2.eml",
    customer: "MT Højgaard Danmark",
    deliverySite: "Nyt OUH Byggepladsvej 12, 5220 Odense SØ",
    country: "DK",
    requestedDate: "2026-11-06",
    lineCount: 8,
    flaggedCount: 0,
    status: "planned",
    rawPreviewTitle: "Email: ordre_ouh_fase2.eml",
    rawPreviewBody: `Fra: k.jensen@mth.dk
Til: ordre@oneorder-nordic.com
Emne: Levering af gipsvægge og profiler til OUH Etape 2

Hej OneOrder,
Vi har godkendt udtrækket til Ny Odense Universitetshospital. 
Venligst bekræft levering fredag morgen kl. 06:30.
8 linjer i alt jf. vedhæftede specifikation.`,
  },
  {
    id: "INB-1045",
    orderId: "ord-se-1045",
    receivedAt: "2026-11-02T14:15:00Z",
    sourceType: "image",
    sourceName: "peab_falken_list.png",
    customer: "Peab Sverige AB",
    deliverySite: "Karlatornet Kvarter Falken, 417 56 Göteborg",
    country: "SE",
    requestedDate: "2026-11-04",
    lineCount: 4,
    flaggedCount: 0,
    status: "confirmed",
    rawPreviewTitle: "OCR: peab_falken_list.png",
    rawPreviewBody: `PEAB PRODUKTION GÖTEBORG - KVARTER FALKEN
Byggledare: Sara Bergström
1. 85 st Plywood WBP 15x1200x2500
2. 40 rlr T-Emball T-Vind Super
3. 250 lpm Träregel 45x145 C24 gran
4. 12 pkt Träskruv CorrSeal 4.8x75`,
  },
];
