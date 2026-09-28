# Dashboard & Data Warehouse Column Definitions

This document defines the schema, units of measurement, source mappings, and business definitions for all columns and KPIs used in the **Cambodia GDCE Transport Mode Analytics Dashboard** and the underlying PostgreSQL Data Warehouse (`warehouse.fact_transportation_stats`).

---

## 1. Table Schema (`warehouse.fact_transportation_stats`)

| Column Name | Data Type | Nullable | Primary Key | Unit / Format | Description | Source Field (GDCE API) |
|---|---|---|---|---|---|---|
| `date` | `DATE` | `NOT NULL` | Yes | `YYYY-MM-01` | Normalized first calendar day of the reporting month. Used for temporal filtering, chronological ordering, and time-series aggregation. | Derived: `period` + `-01` |
| `period` | `TEXT` | `NOT NULL` | No | `YYYY-MM` (e.g., `2024-01`) | Monthly reporting period as designated by the General Department of Customs and Excise (GDCE). | `payload.period` |
| `regime` | `TEXT` | `NOT NULL` | Yes | `Import` \| `Export` | Customs trade flow regime. `Import` corresponds to inbound customs declarations (`IM`), and `Export` corresponds to outbound declarations (`EX`, `RX`). | `payload.regimes` keys |
| `description` | `TEXT` | `NOT NULL` | Yes | Categorical (English) | Official English description of the international mode of transport (e.g., `Sea transport`, `Road transport`, `Air transport`). | `item.dscEn` |
| `description_kh` | `TEXT` | `NULL` | No | Categorical (Khmer) | Official Khmer language description of the transport mode (e.g., `ការដឹកជញ្ជូនតាមផ្លូវសមុទ្រ`, `ការដឹកជញ្ជូនតាមផ្លូវគោក`). | `item.dscKh` |
| `net_weight_ton` | `DOUBLE PRECISION` | `NULL` | No | Metric Tons ($t$) | Total net cargo freight weight in metric tons, calculated as $\text{net\_weight\_kg} / 1000.0$, rounded to 4 decimal places. | Derived: `item.imNetWeight` / `item.exNetWeight` $\div 1000$ |
| `net_weight_kg` | `DOUBLE PRECISION` | `NULL` | No | Kilograms ($kg$) | Raw net weight in kilograms as reported in customs declarations. | `item.imNetWeight` / `item.exNetWeight` |
| `value_usd` | `DOUBLE PRECISION` | `NULL` | No | US Dollars ($\text{USD } \$$) | Total merchandise trade value expressed in US Dollars ($), rounded to 2 decimal places. | `item.imTotalValueUsd` / `item.exTotalValueUsd` |
| `value_khr` | `BIGINT` | `NULL` | No | Khmer Riel ($\text{KHR } ៛$) | Total merchandise trade value expressed in Cambodian Riel ($៛$). | `item.imTotalValueKhr` / `item.exTotalValueKhr` |
| `loaded_at` | `TIMESTAMPTZ` | `NOT NULL` | No | ISO 8601 UTC Timestamp | Audit timestamp indicating when the record was processed and loaded into the warehouse fact table. | Database Default (`now()`) |

---

## 2. Modes of Transport Reference

| English Name (`description`) | Khmer Name (`description_kh`) | Description |
|---|---|---|
| **Sea transport** | ការដឹកជញ្ជូនតាមផ្លូវសមុទ្រ | Maritime shipping via major ports (e.g., Sihanoukville Autonomous Port - PAS). |
| **Road transport** | ការដឹកជញ្ជូនតាមផ្លូវគោក | Cross-border highway and overland freight (e.g., borders with Vietnam, Thailand, Laos). |
| **Inland waterways transport** | ការដឹកជញ្ជូនតាមផ្លូវទឹកក្នុងប្រទេស | Riverine cargo shipping via Mekong/Tonle Sap waterways and Phnom Penh Autonomous Port (PPAP). |
| **Air transport** | ការដឹកជញ្ជូនតាមផ្លូវអាកាស | High-value, express, and perishable air cargo via international airports (PNH, SAI, KOS). |
| **Rail transport** | ការដឹកជញ្ជូនតាមផ្លូវដែក | Freight moved via the northern and southern national railway lines. |
| **Postal transport** | បញ្ញើប្រៃសនីយ៍ | Postal, courier, and small parcel international trade consignments. |
| **Transport on fixed installation** | ថបនកម្មដឹកជញ្ជូនថេរ | Pipelines, power grids, and fixed infrastructure transfers. |

---

## 3. Dashboard KPI Metric Formulations

| Dashboard Metric | Formulation | Business Interpretation |
|---|---|---|
| **Total Import Value** | $$\sum \text{value\_usd} \quad \text{where } \text{regime} = \text{'Import'}$$ | Total cost/value of inbound goods into Cambodia within the filtered timeframe. |
| **Total Export Value** | $$\sum \text{value\_usd} \quad \text{where } \text{regime} = \text{'Export'}$$ | Total revenue/value of outbound domestic goods shipped abroad. |
| **Trade Balance** | $$\text{Total Export Value} - \text{Total Import Value}$$ | Net merchandise trade balance: positive indicates a trade surplus, negative indicates a trade deficit. |
| **Total Cargo Volume** | $$\sum \text{net\_weight\_ton}$$ | Total physical freight throughput in metric tons across all selected modes. |
| **Mode Value Share (%)** | $$\frac{\text{value\_usd}_{\text{mode}}}{\sum \text{value\_usd}} \times 100$$ | Percentage contribution of a specific transport mode to total trade value. |
| **Mode Weight Share (%)** | $$\frac{\text{net\_weight\_ton}_{\text{mode}}}{\sum \text{net\_weight\_ton}} \times 100$$ | Percentage share of physical cargo weight carried by a specific transport mode. |
