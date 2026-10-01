# 📊 Cambodia Merchandise Trade & Transport ETL Pipeline: Comprehensive Project Progress Report

**Audience:** Executive Supervisor, Project Stakeholders, Engineering Reviewers  
**Data Source:** Official Statistics from General Department of Customs and Excise of Cambodia (GDCE) & Port Authorities (PAS / PPAP)  
**Reporting Period:** 2016–2026 (10-Year Backfill Coverage, 128 Monthly Snapshots)  
**Database:** PostgreSQL 16 2-Tier Data Warehouse (`staging` & `warehouse` schemas)  
**Orchestrator:** Apache Airflow Scheduled Batch DAGs  

---

## 🧭 Executive Summary & Area Status

| Project Area | Lifecycle Scope | Completion % | Verified Status | Key Deliverables & Summary |
| :--- | :--- | :---: | :---: | :--- |
| **1. ETL & Data Warehouse** | End-to-end multi-pillar data ingestion, staging, dimensional modeling, and historical backfill | **100%** | `COMPLETED` | 4 distinct data pillars fully automated; 128 months backfilled; 13/13 unit tests passing. |
| **2. Forecasting Engine** | Econometric time-series models with confidence intervals and horizon projection | **90%** | `IN PROGRESS` | **Holt-Winters** (Champion) & **SARIMAX** (Benchmark) fully fitted and tested; remaining 10% is automated production retraining pipeline. |
| **3. Interactive BI Dashboard** | Streamlit executive analytics hub with 3D Globe, sector filtering, and forecasts | **50%** | `IN PROGRESS` | 50% completed (3D globe, time horizons, sector slicing, rankings, forecast UI); 50% remaining (live production deployment, port throughput depth, mobile layout). |
| **4. Future Work Roadmap** | Strategic enhancements, UN Comtrade product-to-country calibration, live webhooks | **0%** | `PLANNED` | UN Comtrade bilateral weight calibration, automated alerting webhooks, PAS/PPAP real-time container dwell metrics. |

---

## 🗄️ Detailed Area Breakdown

### Sheet 2: ETL & Data Warehouse Architecture (100% COMPLETED)

| Sub-System | Task ID | Pipeline Feature / Deliverable | Target / Artifact | Status | Completion % | Notes & Verification |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **Scrapers & Extractors** | ETL-1.1 | Country Bilateral Trade Web Scraper | `src/scrapers/country.py` | `COMPLETED` | 100% | Extracts monthly bilateral export/import by trading partner nation. |
| **Scrapers & Extractors** | ETL-1.2 | HS Chapter Commodity Web Scraper | `src/scrapers/hs.py` | `COMPLETED` | 100% | Extracts monthly trade values by 2-digit Harmonized System chapters. |
| **Scrapers & Extractors** | ETL-1.3 | Transport Modal Statistics Scraper | `src/scrapers/transport.py` | `COMPLETED` | 100% | Ingests freight weights and values across Sea, Air, Land, and River modes. |
| **Scrapers & Extractors** | ETL-1.4 | SITC Economic Sector Scraper | `src/scrapers/sitc.py` | `COMPLETED` | 100% | Parses Standard International Trade Classification 1-digit groupings. |
| **Data Transformation** | ETL-2.1 | Automated Bilingual Normalization | `src/transformers/*` | `COMPLETED` | 100% | Cleans English & Khmer text, strips whitespace, and removes artifacts. |
| **Data Transformation** | ETL-2.2 | ISO Standard Country Code Mapper | `src/transformers/country_mapper.py` | `COMPLETED` | 100% | Normalizes country names into canonical ISO-2, ISO-3, and geographic IDs. |
| **Data Transformation** | ETL-2.3 | Currency Calibration & Weight Conversion | `src/transformers/*` | `COMPLETED` | 100% | Harmonizes USD ($) vs KHR (៛) currencies and metric tons to kg. |
| **Data Warehouse** | ETL-3.1 | Tier-1 Staging Landing Schema | `staging.*` | `COMPLETED` | 100% | Raw idempotent landing tables for scrapers before transformation. |
| **Data Warehouse** | ETL-3.2 | Tier-2 Production Dimensional Schema | `warehouse.*` | `COMPLETED` | 100% | Star schema with surrogate keys, SCD dimensions, and fact tables. |
| **Data Warehouse** | ETL-3.3 | ETL Execution Audit Run Logger | `warehouse.etl_run_log` | `COMPLETED` | 100% | Logs DAG execution timestamps, row counts, and status for data governance. |
| **Orchestration** | ETL-4.1 | Apache Airflow Monthly Scheduled DAG | `dags/transport_stats_dag.py` | `COMPLETED` | 100% | Schedules recurring monthly extract-transform-load jobs with SLA tracking. |
| **Orchestration** | ETL-4.2 | Parallel Multi-Pillar TaskGroups | `dags/transport_stats_dag.py` | `COMPLETED` | 100% | Executes Country, HS, Transport, and SITC pipelines in parallel. |
| **Orchestration** | ETL-4.3 | Multi-Container Docker Infrastructure | `docker-compose.yml` | `COMPLETED` | 100% | Packages Airflow Webserver, Scheduler, PostgreSQL, and Redis containers. |
| **Backfill & QA** | ETL-5.1 | 10-Year Historical Backfill | `data/raw` & `data/processed` | `COMPLETED` | 100% | Loaded 128 monthly historical snapshots (2016–2026) into PostgreSQL. |
| **Backfill & QA** | ETL-5.2 | Automated QA Unit Test Suite | `tests/test_*.py` | `COMPLETED` | 100% | **13/13 automated unit tests passing** covering scrapers, transforms, and loaders. |

---

### Sheet 3: Forecasting Engine (90% COMPLETED)

> **Core Model Architecture:** Focused strictly on the 2 approved models: **Holt-Winters (Champion)** and **SARIMAX (Benchmark)**. Remaining 10% is automated production retraining pipeline.

| Lifecycle Stage | Task ID | Forecasting Task & Deliverables | Model & Methodology Details | Status | Completion % | Output & Current State |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **1. Data Prep & Stationarity** | FC-1.1 | Monthly Aggregate Series Construction | 128 monthly GDCE trade series (2016–2026) | `COMPLETED` | 100% | Clean continuous monthly export, import, and trade balance datasets. |
| **1. Data Prep & Stationarity** | FC-1.2 | Trend & Seasonal STL Decomposition | Additive & Multiplicative Decomposition | `COMPLETED` | 100% | Identified multi-year upward trajectory and recurring seasonal export surges. |
| **1. Data Prep & Stationarity** | FC-1.3 | Autocorrelation & Unit Root Tests (ADF) | ACF/PACF 36-lags + Augmented Dickey-Fuller | `COMPLETED` | 100% | Confirmed first-difference stationarity $d=1$ for robust time-series modeling. |
| **2. Holt-Winters (Champion)** | FC-2.1 | Holt-Winters Triple Exponential Smoothing | Additive Trend + Multiplicative Seasonality ($m=12$) | `COMPLETED` | 100% | Production champion: captures seasonality, rapid inference (<15ms), robust. |
| **2. Holt-Winters (Champion)** | FC-2.2 | Smoothing Parameters Optimization | Alpha (level), Beta (trend), Gamma (seasonality) | `COMPLETED` | 100% | Optimized smoothing coefficients on 10-year historical dataset. |
| **3. SARIMAX (Benchmark)** | FC-3.1 | SARIMAX Model Order Identification | AIC / BIC Information Criterion Grid Search | `COMPLETED` | 100% | Selected optimal specification: SARIMAX $(1,1,1)\times(1,1,1)_{12}$. |
| **3. SARIMAX (Benchmark)** | FC-3.2 | Parameter Estimation & Convergence | Maximum Likelihood Estimation (MLE) | `COMPLETED` | 100% | Fitted autoregressive and seasonal moving average coefficient matrices. |
| **4. Evaluation & Intervals** | FC-4.1 | Temporal Train/Test Backtesting (80/20) | Expanding Window Cross-Validation | `COMPLETED` | 100% | Evaluated out-of-sample accuracy (RMSE, MAE, MAPE). |
| **4. Evaluation & Intervals** | FC-4.2 | Residual Diagnostics & White Noise Checks | Ljung-Box Q-Test & Jarque-Bera Normality | `COMPLETED` | 100% | Confirmed model residuals are uncorrelated Gaussian white noise. |
| **4. Evaluation & Intervals** | FC-4.3 | Calibrated 95% Confidence Intervals | Point Forecasts + Upper/Lower 95% Bands | `COMPLETED` | 100% | Generates realistic uncertainty bounds for 3 to 24-month horizon forecasts. |
| **5. Deployment & UI** | FC-5.1 | Interactive Streamlit UI Integration (Tab 4) | Horizon Slider (3-24M) & Model Overlay | `COMPLETED` | 100% | Live in dashboard: users can toggle models, compare forecasts, and view KPIs. |
| **5. Deployment & UI** | FC-5.2 | Automated Production Pipeline Deployment | Airflow Automated Retraining & Model Registry | `IN PROGRESS` | 50% | Remaining 10%: automated monthly retraining triggers when new GDCE data arrives. |

---

### Sheet 4: Interactive BI Dashboard (50% COMPLETED)

| Section / Category | Task ID | Dashboard Deliverables & Features | Technical Component | Status | Completion % | Notes & Current Deliverables |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **🟢 Completed Features (50%)** | DASH-1.1 | 3D Interactive World Globe (Orthographic) | `dashboard/app_business.py` | `COMPLETED` | 100% | Clean light 3D globe showing great-circle trade corridors from Cambodia hub. |
| **🟢 Completed Features (50%)** | DASH-1.2 | Dynamic Time Horizons Quick Filter | `dashboard/app_business.py` | `COMPLETED` | 100% | Instant recalculation for L3M, L6M, L12M, and Annual Overview (2016–2026). |
| **🟢 Completed Features (50%)** | DASH-1.3 | Industry Pillar Sector Focus Filter | `dashboard/app_business.py` | `COMPLETED` | 100% | Dynamically filters monthly dynamics, yearly trends, and KPIs by HS chapters (GFT, Agri, Electronics, Auto, Steel). |
| **🟢 Completed Features (50%)** | DASH-1.4 | Executive KPI Cards & Growth Deltas (▲ / ▼) | `dashboard/app_business.py` | `COMPLETED` | 100% | Real-time Total Trade, Exports, Imports, and Net Balance with period-over-period comparisons. |
| **🟢 Completed Features (50%)** | DASH-1.5 | Side-by-Side Market Rankings & Expanders | `dashboard/app_business.py` | `COMPLETED` | 100% | Comparative horizontal bar charts with clean collapsible detail tables (`st.expander`). |
| **🟢 Completed Features (50%)** | DASH-1.6 | Strategic Top Products & Commodities Visuals | `dashboard/app_business.py` | `COMPLETED` | 100% | Top exported/imported HS chapters comparative bar charts with detail tables. |
| **🟢 Completed Features (50%)** | DASH-1.7 | Predictive Forecasting UI with Overlay (Tab 4) | `dashboard/app_business.py` | `COMPLETED` | 100% | Live UI slider (3-24M) with Holt-Winters & SARIMAX co-plotting and 95% intervals. |
| **🟡 Remaining Tasks (50%)** | DASH-2.1 | **Deploy the Live Dashboard to Production Server** | `docker/Dockerfile`, Cloud hosting | `IN PROGRESS` | 30% | Production hosting, custom domain, SSL certification, live persistent URL. |
| **🟡 Remaining Tasks (50%)** | DASH-2.2 | Port Logistics & Modal Throughput Sub-Views | `dashboard/app_business.py` (Tab 2) | `IN PROGRESS` | 30% | Expanding sea freight, river barge, and border post sub-analytics (PAS & PPAP). |
| **🟡 Remaining Tasks (50%)** | DASH-2.3 | Product-to-Country Bilateral Flow Visualization | `dashboard/app_business.py` | `PLANNED` | 0% | Interactive commodity destination flow chart using calibrated UN weights. |
| **🟡 Remaining Tasks (50%)** | DASH-2.4 | Mobile & Tablet Responsive Layout Optimization | `dashboard/*` | `PLANNED` | 0% | Card layout and touch gesture optimization for mobile/tablet viewers. |
| **🟡 Remaining Tasks (50%)** | DASH-2.5 | Automated Trade Anomaly Badges & Growth Alerts | `dashboard/app_business.py` | `PLANNED` | 0% | Visual alert badges highlighting unusual volume spikes or steep drops. |
| **🚀 Future Work Roadmap** | FUT-3.1 | UN Comtrade Bilateral Product Weight Calibration | `src/transformers/*` | `PLANNED` | 0% | Maps specific products (Clothes, Rice) to partner countries using UN weights. |
| **🚀 Future Work Roadmap** | FUT-3.2 | Automated Monthly Data Alert Webhooks | `dags/*` | `PLANNED` | 0% | Automated notifications (Slack/Telegram) when fresh monthly GDCE data is published. |
| **🚀 Future Work Roadmap** | FUT-3.3 | Real-time Port Terminal & Yard Dwell Analytics | `sql/init_warehouse.sql` | `PLANNED` | 0% | Integration of terminal capacity metrics for PAS & PPAP port authorities. |

---

## 📁 Repository Deliverables Index

- **Streamlit BI Dashboard:** [`dashboard/app_business.py`](dashboard/app_business.py)
- **Time-Series Forecasting Engine:** [`src/forecast.py`](src/forecast.py)
- **Airflow Scheduled DAGs:** [`dags/transport_stats_dag.py`](dags/transport_stats_dag.py)
- **Warehouse DDL & Star Schema:** [`sql/init_warehouse.sql`](sql/init_warehouse.sql)
- **Master Excel Progress Report:** [`docs/Project_Progress_Report.xlsx`](docs/Project_Progress_Report.xlsx)
- **Automated Test Suite:** [`tests/test_scrapers.py`](tests/test_scrapers.py), [`tests/test_transformers.py`](tests/test_transformers.py)
