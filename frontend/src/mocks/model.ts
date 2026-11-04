export interface ModelFeature {
  name: string;
  key: string;
  importance: number; // 0 to 1
  description: string;
}

export interface ModelMetadata {
  modelName: string;
  framework: string;
  trainingSamples: number;
  lastTrained: string;
  p50MaeDays: number;
  p90EmpiricalCoverage: number;
  pinballLossP50: number;
  pinballLossP90: number;
  onTimeCommitmentImprovement: string;
  features: ModelFeature[];
  calibrationNote: string;
}

export const MOCK_MODEL_DATA: ModelMetadata = {
  modelName: "GradientBoostingRegressor (Quantile Loss α=0.50, α=0.90)",
  framework: "scikit-learn 1.5.1",
  trainingSamples: 12500,
  lastTrained: "2026-11-02",
  p50MaeDays: 0.38,
  p90EmpiricalCoverage: 0.914,
  pinballLossP50: 0.19,
  pinballLossP90: 0.11,
  onTimeCommitmentImprovement: "+15.2 pp",
  features: [
    {
      key: "distance_km",
      name: "Road Distance (km)",
      importance: 0.29,
      description: "Direct highway distance from originating branch/DC to construction site",
    },
    {
      key: "cross_border",
      name: "Cross-Border Transit",
      importance: 0.21,
      description: "Transit crossing Øresund Bridge (DK-SE) or Svinesund (SE-NO) customs corridor",
    },
    {
      key: "source_type",
      name: "Source Facility Hierarchy",
      importance: 0.16,
      description: "Direct local branch pickup vs domestic central DC vs foreign cross-border DC",
    },
    {
      key: "winter_season",
      name: "Nordic Winter Season",
      importance: 0.11,
      description: "Winter weather factor (Nov–Mar) introducing snow, ice, and ferry delays",
    },
    {
      key: "crane_required",
      name: "Truck-Mounted Crane",
      importance: 0.09,
      description: "Specialized Hiab crane truck scheduling and site unloading overhead",
    },
    {
      key: "total_weight_kg",
      name: "Total Weight (kg)",
      importance: 0.06,
      description: "Gross payload weight affecting vehicle dispatch type and loading duration",
    },
    {
      key: "line_count",
      name: "Picking Complexity",
      importance: 0.05,
      description: "Number of discrete SKU lines requiring multi-zone warehouse picking",
    },
    {
      key: "day_of_week",
      name: "Day of Week & Cutoff",
      importance: 0.03,
      description: "Dispatch weekday timing, Friday weekend cutoffs, and driver rest regulation",
    },
  ],
  calibrationNote:
    "Trained on 12,500 simulated Scandinavian shipments calibrated against Nordic public transport and freight benchmarks (Vejdirektoratet DK, Trafikverket SE, Statens vegvesen NO). Quantile regression produces asymmetric loss penalizing late deliveries 9x more heavily than early arrivals.",
};
