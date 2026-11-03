export interface StockItem {
  sku: string;
  name: string;
  unit: string;
  weight_kg: number;
  requires_crane: boolean;
  cross_border_only: boolean;
  stock_dk: number;
  stock_se: number;
  stock_no: number;
  total_stock: number;
  primary_source: "DK" | "SE" | "NO" | "CROSS_BORDER";
  is_low_stock: boolean;
}

export const MOCK_STOCK_ITEMS: StockItem[] = [
  {
    sku: "GYP-13-2400",
    name: "Gipsplade standard 13mm 1200x2400",
    unit: "stk",
    weight_kg: 25.5,
    requires_crane: false,
    cross_border_only: false,
    stock_dk: 1420,
    stock_se: 2100,
    stock_no: 890,
    total_stock: 4410,
    primary_source: "DK",
    is_low_stock: false,
  },
  {
    sku: "GYP-15-FIRE",
    name: "Gipsplade brand 15mm 1200x2400",
    unit: "stk",
    weight_kg: 32.0,
    requires_crane: false,
    cross_border_only: false,
    stock_dk: 480,
    stock_se: 620,
    stock_no: 310,
    total_stock: 1410,
    primary_source: "SE",
    is_low_stock: false,
  },
  {
    sku: "ISO-GLAS-100",
    name: "Isolering glasuld 100mm",
    unit: "m2",
    weight_kg: 2.2,
    requires_crane: false,
    cross_border_only: false,
    stock_dk: 3200,
    stock_se: 4500,
    stock_no: 1900,
    total_stock: 9600,
    primary_source: "DK",
    is_low_stock: false,
  },
  {
    sku: "ISO-ROCK-150",
    name: "Rockwool stenuld flexibatts 150mm",
    unit: "pak",
    weight_kg: 4.8,
    requires_crane: false,
    cross_border_only: false,
    stock_dk: 840,
    stock_se: 1200,
    stock_no: 450,
    total_stock: 2490,
    primary_source: "DK",
    is_low_stock: false,
  },
  {
    sku: "TIM-C24-45-195",
    name: "Konstruktionstræ C24 45x195 4.8m",
    unit: "m",
    weight_kg: 4.6,
    requires_crane: false,
    cross_border_only: false,
    stock_dk: 2100,
    stock_se: 8500,
    stock_no: 3400,
    total_stock: 14000,
    primary_source: "SE",
    is_low_stock: false,
  },
  {
    sku: "GLU-115-360-6M",
    name: "Limtræsbjælke 115x360 6m",
    unit: "stk",
    weight_kg: 115.0,
    requires_crane: true,
    cross_border_only: true,
    stock_dk: 0,
    stock_se: 42,
    stock_no: 0,
    total_stock: 42,
    primary_source: "CROSS_BORDER",
    is_low_stock: true,
  },
  {
    sku: "STEEL-HEA-200-6M",
    name: "Stålbjælke HEA 200 6m (Tung stål)",
    unit: "stk",
    weight_kg: 254.0,
    requires_crane: true,
    cross_border_only: true,
    stock_dk: 0,
    stock_se: 84,
    stock_no: 12,
    total_stock: 96,
    primary_source: "CROSS_BORDER",
    is_low_stock: false,
  },
  {
    sku: "ARM-RIONET-8MM",
    name: "Armeringsnet rionet 8mm 150x150",
    unit: "stk",
    weight_kg: 42.5,
    requires_crane: true,
    cross_border_only: false,
    stock_dk: 320,
    stock_se: 510,
    stock_no: 180,
    total_stock: 1010,
    primary_source: "DK",
    is_low_stock: false,
  },
  {
    sku: "CEM-AALBORG-25",
    name: "Basis cement Aalborg Portland 25kg",
    unit: "sæk",
    weight_kg: 25.0,
    requires_crane: false,
    cross_border_only: false,
    stock_dk: 1850,
    stock_se: 940,
    stock_no: 620,
    total_stock: 3410,
    primary_source: "DK",
    is_low_stock: false,
  },
  {
    sku: "AGG-SAND-1000",
    name: "Støbesand Bigbag 1000kg",
    unit: "stk",
    weight_kg: 1000.0,
    requires_crane: true,
    cross_border_only: false,
    stock_dk: 85,
    stock_se: 140,
    stock_no: 65,
    total_stock: 290,
    primary_source: "DK",
    is_low_stock: false,
  },
  {
    sku: "MEM-DAMP-020",
    name: "Dampspærre folie 0.20mm 2x50m",
    unit: "rl",
    weight_kg: 18.0,
    requires_crane: false,
    cross_border_only: false,
    stock_dk: 240,
    stock_se: 380,
    stock_no: 190,
    total_stock: 810,
    primary_source: "SE",
    is_low_stock: false,
  },
  {
    sku: "ACO-TROLD-25",
    name: "Troldtekt akustikplade 25mm natur",
    unit: "m2",
    weight_kg: 12.5,
    requires_crane: false,
    cross_border_only: true,
    stock_dk: 0,
    stock_se: 0,
    stock_no: 160,
    total_stock: 160,
    primary_source: "CROSS_BORDER",
    is_low_stock: true,
  },
];

export interface ErpInspectorSample {
  id: "dk" | "se" | "no";
  name: string;
  format: string;
  sourceSystem: string;
  rawPayload: string;
  normalizedJson: string;
}

export const NATIVE_ERP_SAMPLES: ErpInspectorSample[] = [
  {
    id: "dk",
    name: "DK ERP Adapter (Danish Semicolon CSV)",
    format: "CSV",
    sourceSystem: "Microsoft Dynamics Business Central (DK Branch Engine)",
    rawPayload: `varenr;beskrivelse;afd_kode;lager_antal;enhed;kraever_kran
GYP-13-2400;Gipsplade standard 13mm 1200x2400;DK-GLO-01;850;stk;0
GYP-13-2400;Gipsplade standard 13mm 1200x2400;DK-AAR-01;570;stk;0
ISO-ROCK-150;Rockwool stenuld flexibatts 150mm;DK-AAR-01;840;pak;0
ARM-RIONET-8MM;Armeringsnet rionet 8mm 150x150;DK-ODE-01;320;stk;1
AGG-SAND-1000;Støbesand Bigbag 1000kg;DK-GLO-01;85;stk;1`,
    normalizedJson: JSON.stringify(
      [
        {
          sku: "GYP-13-2400",
          name: "Gipsplade standard 13mm 1200x2400",
          country: "DK",
          warehouse_code: "DK-GLO-01",
          available_qty: 850,
          unit: "stk",
          requires_crane: false,
        },
        {
          sku: "ARM-RIONET-8MM",
          name: "Armeringsnet rionet 8mm 150x150",
          country: "DK",
          warehouse_code: "DK-ODE-01",
          available_qty: 320,
          unit: "stk",
          requires_crane: true,
        },
      ],
      null,
      2
    ),
  },
  {
    id: "se",
    name: "SE ERP Adapter (Swedish JSON)",
    format: "JSON (Svenska)",
    sourceSystem: "Visma Business / Jeeves ERP (Sweden DC Central)",
    rawPayload: JSON.stringify(
      [
        {
          artikelnr: "STEEL-HEA-200-6M",
          benamning: "Stålbalk HEA 200 S355 6m",
          lagerstalle: "SE-DC-JBG",
          fysiskt_saldo: 84,
          reserverat_antal: 6,
          enhet: "st",
          kranbil: 1,
        },
        {
          artikelnr: "TIM-C24-45-195",
          benamning: "Konstruktionsvirke C24 45x195",
          lagerstalle: "SE-DC-JOR",
          fysiskt_saldo: 8500,
          reserverat_antal: 480,
          enhet: "m",
          kranbil: 0,
        },
      ],
      null,
      2
    ),
    normalizedJson: JSON.stringify(
      [
        {
          sku: "STEEL-HEA-200-6M",
          name: "Stålbjælke HEA 200 6m (Tung stål)",
          country: "SE",
          warehouse_code: "SE-DC-JBG",
          available_qty: 78,
          unit: "stk",
          requires_crane: true,
        },
        {
          sku: "TIM-C24-45-195",
          name: "Konstruktionstræ C24 45x195 4.8m",
          country: "SE",
          warehouse_code: "SE-DC-JOR",
          available_qty: 8020,
          unit: "m",
          requires_crane: false,
        },
      ],
      null,
      2
    ),
  },
  {
    id: "no",
    name: "NO ERP Adapter (English JSON)",
    format: "JSON (Standard)",
    sourceSystem: "SAP ECC / S/4HANA (Optimera Logistics Hub)",
    rawPayload: JSON.stringify(
      [
        {
          sku: "ACO-TROLD-25",
          product_name: "Troldtekt Acoustic Panel Plus 25mm",
          warehouse_id: "NO-DC-OSL",
          available_qty: 160,
          uom: "M2",
          requires_crane: false,
          customs_tariff_code: "4411.14",
        },
        {
          sku: "GYP-13-2400",
          product_name: "Standard Gypsum Board 13mm",
          warehouse_id: "NO-BR-BRG",
          available_qty: 890,
          uom: "STK",
          requires_crane: false,
          customs_tariff_code: "6809.11",
        },
      ],
      null,
      2
    ),
    normalizedJson: JSON.stringify(
      [
        {
          sku: "ACO-TROLD-25",
          name: "Troldtekt akustikplade 25mm natur",
          country: "NO",
          warehouse_code: "NO-DC-OSL",
          available_qty: 160,
          unit: "m2",
          requires_crane: false,
        },
      ],
      null,
      2
    ),
  },
];
