/** API types for OneOrder. They mirror the backend responses (see backend/routers and services). */

export type AiMode = "live" | "demo";
export type NordicCountry = "DK" | "SE" | "NO";

export interface HealthResponse {
  status: string;
  ai_mode: AiMode;
}

// --- orders -------------------------------------------------------------------------------------

export type OrderStatus = "draft" | "approved" | "planned" | "confirmed" | "cancelled";
export type SourceType = "manual" | "image" | "pdf" | "excel" | "email";
export type EtaRisk = "on_time" | "at_risk" | "late";
export type CrmProvider = "salesforce" | "none";
export type CrmSyncStatus = "synced" | "pending" | "failed" | "not_applicable";

export interface CrmSync {
  status: CrmSyncStatus;
  reason: "crm_disabled" | "no_account" | null;
  attempts: number;
  crm_record_id: string | null;
  last_error: string | null;
  last_attempt_at: string | null;
}

export interface CrmCustomerLink {
  crm_account_id: string | null;
  crm_contact_id: string | null;
}

export interface CustomerCandidate extends CrmCustomerLink {
  crm_account_id: string;
  name: string;
  phone: string | null;
  city: string | null;
  score: number;
  country: NordicCountry;
  matched_on: "phone" | "name";
}

export interface CustomerCandidatesResponse {
  crm: CrmProvider;
  countries: NordicCountry[];
  candidates: CustomerCandidate[];
}

export interface CustomerLookup {
  name: string;
  phone: string;
}

/** One row of GET /api/orders. */
export interface OrderSummary {
  id: string;
  status: OrderStatus;
  created_at: string | null;
  source_type: SourceType;
  source_name: string | null;
  customer: string | null;
  customer_phone: string | null;
  delivery_site: string | null;
  requested_date: string | null;
  crm_sync_status?: CrmSyncStatus | null;
  line_count: number;
  review_lines: number;
  shortage_count: number;
  shipment_count: number;
  p50_date: string | null;
  p90_date: string | null;
  risk: EtaRisk | null;
}

export interface OrderCandidate {
  sku: string;
  name: string;
  score: number;
  unit?: string | null;
}

export interface OrderLine {
  line_index: number;
  description: string;
  quantity: number;
  unit: string | null;
  confidence: number;
  source_text: string | null;
  matched_sku: string | null;
  match_score: number | null;
  candidates: OrderCandidate[];
  confirmed: boolean;
  ambiguous: boolean;
  needs_review: boolean;
}

export interface AuditLogEntry {
  id: number;
  timestamp: string | null;
  action: string;
  user: string;
  payload_before: unknown;
  payload_after: unknown;
}

export interface Reservation {
  warehouse_code: string;
  sku: string;
  quantity: number;
  unit: string | null;
  shipment_index: number | null;
  created_at: string | null;
}

/** GET /api/orders/{id}. */
export interface Order {
  id: string;
  status: OrderStatus;
  source_type: SourceType;
  source_name: string | null;
  customer: string | null;
  customer_phone: string | null;
  delivery_site: string | null;
  requested_date: string | null;
  lines: OrderLine[];
  warnings: string[];
  needs_review: boolean;
  plan: FulfillmentPlan | null;
  has_source: boolean;
  created_at: string | null;
  crm_account_id?: string | null;
  crm_contact_id?: string | null;
  crm_sync?: CrmSync | null;
  reservations: Reservation[];
  audit_logs: AuditLogEntry[];
}

export type OrderSource =
  | { kind: "image"; name: string | null; mime: string | null }
  | { kind: "pdf"; name: string | null; mime: string | null }
  | { kind: "text"; name: string | null; mime: string | null; text: string }
  | { kind: "table"; name: string | null; mime: string | null; rows: string[][]; truncated: boolean };

export type AvailabilityStatus = "ok" | "partial" | "none" | "unmatched";

export interface LineAvailability {
  line_index: number;
  sku: string | null;
  requested: number;
  available: number;
  by_country: Partial<Record<NordicCountry, number>>;
  status: AvailabilityStatus;
}

export interface LineCorrection {
  line_index: number;
  sku?: string;
  quantity?: number;
  confirmed?: boolean;
}

// --- plan ---------------------------------------------------------------------------------------

export interface ShipmentEta {
  dispatch_date: string;
  baseline_date: string;
  p50_date: string;
  p90_date: string;
  delay_p50_days: number;
  delay_p90_days: number;
  risk: EtaRisk | null;
  notes: string[];
}

export interface OrderEta {
  p50_date: string;
  p90_date: string;
  risk: EtaRisk | null;
}

export interface Allocation {
  line_index: number;
  sku: string;
  description: string | null;
  quantity: number;
  unit: string | null;
  weight_kg: number;
  reason: string;
}

export type VehicleType = "small_truck" | "heavy_truck" | "crane_truck";

export interface Shipment {
  shipment_index: number;
  origin_warehouse: string;
  origin_name: string;
  origin_country: NordicCountry;
  origin_type: "branch" | "dc";
  destination_country: NordicCountry;
  cross_border: boolean;
  distance_km: number;
  total_weight_kg: number;
  crane_required: boolean;
  vehicle_type: VehicleType;
  vehicle_count: number;
  lines: Allocation[];
  eta: ShipmentEta | null;
}

export interface Shortage {
  line_index: number;
  sku: string;
  description: string | null;
  requested: number;
  allocated: number;
  missing: number;
  reason: string;
}

export interface FulfillmentPlan {
  order_id: string | null;
  customer: string | null;
  requested_date: string | null;
  site: { id: string; name: string; country: NordicCountry; match: "site_id" | "address" | "city" };
  shipments: Shipment[];
  shortages: Shortage[];
  total_weight_kg: number;
  fully_sourced: boolean;
  warnings: string[];
  order_eta: OrderEta | null;
}

export interface Site {
  id: string;
  name: string;
  country: NordicCountry;
  address: string;
  crane_accessible: boolean;
}

// --- stock --------------------------------------------------------------------------------------

export type StockLevel = "ok" | "low" | "out";

export interface StockCell {
  on_hand: number;
  reserved: number;
  available: number;
}

export interface StockWarehouse extends StockCell {
  code: string;
  name: string;
  type: "branch" | "dc" | null;
  country: NordicCountry;
}

export interface StockItem {
  sku: string;
  name: string;
  unit: string;
  by_country: Record<NordicCountry, StockCell>;
  warehouses: StockWarehouse[];
  total_available: number;
  level: StockLevel;
  single_country: boolean;
}

export interface StockResponse {
  summary: Record<NordicCountry, { skus: number; out_or_low: number }>;
  items: StockItem[];
  total: number;
}

// --- model --------------------------------------------------------------------------------------

export interface ModelInfo {
  features: string[];
  feature_importance: Record<string, number>;
  metrics: { p90_coverage: number; mae_p50_days: number; holdout_rows: number };
  training_rows: number;
  data_source: string;
  disclaimer: string;
}

// --- sample inbox -------------------------------------------------------------------------------

export interface InboxItem {
  id: string;
  kind: SourceType;
  filename: string;
  size_bytes: number;
  preview: string | null;
}

// --- rules --------------------------------------------------------------------------------------

export type SourcingTier = "branch" | "domestic_dc" | "cross_border_dc";

export interface VehicleRule {
  type: VehicleType;
  max_weight_kg: number;
  crane: boolean;
}

/** GET/PUT /api/rules. `intake` and `country_lead_time_buffer_days` are kept as received. */
export interface Rules {
  version: number;
  crm?: Record<NordicCountry, CrmProvider>;
  intake: { min_confidence: number };
  sourcing: {
    priority: SourcingTier[];
    allow_cross_border: boolean;
    allow_line_split: boolean;
    branch_max_distance_km: number;
    max_shipments_per_order: number;
  };
  distance: { road_factor: number };
  vehicles: VehicleRule[];
  country_lead_time_buffer_days: Record<string, number>;
}


export interface CatalogProduct { sku: string; name: string; unit: string | null }
export interface DraftOrderInput {
  customer: string | null;
  customer_phone: string | null;
  delivery_site: string | null;
  requested_date: string | null;
  lines: { line_index?: number; sku: string | null; description: string; quantity: number; confirmed: boolean }[];
}

export type DraftOrderPatch = Partial<DraftOrderInput & CrmCustomerLink>;
