# Store Sales Demand Forecasting System Summary

This document details the end-to-end process developed for predicting store sales at Favorita stores in Ecuador, from initial ingestion and feature engineering to a hybrid forecasting pipeline, dynamic hyperparameter tuning, daily disaggregation, and visual feasibility auditing.

**Demand Forecasting System Workflow**
![Demand Forecasting System Workflow](./Demand%20Forecasting%20System%20Workflow.png)

---

## 📋 Project Directory Structure

All implementation steps are modularly structured across Jupyter notebooks, source files, and result directories within the `projects/Inventory Optimization Modeling/Demand Forecasting System` folder:

```text
projects/Inventory Optimization Modeling/Demand Forecasting System/
├── Demand Forecasting System Summary.md          # This summary report
├── test_forecasting_implementation_plan.md      # Out-of-sample execution plan
├── processing.ipynb                            # Phase 1: Preprocessing & EDA
│
├── data/                                       # Cleaned & Engineered Datasets
│   ├── final_train_df.csv                      # Raw daily aggregated train set
│   ├── final_test_df.csv                       # Raw daily aggregated test set
│   ├── weekly_features.csv                     # Consolidated weekly train features
│   ├── inventory_features.csv                  # Inventory-specific features
│   ├── actual_fitted_sales_on_train_final.csv  # Combined actual & fitted training sales (Inventory System input)
│   ├── actual_fitted_sales_on_test_final.csv   # Out-of-sample weekly test forecasts (Inventory System input)
│   └── segmentation_features.csv               # Segmented store features
│
├── models/                                     # Modeling Phase Assets
│   ├── traditional_model_implementation.ipynb   # Phase 2: Statistical Modeling
│   ├── ml_dl_model_implementation.ipynb        # Phase 3: ML/DL and Tuning
│   ├── best_models_per_family.csv              # Winning traditional models
│   ├── default_ml_dl_model_performance.csv     # Base ML model metrics
│   ├── tuned_ml_dl_model_performance.csv       # Tuned ML model metrics
│   ├── production_models/                      # Saved PyTorch & XGBoost .pkl files
│   └── production_traditional_models/          # Saved SARIMAX & baseline .pkl files
│
└── results/                                    # Evaluation & Final Inference
    ├── final_model.ipynb                       # Phase 4: Hybrid Evaluation
    ├── forecast_on_test_data.ipynb             # Phase 5: Test Set Forecasting
    ├── feasibility_evaluation.ipynb            # Phase 6: Feasibility Auditing
    ├── ml_trad_model_comparison.csv            # Detailed ML vs Trad comparison
    ├── hybrid_fitted_values.csv                # Historical fitted hybrid values
    ├── test_predictions_weekly_edit_3.csv      # Out-of-sample weekly predictions
    ├── test_predictions_daily_edit_3.csv       # Out-of-sample daily predictions
    └── dashboard_plots/                        # Visual plots (ACF, YoY, Decomposition)
        └── MLDL Charts/                        # Specific ML/DL predictions vs actuals
```

---

## 🔄 Phase-by-Phase Process Outline

### 1. Data Ingestion, Cleaning & Feature Engineering (`processing.ipynb`)
The foundation of the project focused on transforming raw transaction, store, oil, and holiday datasets into a highly descriptive time-series dataset.
* **Exogenous Imputation**: Imputed missing oil prices in `oil.csv` by applying forward-fill and linear interpolation to maintain a continuous daily price series.
* **Earthquake Shockwave Factor**: Created a continuous `days_since_earthquake` feature to model the immediate disruption and long-term recovery window following the massive April 16, 2016 Ecuador earthquake.
* **Holiday Cleanup**: Cleansed the complex holiday register, correctly handling transferred holidays, weekend bridges, and national vs. local events.
* **Periodicity & Cyclical Encoding**: Captured seasonal cycles by transforming day of week, day of month, and month using sine and cosine trigonometric functions:

$$\text{Feature}_{\sin} = \sin\left(\frac{2\pi \times \text{value}}{\text{period}}\right), \quad \text{Feature}_{\cos} = \cos\left(\frac{2\pi \times \text{value}}{\text{period}}\right)$$

* **Lag & Rolling Metrics**: Computed historical sales lag features (`lag_1`, `lag_4`, `rolling_mean_4`, etc.) at the family-store level.
* **Aggregation**: Compiled and exported a consolidated weekly dataset (`weekly_features.csv`) and generated initial EDA plots (ACF/PACF, correlations, and distribution metrics).

---

### 2. Statistical Traditional Modeling (`traditional_model_implementation.ipynb`)
Established a strong statistical baseline using classical time-series models customized for each product category.
* **Algorithms Implemented**: Naive, Seasonal Naive, ARIMA, SARIMA, and SARIMAX.
* **Family-Level Granularity**: Fit independent models for each of the top 10 product families to capture category-specific seasonal shapes and exogenous effects.
* **Optimal Model Selection**: Selected optimal configurations based on validation set Mean Absolute Percentage Error (MAPE). 

#### Winning Traditional Models by Family
The optimal traditional configurations identified and exported to `best_models_per_family.csv` are:

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

---

### 3. Machine Learning & Deep Learning Modeling (`ml_dl_model_implementation.ipynb`)
Evaluated non-linear machine learning models capable of capturing multidimensional patterns missed by traditional baselines.
* **Algorithms Implemented**: Decision Trees, Random Forests, XGBoost, PyTorch Dense Neural Networks (BasicNN), and LSTMs.
* **Inference Strategies**:
  * **Recursive Forecasting**: A single model predicting $t+1$, and recursively feeding that prediction back into lag variables for subsequent predictions.
  * **Direct Forecasting**: Training $H$ independent models (where $H=4$ weeks) to forecast each specific future step directly, bypassing recursive error accumulation.
* **Dynamic Boundary-Shifting Tuning Engine**:
  * Formulated a custom tuning engine to optimize model hyperparameters.
  * During grid search, if the best-performing hyperparameter landed on the edge (min/max boundary) of the search space, the engine dynamically shifted the parameter grid bounds in that direction (e.g., expanding tree depth or learning rate lists) and restarted the tuning loop. This automated process guaranteed convergence to a true global optimum.

---

### 4. Hybrid Ensemble & Comparative Analysis (`final_model.ipynb`)
To leverage the stability of traditional models and the precision of machine learning, a hybrid routing framework was constructed at the product-family level.
* **Improvement Metric**: Quantified performance differences using the `MAPE_Better_%` metric:

$$\text{MAPE\_Better\_\%} = \frac{\text{MAPE}_{\text{Trad}} - \text{MAPE}_{\text{ML}}}{\text{MAPE}_{\text{Trad}}} \times 100$$

* **Hybrid Routing Rule**: 
  * If the ML model improved validation set performance by **0% or more** (`MAPE_Better_% >= 0`), the ML model was selected.
  * Otherwise, the family fell back to the traditional statistical model.

> **Important clarification:** The hybrid routing rule was used to identify the best-performing model family on the validation set. It should be interpreted as a validation-stage comparison rule, not an unconditional production-deployment rule. Final out-of-sample forecasting was subject to an additional feasibility and reliability audit before being used as input for inventory optimization.

#### Model Comparison & Final Routing Metrics (`ml_trad_model_comparison.csv`)

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

---

### 5. Out-of-Sample Test Set Forecasting & Core Pivot (`forecast_on_test_data.ipynb`)
Generated forecasts for the **16-day out-of-sample test period** (August 16 to August 31, 2017), corresponding to approximately 3 weekly intervals.

* **Feature Fusion Pipeline**:
  * Since the test set has no future `sales` values, lag and rolling features could not be calculated.
  * I fused the **static historical lags** (extracted from the last known training week in `weekly_features.csv`) with the **future known exogenous features** (promotions, oil prices, holiday counts) from the test set.
* **The Core Deployment Pivot: Traditional Fallback for Reliable Out-of-Sample Forecasting**:
  * **The Core Deployment Pivot**: Although several machine learning models performed better during validation, the final out-of-sample forecasting stage required reliable saved model artifacts and operationally plausible forecast behavior. During test inference, the saved XGBoost model artifacts produced unreliable forecast volumes, indicating that the deployment path was not stable enough for downstream inventory optimization. Therefore, I disabled ML routing for the out-of-sample period and routed all product families to their best traditional statistical models.
  * **Interpretation**: This pivot should not be interpreted as a general rejection of machine learning models. Instead, it was a deployment-risk decision. The validation results showed that ML models could capture useful nonlinear patterns, but the final inventory optimization pipeline required forecasts that were reproducible, stable, and operationally defensible.
* **Daily Disaggregation Engine**:
  * Shopping volumes vary significantly by day of the week. Simply dividing weekly sales by 7 would result in inaccurate daily forecasts.
  * Developed a disaggregation engine:
    1. Calculated historical **day-of-week sales weights** for each family from the training dataset:
       $$\text{Weight}_{\text{family}, \text{dow}} = \frac{\sum \text{Sales}_{\text{family}, \text{dow}}}{\sum \text{Sales}_{\text{family}, \text{all\_days}}}$$
    2. Mapped each daily row in `final_test_df.csv` to its corresponding Sunday week ending date.
    3. Multiplied the predicted weekly total by the historical day-of-week weight to disaggregate the weekly total:
       $$\text{Daily\_Forecast}_{\text{family}, t} = \text{Weekly\_Forecast}_{\text{family}, \text{week}} \times \text{Weight}_{\text{family}, \text{dow}(t)}$$
    4. Saved the final daily predictions to `test_predictions_daily_edit_3.csv`.

---

### 6. Feasibility Audit & Visual Validation (`feasibility_evaluation.ipynb`)
To ensure statistical validity and prevent anomalous predictions, the final forecasts were validated across four distinct analytical frameworks:

1. **Visual Continuation Check**:
   * Plotted history alongside the forecasts to verify a smooth transition without vertical jumps or structural breaks.
2. **Seasonal Decomposition Audit**:
   * Extracted trend and seasonal patterns from the combined timeline (historical actuals + forecasted values) to verify that forecasted trend directions and seasonal cycles align with historical patterns.
3. **YoY (Year-over-Year) Growth Benchmarking**:
   * Benchmarked the August 16–31, 2017 forecasts against actual sales from August 16–31, 2016 to confirm reasonable growth rates.
4. **Exogenous Cause-and-Effect Analysis**:
   * Verified that predicted sales peaks align logically with planned store promotions (`onpromotion`) and oil price trends.
* **Output Plots**: Generated and saved detailed validation plots (such as `combined_decomposition_feasibility_*.png` and `yoy_growth_feasibility_*.png`) for all top product families under the `results/` folder.

> **Interpretation Note on ML Forecast Auditing:** Feasibility audit is not a replacement for statistical validation metrics. It is an operational plausibility check. For nonlinear ML models, decomposition and YoY checks should not be interpreted as requiring the model to follow a linear additive structure. Instead, these checks are used to detect extreme discontinuities, implausible growth, or deployment-risk behavior before forecasts are used in inventory simulation.

---

## 📈 Key Accomplishments & Technical Deliverables
* **Data Processing**: Full feature pipeline generating lag, rolling, cyclical, and holiday-sensitive features.
* **Traditional Modeling**: 9 optimized, family-specific statistical models (SARIMAX and Seasonal Naive) saved as `.pkl` objects in `models/production_traditional_models/`.
* **ML/DL Engineering**: Implemented tree-based and deep learning architectures with a custom **Dynamic Boundary-Shifting Tuning Engine**.
* **Hybrid Framework**: A modular routing matrix to select the best forecasting approach on a family-by-family basis. Although in general, ML models performed better than Tradtitional models on the train dataset, they performed badly on test dataset after checking their feasibility. At the end, the final forecasted sales dataset bases on 100% traditional models.
* **Inference Pipeline**: A fused test-set feature pipeline, an automated fallback for corrupted models, and a **Daily Disaggregation Engine** based on historical day-of-week weights.
* **Quality Assurance**: A multi-framework visual and mathematical auditing notebook producing comprehensive diagnostic charts.
