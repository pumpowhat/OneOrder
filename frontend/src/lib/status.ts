import type { BadgeTone } from "../components/ui/Badge.tsx";
import type { TranslationKey } from "../i18n/en.ts";
import type { EtaRisk, OrderStatus, VehicleType } from "../types/api.ts";

export const STATUS_TONE: Record<OrderStatus, BadgeTone> = {
  draft: "warn",
  approved: "neutral",
  planned: "info",
  confirmed: "success",
  cancelled: "neutral",
};

export const STATUS_LABEL: Record<OrderStatus, TranslationKey> = {
  draft: "status.draft",
  approved: "status.approved",
  planned: "status.planned",
  confirmed: "status.confirmed",
  cancelled: "status.cancelled",
};

export const RISK_TONE: Record<EtaRisk, BadgeTone> = {
  on_time: "success",
  at_risk: "warn",
  late: "danger",
};

export const RISK_LABEL: Record<EtaRisk, TranslationKey> = {
  on_time: "risk.on_time",
  at_risk: "risk.at_risk",
  late: "risk.late",
};

export const VEHICLE_LABEL: Record<VehicleType, TranslationKey> = {
  small_truck: "vehicle.small_truck",
  heavy_truck: "vehicle.heavy_truck",
  crane_truck: "vehicle.crane_truck",
};
