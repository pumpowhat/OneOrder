# OneOrder — Frontend Shell

OneOrder is a Nordic B2B building materials order orchestration dashboard designed to streamline contractor request intake, human-in-the-loop review, multi-warehouse fulfillment routing across Denmark, Sweden, and Norway, and delivery time prediction.

---

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

- **Port:** `5173` (`strictPort: true` enforced)
- **Vite Proxy:** All relative requests to `/api` and `/mock-erp` automatically proxy to the FastAPI backend running at `http://127.0.0.1:8000`.

---

## Six Core Screens

| Route | Screen Name | Description |
|---|---|---|
| `/inbox` | **Contractor Intake** | Incoming customer material orders from OCR photo notes, emails, and Excel BOQ sheets with raw previews and extraction stats. |
| `/review` | **Order Review & Verification** | Human-in-the-loop review enforcing the 85% confidence threshold. Flagged lines require manual confirmation before approval. Features an immutable audit trail. |
| `/plan` | **Fulfillment Planning** | Multi-warehouse routing (Nearest Branch → Domestic DC → Cross-Border DC), vehicle & crane truck assignment, and P50/P90 ML delivery windows. |
| `/stock` | **Group Inventory** | Consolidated inventory across DK, SE, and NO with low-stock alerts and a live Native ERP Adapter Inspector (Danish CSV, Swedish JSON, English JSON). |
| `/rules` | **Business Rules** | Interactive dispatcher rules configuration (`rules.json`) covering intake confidence, sourcing priority order, vehicle weight caps, and winter buffers. |
| `/model` | **ML Delivery Time Model** | LightGBM quantile regression performance metrics, SHAP feature importance weights, and an interactive What-If ETA Simulator. |

---

## API Integration Guide (For Teammates)

When wiring real backend endpoints:

1. **API Types & Data Contracts:**
   - Central contract declarations reside in `src/types/api.ts`.
   - Confirmed backend types match `backend/db.py` (`Order`, `OrderLine`, `AuditLogEntry`, etc.).
   - Provisional contracts are clearly marked with `// PROVISIONAL:`.
   - Assumptions are documented with `// ASSUMPTION:`.

2. **Connecting Endpoints:**
   - Replace mock imports from `src/mocks/*.ts` with API calls via `src/api/client.ts`.
   - Use relative URLs (e.g. `/api/orders/{id}`) so Vite proxies to `127.0.0.1:8000`.
   - When a screen is fully connected to FastAPI, simply remove the `<MockDataBanner />` component from that page.

3. **Bilingual Support (i18n):**
   - All user-facing strings are keyed through `useI18n()`.
   - English dictionary: `src/i18n/en.ts`.
   - Vietnamese dictionary: `src/i18n/vi.ts` (enforced with strict TypeScript type parity).

---

## Tech Stack

- **React 19** + **TypeScript** (Strict Mode)
- **Vite 8**
- **Tailwind CSS v4** (Zero config files, fully tokenized in `src/index.css` via `@theme inline`)
- **React Router 7** (Declarative `BrowserRouter`)
- **Lucide React** (Consistent icon library)
- **Inter Variable Font** (Self-hosted via `@fontsource-variable/inter`)
