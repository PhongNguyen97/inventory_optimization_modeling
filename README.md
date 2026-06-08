# Forecast-Driven Inventory Optimization System

An end-to-end supply chain analytics project that connects **demand forecasting** with **inventory policy optimization**. The system forecasts retail product-family demand, models forecast uncertainty, simulates stochastic demand paths, and converts those forecasts into replenishment policy parameters such as safety stock, reorder point, order quantity, and order-up-to level.

The project is built around a practical supply chain question:

> How can demand forecasts be translated into inventory policies that maintain high service levels while controlling holding, ordering, and shortage costs?

The final inventory model targets a customer fill rate of **at least 95%** under stochastic weekly demand, deterministic lead time, and lost-sales assumptions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Business Problem](#business-problem)
3. [Dataset and Scope](#dataset-and-scope)
4. [Solution Architecture](#solution-architecture)
5. [Key Results](#key-results)
6. [Repository Structure](#repository-structure)
7. [Methodology](#methodology)
8. [Technical Highlights](#technical-highlights)
9. [How to Run the Project](#how-to-run-the-project)
10. [Outputs and Reporting](#outputs-and-reporting)
11. [Assumptions and Limitations](#assumptions-and-limitations)
12. [Future Improvements](#future-improvements)
13. [Skills Demonstrated](#skills-demonstrated)

---

## Project Overview

This project contains two connected analytical systems:

| System | Purpose | Main Output |
|---|---|---|
| **Demand Forecasting System** | Predict future product-family demand using traditional time-series models and machine learning comparison models. | Weekly and daily forecast outputs for the test period. |
| **Inventory Optimization System** | Convert forecasts and forecast uncertainty into cost-optimal replenishment policies. | Optimized safety stock, reorder point, order quantity, order-up-to level, service metrics, and cost metrics. |

The project moves beyond prediction accuracy alone. It uses demand forecasts as operational inputs for inventory decisions, which is closer to how forecasting creates business value in supply chain planning.

---

## Business Problem

Retail inventory planning requires balancing two competing objectives:

1. **Service performance**: hold enough inventory to avoid stockouts and satisfy customer demand.
2. **Cost efficiency**: avoid excessive inventory, unnecessary replenishment, and avoidable holding cost.

A demand forecast is useful only if it can support decisions such as:

- how much safety stock to hold;
- when to replenish;
- how much to order;
- how service level changes when lead time or cost assumptions change;
- whether a policy remains stable under demand uncertainty.

This project addresses that decision problem by building a workflow that connects forecasting, simulation, optimization, validation, and sensitivity analysis.

---

## Dataset and Scope

The project is based on retail store sales data from Favorita stores in Ecuador. The modeling workflow uses sales history together with relevant external and operational variables such as promotions, holidays, oil prices, and store metadata.

To get data, access this link (Kaggle) [Data Source](https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data)

### Forecasting Scope

The forecasting system evaluates product-family demand patterns and generates future sales forecasts. The pipeline includes:

- transaction and feature preprocessing;
- holiday and promotion feature engineering;
- oil price imputation;
- earthquake impact modeling;
- traditional time-series forecasting;
- machine learning and deep learning comparison;
- out-of-sample forecast generation;
- daily disaggregation from weekly forecasts.

### Inventory Optimization Scope

The inventory optimization system focuses on three representative product families:

| Product Family | Policy Type | Reason for Selection |
|---|---|---|
| `GROCERY I` | Continuous review `(s,Q)` | High-volume and frequently purchased product family. |
| `BEVERAGES` | Continuous review `(s,Q)` | High-volume and frequently purchased product family. |
| `CLEANING` | Periodic review `(R,S)` | Stable demand pattern suitable for scheduled review. |

The inventory model uses **weekly demand**. Daily forecasts are generated in the forecasting system but are not used as the main demand scale for inventory optimization.

---

## 📋 Solution Architecture

The system follows a forecast-driven inventory optimization architecture.

```text
Raw Retail Data
    ↓
Data Cleaning and Feature Engineering
    ↓
Demand Forecasting System
    ├── Traditional time-series models              
    ├── Machine learning / deep learning comparison
    ├── Hybrid model-routing evaluation
    └── Out-of-sample weekly and daily forecasts
    ↓
Forecast Error and Demand Uncertainty Modeling
    ├── Forecast ratio modeling
    ├── Residual modeling
    ├── Empirical bootstrap
    ├── KDE comparison
    └── Gamma benchmark
    ↓
Inventory Optimization System
    ├── Weekly stochastic demand simulation
    ├── Continuous review `(s,Q)` policy
    ├── Periodic review `(R,S)` policy
    ├── Two-stage grid search
    ├── Local search refinement
    ├── Monte Carlo validation
    ├── Historical rolling backtest
    └── Sensitivity analysis
    ↓
Final Inventory Policy Recommendations
```

---

## Key Results

Under the base-case service target of **95% fill rate**, the optimized policies achieved fill rates above the target for all selected product families.

| Product Family | Policy Type | Safety Stock | Reorder Point / Review Period | Order Quantity / Order-Up-To Level | Realized Fill Rate | Realized CSL | Average Inventory | Total Cost Index |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `GROCERY I` | `(s,Q)` | 487,622.56 | 1,750,781.15 | 314,433.58 | 99.16% | 93.13% | 609,857.95 | 543,439.88 |
| `BEVERAGES` | `(s,Q)` | 588,068.73 | 1,565,680.61 | 260,348.02 | 99.66% | 98.47% | 687,134.05 | 156,552.77 |
| `CLEANING` | `(R,S)` | 0.00 | `R = 1` week | 798,371.82 | 100.00% | 100.00% | 446,039.91 | 1,361.65 |

### Main Business Insights

- The optimized policies achieved the required service level under simulated stochastic demand.
- `GROCERY I` and `BEVERAGES` require large safety stock buffers because they are high-volume product families with meaningful forecast uncertainty.
- `CLEANING` achieved the service target with zero safety stock in the base case because its weekly demand was highly stable under the selected uncertainty model.
- Lead time is a major inventory driver. When lead time increases, the risk period expands and safety stock requirements rise substantially.
- Simulation-based optimization provides stronger operational evidence than relying only on deterministic forecasts or raw historical averages.

> **Cost interpretation:** The project uses a normalized unit cost of `c = 1`. Therefore, total cost should be interpreted as a relative cost index rather than actual company dollar cost.

---

## 📋 Repository Structure

```text
Inventory Optimization Modeling/
├── README.md                                           
├── Inventory Optimization Modeling Workflow.png            # High-level end-to-end workflow diagram
│
├── Demand Forecasting System/                              # SUB-SYSTEM I: DEMAND FORECASTING
│   ├── Demand Forecasting System Summary.md                # Summary report for forecasting system
│   ├── processing.ipynb                                    # Phase 1: Ingestion, cleaning & feature engineering
│   ├── data/                                               # Cleaned & aggregated weekly/daily data
│   │   ├── final_train_df.csv                              # Raw daily aggregated train set 
│   │   ├── final_test_df.csv                               # Raw daily aggregated test set
│   │   ├── weekly_features.csv                             # Consolidated weekly train features
│   │   ├── actual_fitted_sales_on_train_final.csv          # Combined actual & fitted training sales (Inventory System input)
│   │   ├── actual_fitted_sales_on_test_final.csv           # Out-of-sample weekly test forecasts (Inventory System input)
│   │   └── segmentation_features.csv                       # Segmented store features
│   ├── models/                                             # Modeling assets and winning configurations
│   │   ├── traditional_model_implementation.ipynb          # Phase 2: Statistical modeling
│   │   ├── ml_dl_model_implementation.ipynb                # Phase 3: ML/DL modeling & hyperparameter tuning
│   │   ├── best_models_per_family.csv                      # Winning traditional models by family
│   │   ├── default_ml_dl_model_performance.csv             # Baseline ML model performance
│   │   ├── tuned_ml_dl_model_performance.csv               # Tuned ML model performance
│   │   └── production_traditional_models/                  # Saved models' .pkl objects
│   └── results/                                            # Evaluation & final inference reports
│       ├── final_model.ipynb                               # Phase 4: Hybrid evaluation and routing
│       ├── forecast_on_test_data.ipynb                     # Phase 5: Test set forecasting & disaggregation
│       ├── feasibility_evaluation.ipynb                    # Phase 6: Feasibility auditing & QA
│       ├── ml_trad_model_comparison.csv                    # Detailed validation comparison
│       ├── hybrid_fitted_values.csv                        # Historical fitted hybrid values
│       ├── test_predictions_weekly_edit_3.csv              # Out-of-sample weekly predictions
│       └── test_predictions_daily_edit_3.csv               # Out-of-sample daily predictions
│
└── Inventory Optimization System/                          # SUB-SYSTEM II: INVENTORY OPTIMIZATION
    ├── Inventory Optimization Summary.md                   # Summary report for inventory optimization system
    ├── main.py                                             # Master pipeline orchestrator script
    ├── requirements.txt                                    # Python package dependencies
    ├── configs/
    │   └── inventory_config.yaml                           # System configurations, costs, and policy settings
    ├── src/                                                # Production-grade Python modules
    │   ├── config.py                                       # Configuration loader & weekly cost derivation
    │   ├── data_loader.py                                  # Time-series alignment and validation loader
    │   ├── demand_uncertainty.py                           # Forecast ratio bias and error scaling calculations
    │   ├── distributions.py                                # Bootstrapping, KDE, & Gamma fitting
    │   ├── metrics.py                                      # Operational KPIs: Fill Rate, CSL, Holding/Ordering/Shortage costs
    │   ├── optimization.py                                 # Multi-stage Grid Search & Neighborhood Local Search
    │   ├── policies.py                                     # Policy definitions for SQ (continuous) & RS (periodic)
    │   ├── simulation.py                                   # Vectorized week-by-step lost-sales simulation engine
    │   ├── validation.py                                   # Monte Carlo validation & dynamic historical rolling backtests
    │   ├── sensitivity.py                                  # Sensitivity sweep engine (costs, service, lead time, uncertainty)
    │   └── reporting.py                                    # Automated CSV exports and chart generator
    ├── notebooks/                                          # Iterative prototyping notebooks
    │   ├── 01_data_preparation_check.ipynb                 # Step 1: Pre-checks & data alignment
    │   ├── 02_uncertainty_modeling.ipynb                   # Step 2: Error bootstrapping and distribution fitting
    │   ├── 03_policy_optimization.ipynb                    # Step 3: Grid search & local search parameter tuning
    │   ├── 04_validation_backtesting.ipynb                 # Step 4: Monte Carlo validation & dynamic backtesting
    │   └── 05_sensitivity_analysis_reporting.ipynb         # Step 5: Sensitivity analysis sweeps & reporting
    └── outputs/                                            # Output folder containing tables, plots, and reports
        ├── plots/                                          # Visual diagnostic charts (ending stock distributions, sensitivity plots)
        ├── policy_results/                                 # CSV results for optimal policy parameters
        ├── sensitivity_results/                            # CSV results for sensitivity analysis sweeps
        └── tables/                                         # Power BI integration tables and validation logs
```

---

## Methodology

## 1. Demand Forecasting System 📈

The demand forecasting system creates the expected future demand path used by the inventory optimization model.

### 1.1 Data Ingestion, Cleaning, and Feature Engineering

The preprocessing workflow combines transaction, holiday, oil price, promotion, and store-level data into modeling-ready time-series datasets.

Key feature engineering steps include:

- **Oil price imputation** using forward-fill and interpolation to maintain a continuous daily external signal.
- **Holiday cleanup** to handle transferred holidays, bridge holidays, and national/local holiday effects.
- **Earthquake recovery feature** to represent the April 2016 Ecuador earthquake impact and recovery window.
- **Cyclical calendar encoding** using sine and cosine transformations for periodic features. Converted calendar indices (day of week, day of month, month) into continuous trigonometric variables to ensure smooth transitions between calendar boundaries.
$$\text{Feature}_{\sin} = \sin\left(\frac{2\pi \times \text{value}}{\text{period}}\right), \quad \text{Feature}_{\cos} = \cos\left(\frac{2\pi \times \text{value}}{\text{period}}\right)$$
- **Lag and rolling features** for time-series memory.
- **Weekly aggregation** for model training and inventory optimization compatibility.

### 1.2 Traditional Time-Series Modeling

Traditional forecasting models were trained independently by product family. Candidate models included:

- Naive baseline;
- Seasonal naive baseline;
- ARIMA;
- SARIMA;
- SARIMAX with exogenous variables.

The best traditional model for each family was selected using validation MAPE.

| Family | Model | Optimized Parameters / Orders | MAE | RMSE | MAPE (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BEVERAGES** | SARIMAX | $(2, 0, 0) \times (1, 0, 0, 52)$ | 175,188.14 | 185,533.39 | 24.11% |
| **BREAD/BAKERY** | SARIMAX | $(1, 0, 1) \times (1, 0, 1, 52)$ | 9,323.33 | 10,891.51 | 7.63% |
| **CLEANING** | SARIMAX | $(1, 0, 1) \times (1, 0, 0, 52)$ | 70,295.95 | 79,337.73 | 19.94% |
| **DAIRY** | Seasonal Naive | $\text{lag} = 52$ | 68,362.50 | 112,884.91 | 70.70% |
| **DELI** | SARIMAX | $(1, 0, 1) \times (1, 0, 0, 52)$ | 5,724.12 | 6,466.95 | 11.57% |
| **GROCERY I** | SARIMAX | $(0, 0, 2) \times (1, 0, 1, 52)$ | 143,142.28 | 173,534.39 | 15.87% |
| **MEATS** | Seasonal Naive | $\text{lag} = 52$ | 31,941.71 | 49,574.70 | 75.17% |
| **PERSONAL CARE** | SARIMAX | $(3, 0, 3) \times (1, 0, 0, 52)$ | 8,951.66 | 11,823.58 | 19.65% |
| **POULTRY** | SARIMAX | $(1, 0, 2) \times (1, 0, 0, 52)$ | 6,820.98 | 7,569.74 | 10.31% |

### 1.3 Machine Learning and Deep Learning Comparison

Machine learning and deep learning models were evaluated to capture nonlinear relationships and feature interactions. Candidate models included:

- Decision Tree;
- Random Forest;
- XGBoost;
- Dense Neural Network;
- LSTM.

Both recursive and direct forecasting strategies were considered. A dynamic boundary-shifting tuning process was implemented to expand the search grid when the best hyperparameter appeared at the boundary of the current search space.

### 1.4 Hybrid Model Routing

A family-level routing rule compared traditional and machine learning validation performance:

```text
If ML validation MAPE <= traditional validation MAPE:
    route family to ML model
else:
    route family to traditional model
```

This allowed each product family to use the model type that performed better in validation.

| Product Family | Traditional MAPE | ML MAPE | MAPE Improvement % | Selected Model Route |
| :--- | :---: | :---: | :---: | :---: |
| **BEVERAGES** | 11.14% | 6.02% | **+45.99%** | Machine Learning (Direct) |
| **BREAD/BAKERY** | 5.42% | 6.95% | -28.19% | Traditional (SARIMAX) |
| **CLEANING** | 7.44% | 5.95% | **+20.13%** | Machine Learning (Direct) |
| **DAIRY** | 19.39% | 6.28% | **+67.60%** | Machine Learning (Direct) |
| **DELI** | 6.28% | 7.84% | -24.96% | Traditional (SARIMAX) |
| **GROCERY I** | 7.64% | 2.76% | **+63.83%** | Machine Learning (Direct) |
| **MEATS** | 8.21% | 6.99% | **+14.88%** | Machine Learning (Direct) |
| **PERSONAL CARE** | 9.94% | 10.30% | -3.70% | Traditional (SARIMAX) |
| **POULTRY** | 7.62% | 7.20% | **+5.47%** | Machine Learning (Direct) |

### 1.5 Out-of-Sample Forecasting and Technical Fallback

The out-of-sample test period did not contain future actual sales, so lag-based and rolling features had to be carefully constructed using the latest available historical information and known future exogenous variables.

During final out-of-sample forecasting, model verification identified unreliable saved machine learning model artifacts. To preserve forecasting robustness, the final out-of-sample pipeline routed all product families to their winning traditional statistical models.

This fallback decision prioritized reliable production inference over using a model artifact that produced unrealistic forecasts.

### 1.6 Daily Disaggregation

Although the inventory model uses weekly demand, the forecasting system also produced daily forecasts. Weekly forecasts were disaggregated into daily values using historical day-of-week sales weights:

$$
\text{Daily Forecast}_{family,t}
=
\text{Weekly Forecast}_{family,w}
\times
\text{Historical Day-of-Week Weight}_{family,dow(t)}
$$

This avoids the unrealistic assumption that weekly demand should be divided evenly across seven days.

---

## 2. Inventory Optimization System 📦

The inventory optimization system converts weekly forecasts and forecast uncertainty into replenishment policy recommendations.

### 2.1 Policy Design

Two inventory policies are modeled:

| Policy | Used For | Rule |
|---|---|---|
| Continuous review `(s,Q)` | `GROCERY I`, `BEVERAGES` | Place an order of size `Q` when inventory position falls to or below reorder point `s`. |
| Periodic review `(R,S)` | `CLEANING` | Review inventory every `R` weeks and order enough to raise inventory position to `S`. |

Base-case assumptions:

| Parameter | Value |
|---|---:|
| Demand scale | Weekly |
| Lead time | `L = 1` week |
| Review period for `(R,S)` | `R = 1` week |
| Target fill rate | `β >= 0.95` |
| Shortage assumption | Lost sales |
| Unit cost | Normalized to `c = 1` |
| Annual holding cost rate | 15% |
| Weekly holding cost | `0.15 / 52 = 0.0028846` |

### 2.2 Forecast-Uncertainty Modeling

The model separates expected demand from unexpected demand uncertainty.

Expected demand comes from the weekly forecast:

$$
\hat{D}_w
$$

Forecast uncertainty is represented using forecast ratios and residuals:

$$
r_w = \frac{D_w}{\max(\hat{D}_w, \epsilon)}
$$

$$
e_w = D_w - \hat{D}_w
$$

The base-case simulation uses forecast-ratio bootstrapping with bias correction and extreme-ratio capping.

### 2.3 Stochastic Demand Simulation

Simulated weekly demand paths are generated by combining the expected forecast path with sampled forecast uncertainty:

$$
D_{w}^{sim,i}=\max(0,\hat{D}_w \times r_w^{sampled,i})
$$

The model generates 10,000 simulated future demand paths for Monte Carlo evaluation.

### 2.4 Risk-Period Demand

The risk period depends on the selected inventory policy:

| Product Family | Policy | Risk Period |
|---|---|---:|
| `GROCERY I` | `(s,Q)` | `L = 1` week |
| `BEVERAGES` | `(s,Q)` | `L = 1` week |
| `CLEANING` | `(R,S)` | `R + L = 2` weeks |

### 2.5 Optimization Objective

The policy optimization minimizes total cost subject to the fill-rate constraint:

$$
\min \; \text{Total Cost}
=
H_{week} \times \text{Average Inventory}
+
K \times \text{Number of Orders}
+
B \times \text{Units Short}
$$

Subject to:

$$
\beta^{sim} \geq 0.95
$$

### 2.6 Optimization Method

The inventory optimization process uses:

1. **EOQ initialization** for `(s,Q)` policies.
2. **Coarse grid search** over safety stock and order quantity candidates.
3. **Fine grid search** around the best feasible candidate.
4. **Local search refinement** as an exploratory comparison.
5. **Feasibility filtering** using simulated fill rate.

### 2.7 Validation

The optimized policies are validated using:

- **Monte Carlo validation** across stochastic demand paths. Simulated the policies across 10,000 randomized demand paths and evaluated them against three **Validation Gates**:
    1.  *Service Level Gate*: Realized average fill rate must be $\ge 95\%$.
    2.  *Operational Feasibility Gate*: Average number of orders placed must be $> 0$ (verifying the policy is active).
    3.  *Cost Stability Gate*: Coefficient of Variation of total cost must be low ($CV_{\text{cost}} < 10.0$) to avoid tail-risk cost volatility.
- **Historical rolling backtesting** using chronological historical forecasts and realized sales. Simulated chronological, week-by-week performance over actual historical sales, implementing **dynamic parameters** that adjust weekly based on the upcoming forecast:
    *   Continuous $(s_t, Q)$ reorder point: $s_t = \text{forecast}_{t+1} + S_s$ (covering the 1-week lead time risk window).
    *   Periodic $(R, S_t)$ order-up-to level: $S_t = (\text{forecast}_{t+1} + \text{forecast}_{t+2}) + S_s$ (covering the 2-week risk period under weekly reviews).
    This backtest verified that my dynamic policies successfully adapt to changing demand trends without causing stockouts or excess holding.

### 2.8 Sensitivity Analysis

Sensitivity analysis tests whether the selected policies remain reasonable when assumptions change.

Scenarios include:

- holding cost rate changes ($10\% - 25\%$);
- order cost changes ($10 - 50$);
- shortage cost changes ($50\% - 150\%$);
- service target changes ($\beta = 90\%, 95\%, 98\%$);
- lead time changes ($1 - 2$ weeks);
- ratio cap changes;
- uncertainty model changes;
- gamma benchmark comparison.

---

## Technical Highlights

| Area | Implementation Highlight |
|---|---|
| Forecasting | Built traditional time-series and ML/DL comparison pipelines by product family. |
| Feature Engineering | Engineered oil price, holiday, earthquake, cyclical, lag, and rolling features. |
| Hybrid Modeling | Developed a model-routing framework comparing traditional and ML validation performance. |
| Robust Inference | Implemented fallback logic when saved ML artifacts produced unreliable out-of-sample behavior. |
| Demand Uncertainty | Modeled forecast error using ratio and residual approaches instead of raw demand variation only. |
| Simulation | Built a vectorized weekly lost-sales simulation engine for Monte Carlo demand-path evaluation. |
| Optimization | Implemented two-stage grid search and local search for inventory policy selection. |
| Validation | Used Monte Carlo validation and historical rolling backtesting to test policy credibility. |
| Sensitivity Analysis | Tested service, cost, lead time, and uncertainty-model robustness. |
| Reporting | Exported tables and plots for Power BI and executive reporting. |

---

## How to Run the Project

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Inventory Optimization Modeling"
```

### 2. Create and Activate a Python Environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install Dependencies

```bash
cd "Inventory Optimization System"
pip install -r requirements.txt
```

### 4. Run the Demand Forecasting Pipeline

The demand forecasting system is notebook-driven for transparency and inspection. Run the notebooks in this order:

```text
Demand Forecasting System/
├── processing.ipynb
├── models/traditional_model_implementation.ipynb
├── models/ml_dl_model_implementation.ipynb
└── results/
    ├── final_model.ipynb
    ├── forecast_on_test_data.ipynb
    └── feasibility_evaluation.ipynb
```

### 5. Run the Inventory Optimization Pipeline

The inventory optimization system is modularized into reusable Python source files and can be executed through the main runner:

```bash
cd "Inventory Optimization System"
python main.py
```

The runner performs the following workflow:

1. load configuration assumptions;
2. load and validate input data;
3. construct forecast uncertainty;
4. generate Monte Carlo demand paths;
5. optimize inventory policies;
6. validate policies;
7. run sensitivity analysis;
8. export final tables and plots.

---

## Outputs and Reporting 📋

The project generates several output types:

| Output Type | Example |
|---|---|
| Forecast outputs | Weekly and daily test predictions. |
| Model comparison tables | Traditional vs. ML performance by product family. |
| Inventory policy tables | Safety stock, reorder point, order quantity, fill rate, CSL, and cost. |
| Validation outputs | Monte Carlo validation and rolling backtest results. |
| Sensitivity outputs | Scenario-level policy and cost comparisons. |
| Dashboard-ready data | Power BI-ready CSV tables. |
| Visual diagnostics | Forecast continuation plots, demand distribution plots, inventory validation charts, and sensitivity plots. |

The project is designed to support a final Power BI dashboard and executive presentation showing:

- forecasting model performance;
- inventory policy recommendations;
- simulated service-level performance;
- validation evidence;
- cost-service trade-offs;
- lead-time sensitivity;
- policy robustness.

---

## Assumptions and Limitations 📋

This project is a portfolio and modeling project, not a direct production deployment. Important assumptions include:

1. **Weekly demand scale**: Inventory optimization uses weekly demand only.
2. **Selected product families**: Inventory policies are optimized for `GROCERY I`, `BEVERAGES`, and `CLEANING`.
3. **Deterministic lead time**: The base model assumes `L = 1` week.
4. **Periodic review period**: The `(R,S)` policy uses `R = 1` week.
5. **Lost sales**: Unmet demand is treated as lost sales, not backorders.
6. **Normalized cost**: Unit cost is set to `c = 1`, so total cost is a relative cost index.
7. **Short test horizon**: The out-of-sample test period is short, so Monte Carlo simulation and historical backtesting are used to strengthen validation.
8. **Forecast uncertainty assumption**: Future uncertainty is assumed to be represented by historical forecast ratios or residuals.
9. **Policy-class assumption**: The model optimizes parameters conditional on selected policy types; it does not globally optimize policy class selection across all possible policies.

These assumptions are explicitly tested or discussed through validation and sensitivity analysis where possible.

---

## Future Improvements 🚀

Potential extensions include:

- adding stochastic lead time;
- optimizing policy type selection rather than assigning policy type by assumption;
- incorporating actual product unit costs and gross margins;
- modeling store-level or SKU-level inventory policies;
- adding supplier constraints, minimum order quantities, and storage capacity limits;
- improving ML model serialization and deployment reliability;
- adding automated tests for simulation, optimization, and validation modules;
- converting the forecasting notebooks into a fully script-based pipeline;
- deploying the inventory optimization workflow as an interactive dashboard or application.

---

## Skills Demonstrated

This project demonstrates practical capability in:

- supply chain analytics;
- demand forecasting;
- time-series feature engineering;
- machine learning model comparison;
- forecast-error modeling;
- stochastic simulation;
- inventory policy design;
- safety stock optimization;
- Monte Carlo validation;
- sensitivity analysis;
- Python modular programming;
- reproducible analytical workflow design;
- Power BI-ready reporting preparation;
- translating predictive analytics into operational decision support.

---

## Project Summary

This project demonstrates how a demand forecasting system can be converted into an inventory decision-support system. Instead of treating forecasting as the final output, the workflow uses forecasts as inputs for stochastic simulation and replenishment policy optimization.

The final result is an evidence-based inventory optimization framework that recommends policy parameters, validates service-level performance, evaluates cost trade-offs, and supports executive reporting for supply chain decision-making.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
