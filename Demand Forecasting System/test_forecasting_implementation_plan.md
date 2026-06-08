# Implementation Plan: Test Set Forecasting

This plan addresses your 3 specific concerns while outlining the precise logic for generating the final daily and weekly test set predictions.

## Addressing Your Concerns

### 1. Forecasting Beyond 4 Weeks (The Test Data Duration)
I ran an analysis on your `final_test_df.csv`. It starts on **2017-08-16** and ends on **2017-08-31**. This is exactly **16 days**, which is roughly **2.3 weeks**! 
Because my Direct ML strategy trained models for 4 whole weeks ($h_1, h_2, h_3, h_4$), my existing models actually cover the *entire* test dataset. I only need the forecasts from $h_1, h_2$, and a portion of $h_3$ to cover all 16 days.

**However, if the test set *was* larger than 4 weeks, here is the best way to handle it:**
You would use a **"Recursive-Direct" hybrid strategy**. After predicting weeks 1-4 using the last known training row, you take those 4 predicted sales values and append them to your historical sales data. You then recalculate the lag features (like `lag_1`, `lag_4`, `rolling_mean_4`) using your own predictions. This gives you a new "simulated current state", which you pass back into your $h_1...h_4$ models to predict weeks 5-8. You repeat this loop infinitely. (For this project, I won't need to do this because the test set is only 16 days).

### Phase 1: Understanding the Feature Generation (The Direct Strategy & Exogenous Variables)
You raised an excellent point about processing `final_test_df.csv`! 
Because there is no `sales` column in the test set, I cannot calculate new lag or rolling features. However, I **must** extract the "future known" exogenous variables (like `onpromotion`, `is_holiday_week`, `avg_oil_price`, `month`, `year`) from the test set because both the Traditional and ML models likely need them.

Therefore, building the feature vector for a future week requires merging two things:
1. **Historical Lags & Rolling Means:** Taken from the *last known row* of the training data (`weekly_features.csv`).
2. **Future Exogenous Variables:** Taken by aggregating the test data (`final_test_df.csv`) for that specific future week.

### Phase 2: Feature Engineering Pipeline
1. **Process the Test Data (`final_test_df.csv`):** 
   I will run your exact aggregation code on the test data, but I will exclude the `sales` aggregation since it doesn't exist.
   * **Date Features:** Aggregate `is_holiday`, `days_since_earthquake`, and `oil_price` to weekly (`freq='W-SUN'`).
   * **Promotion:** Aggregate `onpromotion` by family and week (`sum`).
   * **Time Features:** Generate `total_week_number`, `month`, `quarter`, and `year`.
   * This gives me `weekly_test_df` containing the future exogenous variables for the upcoming ~3 weeks.

2. **Extract the "Current State" Lags:** 
   I will load `data/weekly_features.csv` and filter it to grab the very last chronological week for each family. This gives me my static `lag_1`, `lag_4`, `rolling_mean_4`, etc.

3. **Feature Fusion:** 
   For any given future week I am predicting, I will combine the static lags (from Step 2) with the specific future week's exogenous variables (from Step 1) to form the perfect, complete feature matrix.

### 2. Using `weekly_features.csv`
Understood! I will completely bypass running the aggregation code on `final_train_df.csv` and directly load `data/weekly_features.csv` to grab the "last known feature row" for my ML models.

### 3. Model Loading Logic
I will precisely follow your routing logic to fetch the correct models. 
* If Traditional (MAPE_Better_% <= 0): I will look up the specific family in `models/best_models_per_family.csv`. This will tell me exactly which model algorithm won (e.g., ARIMA vs SARIMAX) so I know which `.pkl` file to load from `models/production_traditional_models/`.
* If ML (MAPE_Better_% > 0): I will simply load the 4 horizon models (`{family}_h1.pkl` through `h4.pkl`) from `models/production_models/`.

---

## Detailed Forecasting Loop

### Phase 1: Preparation
1. Load `results/ml_trad_model_comparison.csv` to determine the routing (ML vs Traditional) for each family based on the strict `> 0` rule.
2. Load `data/weekly_features.csv` and filter it to isolate the very last chronological row for each family. This is my "Current State" feature vector.
3. Load `models/best_models_per_family.csv` to map Traditional model names.

### Phase 2: Generating Forecasts (Family by Family)
I iterate through the top 10 families:

**If Route is Machine Learning:**
1. Isolate the family's static lag features from the final row of `weekly_features.csv`.
2. For Horizon $h$ (Week 1, 2, 3), combine these static lags with the corresponding future week's exogenous features (like `onpromotion`) from `weekly_test_df`.
3. Load `models/production_models/{family}_h1.pkl` $\rightarrow$ Feed it the Week 1 fused features $\rightarrow$ Predict Week 1.
4. Load `models/production_models/{family}_h2.pkl` $\rightarrow$ Feed it the Week 2 fused features $\rightarrow$ Predict Week 2.
5. Load `models/production_models/{family}_h3.pkl` $\rightarrow$ Feed it the Week 3 fused features $\rightarrow$ Predict Week 3.

**If Route is Traditional:**
1. Look up the winning traditional model algorithm for the family in `best_models_per_family.csv`.
2. Load the corresponding `.pkl` object from `models/production_traditional_models/`.
3. Extract the future exogenous variables matrix (`onpromotion`, `oil_price`, etc.) for the next 3 weeks from `weekly_test_df`.
4. Call the statistical `model.forecast(steps=3, exog=future_exog_matrix)` to cover the upcoming 3 weeks.

### Phase 3: Output Generation (Daily & Weekly)
1. **Weekly Output:** I will append all generated forecasts together and save `test_predictions_weekly.csv`.
2. **Daily Output:** 
   * I will calculate historical **day-of-week sales weights** for each family using the training data (e.g., what percentage of weekly BEVERAGES sales occur on a Monday vs Sunday).
   * I map the daily rows in `final_test_df.csv` to my predicted weekly totals.
   * I multiply the weekly forecast by the daily weight to get the final daily sales prediction.
   * Save as `test_predictions_daily.csv`.

---

## Verification Plan
* Ensure that the final dataframe has predictions for all top 10 families across the required future time steps.
* Verify that the chosen model (ML vs Trad) precisely matches the logic defined by the `MAPE_Better_%` threshold.
* Ensure no NaN values exist in the final predictions.
