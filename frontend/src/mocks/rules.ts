export interface RulesConfig {
  intake: {
    minConfidenceThreshold: number;
    requireHumanConfirmOnAmbiguous: boolean;
    fuzzyMatchMinScore: number;
  };
  sourcing: {
    priorityOrder: string[];
    allowCrossBorderFallback: boolean;
    maxShipmentsPerOrder: number;
    consolidateBranchWithinKm: number;
  };
  vehicles: {
    smallTruckMaxKg: number;
    heavyTruckMaxKg: number;
    craneTruckMaxKg: number;
    autoAssignCraneForFlaggedSku: boolean;
  };
  marketBuffers: {
    DK: { dcLeadDays: number; crossBorderExtraDays: number; winterPenaltyDays: number };
    SE: { dcLeadDays: number; crossBorderExtraDays: number; winterPenaltyDays: number };
    NO: { dcLeadDays: number; crossBorderExtraDays: number; winterPenaltyDays: number };
  };
}

export const DEFAULT_RULES: RulesConfig = {
  intake: {
    minConfidenceThreshold: 0.85,
    requireHumanConfirmOnAmbiguous: true,
    fuzzyMatchMinScore: 80,
  },
  sourcing: {
    priorityOrder: ["nearest_branch", "domestic_dc", "cross_border_dc"],
    allowCrossBorderFallback: true,
    maxShipmentsPerOrder: 3,
    consolidateBranchWithinKm: 35,
  },
  vehicles: {
    smallTruckMaxKg: 1500,
    heavyTruckMaxKg: 12000,
    craneTruckMaxKg: 18000,
    autoAssignCraneForFlaggedSku: true,
  },
  marketBuffers: {
    DK: { dcLeadDays: 1, crossBorderExtraDays: 1, winterPenaltyDays: 0.5 },
    SE: { dcLeadDays: 1, crossBorderExtraDays: 1, winterPenaltyDays: 1.0 },
    NO: { dcLeadDays: 1, crossBorderExtraDays: 2, winterPenaltyDays: 1.5 },
  },
};
