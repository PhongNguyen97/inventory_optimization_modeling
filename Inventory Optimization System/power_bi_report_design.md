# Power BI Dashboard & Executive Report Design Guide

This guide details the structure, visual components, key messages, and metrics to convey in your final executive report and Power BI dashboard for the **Inventory Optimization Modeling** project. 

To keep the report concise (under 10 pages) while showcasing your technical and analytical capabilities to reviewers, I design a high-impact **5-page report layout** that connects the **Demand Forecasting System (Part 1)** and the **Inventory Optimization System (Part 2)**.

---

## Page 1: Executive Portal — End-to-End Supply Chain Integration

### 🎯 Objective
Introduce the project portal, define the connection between demand forecasting (predictions) and inventory optimization (actions), and present high-level supply chain workflow integration.

### 💡 Key Messages to Convey
*   **The Supply Chain Loop**: Forecasting demand is only the first step. To generate value, predictions must be translated into cost-optimal inventory policy parameters that prevent stockouts while minimizing holding costs.
*   **Unified Modeling**: Showcases feature engineering, time-series forecasting, historical day-of-week weight disaggregation, two-stage grid search optimizations, and Monte Carlo validation checks.

### 📊 Recommended Visual Components
1.  **Supply Chain Workflow Diagram**:
    *   *Visual*: A process flowchart showing the flow of data:
        `Raw Transactions` $\rightarrow$ `Exogenous & Cyclical Features` $\rightarrow$ `SARIMAX Pipeline (Part 1)` $\rightarrow$ `Daily Disaggregation weights` $\rightarrow$ `Monte Carlo Demand Path Simulator (Part 2)` $\rightarrow$ `Two-Stage Optimization` $\rightarrow$ `Power BI Dashboard Tables`.
2.  **Top-Line KPI Cards**:
    *   **Demand Forecast Route**: 100% Traditional Model Fallback Route (robustness).
    *   **Optimization Target**: $\ge 95\%$ Service Level ( realized fill rates achieved: $99.16\% - 100.00\%$).
    *   **MC Replications Evaluated**: 10,000 future paths per family.
3.  **Project Executive Summary Text Box**:
    *   Briefly state the goal: Design a forecast-driven inventory replenishment system for high-volume store sales (Favorita Stores, Ecuador) across product categories, establishing optimal safety stock, reorder levels ($s$), and order quantities ($Q$).

---

## Page 2: Part 1 — Demand Forecasting System Performance

### 🎯 Objective
Show feature engineering achievements, traditional vs. machine learning comparisons, and the critical technical pivot during the out-of-sample forecast.

### 💡 Key Messages to Convey
*   **Feature Engineering Depth**: Highlights engineering of the Ecuador Earthquake shockwave factor, cyclical time features (sine/cosine encoding), and holiday register cleanses.
*   **Model Comparison & Dynamic Tuning**: Explains the **Dynamic Boundary-Shifting Tuning Engine** (automatically adjusting parameter grid bounds during grid-search to find global optima) and the hybrid ensemble routing rule.
*   **The Technical Fallback Pivot**: Describes how visual auditing caught corruption in the machine learning models on disk, and how you routed out-of-sample forecasts to winning traditional statistical models (SARIMAX / Seasonal Naive) to ensure forecasting continuity and robustness.
*   **Day-of-Week Disaggregation**: Explains how weekly forecasts were split into daily totals using historical day-of-week sales weights.

### 📊 Recommended Visual Components
1.  **Traditional vs. ML Model Validation Comparison (Table/Matrix)**:
    *   *Columns*: Family, Traditional Model, ML Model, MAPE Improvement (%), Selected Training Route.
    *   *Highlight*: Show how ML models improved validation MAPE on training data (e.g. $+63.8\%$ for Grocery I, $+45.9\%$ for Beverages).
2.  **Visual Continuation Line Chart**:
    *   *Visual*: Plot 2016-2017 historical actual sales alongside the 3-week out-of-sample fitted forecast for GROCERY I and BEVERAGES, showing a smooth transition (proves feasibility audit continuation check).
3.  **Disaggregation Weights Visual (Stacked Bar)**:
    *   *Visual*: Proportions of weekly sales by day-of-week for selected families (shows shopping peaks on weekends).

---

## Page 3: Part 2 — Inventory Optimization & Policy Design

### 🎯 Objective
Justify the inventory replenishment policy selection ($(s,Q)$ vs $(R,S)$) and present the optimal parameters generated.

### 💡 Key Messages to Convey
*   **Replenishment Strategy Rules**:
    *   **Grocery I & Beverages**: High-volume, continuous sales, zero empty weeks $\rightarrow$ continuous review $(s,Q)$ policy to reorder immediately upon reaching threshold.
    *   **Cleaning**: Extremely stable, low demand volatility ($CV \approx 0.177$) $\rightarrow$ periodic review $(R,S)$ policy to minimize monitoring overhead.
*   **Cost Minimization**: Show how classical EOQ was calculated as a starting grid-search heuristic, followed by coarse and fine grid searches.

### 📊 Recommended Visual Components
1.  **Policy Justification Table**:
    *   *Columns*: Product Family, Mean Demand, CV, Demand Frequency, Chosen Replenishment Policy.
2.  **Optimal Inventory Policy Parameters (Table/Matrix)**:
    *   *Columns*: Family, Policy Type, Lead Time, Review Period, Risk Period, Safety Stock ($S_s$), Reorder Point ($s$), Order Quantity ($Q$), Order-Up-To Level ($S$).
3.  **Realized Service Levels vs. Targets (Side-by-Side Bar Chart)**:
    *   *Visual*: Realized fill rate (Grocery I: $99.16\%$, Beverages: $99.66\%$, Cleaning: $100.00\%$) compared to the target $95\%$ line.

---

## Page 4: Part 2 (Cont.) — Simulation & Monte Carlo Validation

### 🎯 Objective
Audit and validate the reliability of optimized parameters using Monte Carlo simulation paths and rolling historical backtests.

### 💡 Key Messages to Convey
*   **Headless Vectorized Simulator**: Showcases your coding execution: running 10,000 replications in parallel using a custom vectorized simulator to process multidimensional arrays up to 100x faster than scalar loops.
*   **Dynamic Rolling Backtests**: Shows how reorder boundaries ($s_t, S_t$) were updated dynamically week-by-week using historical forecasts to prove historical feasibility.
*   **Operational Health Gates**: Explains the pass/fail checks: evaluating fill rates, ensuring orders are placed, and verifying cost stability (Coefficient of Variation) under stochastic demand.

### 📊 Recommended Visual Components
1.  **Monte Carlo Ending Inventory Histogram**:
    *   *Visual*: Frequency distribution of ending inventory levels across the 10,000 replications (proves stockout risks are tightly controlled).
2.  **Validation Status Table (Audit Summary)**:
    *   *Columns*: Family, Validation Passed (True/False), Realized Fill Rate, Average Inventory, Cost Standard Deviation, Cost CV.
3.  **Dynamic Backtest Timeline (Line Chart)**:
    *   *Visual*: Plot historical actual inventory levels along with the dynamic reorder point $s_t$ or order-up-to level $S_t$ over time, proving the buffer tracks forecast trend lines.

---

## Page 5: Strategic Sensitivity Analysis & Trade-off Explorer

### 🎯 Objective
Provide decision support to supply chain executives by demonstrating policy sensitivity to changes in parameters.

### 💡 Key Messages to Convey
*   **Holding Cost Sensitivity**: Higher holding rates (25%) shrink order quantities (reducing capital locked in warehouses) but increase replenishment frequency.
*   **Lead Time Exposure**: If supplier lead time doubles from 1 to 2 weeks, safety stocks must increase substantially (e.g. from 487k to 949k for GROCERY I, and from 588k to 1.06M for BEVERAGES) to absorb risk-period volatility, highlighting the strategic value of supplier lead time reduction.
*   **Uncertainty Model Robustness**: Comparison of bootstrap vs. KDE distributions shows consistent optimal outputs, proving the system is robust.

### 📊 Recommended Visual Components
1.  **Service Target vs. Total Cost Trade-off Curve (Scatter Chart)**:
    *   *Visual*: Total Cost on Y-axis, Service target ($\beta = 90\%, 95\%, 98\%$) on X-axis (shows the non-linear cost increase as service targets approach 100%).
2.  **Lead Time Impact Visual (Clustered Column)**:
    *   *Visual*: Safety Stock levels for $L=1$ vs. $L=2$, showing the significant capital requirements when lead times expand.
3.  **Scenario Parameter Slicer**:
    *   A Power BI slicer allowing the user to select scenarios: *Base Case, Holding Rate 10%, Holding Rate 25%, Order Cost K=10, Order Cost K=50, Lead Time L=2, Residual Bootstrap, Ratio KDE*.
