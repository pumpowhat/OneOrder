/**
 * API types for OneOrder.
 * Matches backend/main.py and backend/db.py for confirmed endpoints.
 * Provisional types are marked with comments.
 */

// Confirmed: GET /api/health
export type AiMode = "live" | "demo";

export interface HealthResponse {
  status: string;
  ai_mode: AiMode;
}

// ASSUMPTION: Candidate shape parsed from JSON in backend/db.py candidates column
export interface OrderCandidate {
  sku: string;
  description: string;
  score: number;
}

// Confirmed: OrderLine schema serialized from backend/db.py OrderLineModel
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

// Confirmed: AuditLog schema from backend/db.py AuditLogModel
export interface AuditLogEntry {
  id: number;
  timestamp: string | null;
  action: "create_draft" | "edit_line" | "approve" | string;
  user: string;
  payload_before: unknown;
  payload_after: unknown;
}

// Order lifecycle, same as backend/services/orders/status.py:
// draft -> approved -> planned -> confirmed, and cancelled (final) from draft/approved/planned.
export type OrderStatus = "draft" | "approved" | "planned" | "confirmed" | "cancelled";

// ASSUMPTION: Intake sources supported by intake services
export type SourceType = "image" | "email" | "excel";

// Confirmed: Order schema serialized from backend/db.py OrderModel
export interface Order {
  id: string;
  status: OrderStatus;
  source_type: SourceType;
  source_name: string | null;
  customer: string | null;
  delivery_site: string | null;
  requested_date: string | null;
  lines: OrderLine[];
  warnings: string[];
  needs_review: boolean;
  audit_logs: AuditLogEntry[];
}

// ---------------------------------------------------------------------------
// PROVISIONAL: The types below support frontend shell screens before
// backend endpoints for intake, fulfillment planning, stock, rules, and model
// metrics are wired.
// ---------------------------------------------------------------------------

export type NordicCountry = "DK" | "SE" | "NO";

// PROVISIONAL: Inbox item for /inbox contractor intake queue
export interface InboxItem {
  id: string;
  orderId: string;
  receivedAt: string;
  sourceType: SourceType;
  sourceName: string;
  customer: string;
  deliverySite: string;
  country: NordicCountry;
  requestedDate: string | null;
  lineCount: number;
  flaggedCount: number;
  status: OrderStatus;
  rawPreviewTitle: string;
  rawPreviewBody: string;
}

export type VehicleType = "small_truck" | "heavy_truck" | "crane_truck";

export type WarehouseSourceType = "branch" | "domestic_dc" | "cross_border_dc";

// PROVISIONAL: Material line allocated to a specific shipment
export interface ShipmentLineItem {
  sku: string;
  description: string;
  quantity: number;
  unit: string;
  weight_kg: number;
}

// PROVISIONAL: Individual shipment plan for /plan
export interface ShipmentPlan {
  id: string;
  shipment_index: number;
  origin_warehouse: string;
  origin_country: NordicCountry;
  destination_site: string;
  destination_country: NordicCountry;
  vehicle_type: VehicleType;
  crane_required: boolean;
  cross_border: boolean;
  distance_km: number;
  total_weight_kg: number;
  p50_date: string;
  p90_date: string;
  on_time: boolean;
  selection_reason: string;
  erp_reservation_id?: string;
  lines: ShipmentLineItem[];
}

// PROVISIONAL: Order-level fulfillment plan
export interface FulfillmentPlan {
  order_id: string;
  customer: string;
  delivery_site: string;
  requested_date: string;
  shipments: ShipmentPlan[];
  total_weight_kg: number;
  max_p90_date: string;
  on_time: boolean;
}

// PROVISIONAL: Multi-warehouse stock level row for /stock
export interface WarehouseStockRow {
  sku: string;
  description: string;
  category: string;
  unit: string;
  dk_stock: number;
  se_stock: number;
  no_stock: number;
  total_stock: number;
  reorder_level: number;
  lead_time_days: number;
}

// PROVISIONAL: Native ERP raw JSON inspector sample
export interface NativeErpSample {
  erp_system: string;
  warehouse_code: string;
  country: NordicCountry;
  sample_json: string;
}

// PROVISIONAL: Configurable business rules for /rules
export interface BusinessRules {
  confidence_threshold: number;
  sourcing_priority: string[];
  allow_cross_border: boolean;
  max_shipments_per_order: number;
  vehicle_weight_limits: Record<VehicleType, number>;
  country_lead_time_buffer_days: Record<NordicCountry, number>;
}

// PROVISIONAL: ML ETA model metrics for /model
export interface ModelMetrics {
  model_name: string;
  algorithm: string;
  train_samples: number;
  mae_days: number;
  rmse_days: number;
  r2_score: number;
  p50_coverage: number;
  p90_coverage: number;
  last_retrained_iso: string;
}

// PROVISIONAL: Feature importance entry for /model
export interface FeatureImportanceItem {
  feature: string;
  importance: number;
  description: string;
}

// PROVISIONAL: Prediction calibration bin
export interface CalibrationNote {
  bin: string;
  predicted_days: number;
  actual_days: number;
  sample_count: number;
}
