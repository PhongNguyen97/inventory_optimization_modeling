# Coding Method Recommendation for the Inventory Optimization Workflow

## 1. Purpose of This Document

This document recommends the most appropriate coding method for implementing the inventory optimization workflow. The goal is not only to finish the current inventory optimization project, but also to build a codebase that can be reused in future forecasting, inventory, logistics, and supply chain analytics projects.

The recommended approach is a **hybrid coding architecture**:

> Use **Jupyter notebooks (`.ipynb`)** for exploration, explanation, diagnostics, visualization, and reporting; use **Python modules/classes (`.py`)** for reusable modeling logic.

This structure gives the project both analytical clarity and professional software organization.

---

## 2. Direct Recommendation

For this project, do **not** use only notebooks and do **not** use only Python script files.

Use the following combination:

| Component | Recommended Use | Reason |
|---|---|---|
| `.ipynb` notebooks | Experimentation, explanation, diagnostics, visual checks, and reporting | Easy to inspect intermediate results and explain modeling decisions step by step |
| `.py` files | Reusable functions, classes, simulation engines, optimization logic, validation logic, and sensitivity analysis | Easier to reuse, test, maintain, and apply to future projects |
| `.yaml` or `.json` config files | Store assumptions, parameters, family names, cost values, service targets, and policy choices | Prevents hard-coding and makes the model easier to adapt |
| `.csv` output files | Save final policy results, validation results, sensitivity results, and Power BI-ready tables | Makes the outputs usable for dashboards, reports, and presentations |
| `main.py` or pipeline runner | Run the full workflow end-to-end after the code is stable | Converts the project from exploration into a repeatable workflow |

The best architecture is:

> **Notebook-driven analysis with a reusable Python package underneath.**

---

## 3. Why This Hybrid Method Is Best for My Project

My inventory optimization project is not a small one-time coding task. It includes several major components:

1. Weekly demand preparation.
2. Forecast-ratio and forecast-residual construction.
3. Demand uncertainty simulation.
4. Risk-period demand construction.
5. Inventory policy simulation.
6. Two-stage grid search.
7. Gamma benchmark comparison.
8. Monte Carlo validation.
9. Historical rolling backtest.
10. Sensitivity analysis.
11. Iteration and rerun logic if validation fails.
12. Final reporting and Power BI/PowerPoint preparation.

Because these components are repeated across product families and can be reused in other inventory projects, they should not be written only inside notebooks.

A notebook-only structure would make the project easy to start but difficult to maintain. A pure `.py` structure would make the project reusable but harder to explain while learning and developing. Therefore, the hybrid approach is the most suitable.

---

## 4. Why Not Use Only Jupyter Notebooks?

Jupyter notebooks are useful, especially while learning and developing. They allow me to run code step by step, inspect intermediate tables, plot demand distributions, and explain My reasoning in Markdown cells.

However, notebooks become problematic when the logic becomes large and repetitive.

### 4.1 Problems with Notebook-Only Coding

If the full inventory optimization model is written only in notebooks, several problems may occur:

| Problem | Explanation |
|---|---|
| Difficult to reuse | Code written across notebook cells is harder to apply to another project. |
| Difficult to debug | Variables may depend on hidden execution order. Running cells out of order can create errors. |
| Difficult to test | It is harder to test one function or class independently. |
| Code duplication | The same logic may be copied for multiple product families. |
| Hard to maintain | Large notebooks become long, messy, and difficult to navigate. |
| Hard to scale | Adding new product families, policies, or sensitivity scenarios becomes inefficient. |
| Weak software-engineering signal | For job applications, notebook-only projects may look less production-ready. |

### 4.2 Proper Role of Notebooks

Use notebooks for:

- Data inspection.
- Exploratory analysis.
- Visualizing weekly demand.
- Checking forecast ratios and residuals.
- Comparing uncertainty models.
- Plotting simulated demand.
- Reviewing optimization results.
- Explaining validation outputs.
- Building report-ready tables and figures.

Do **not** use notebooks as the permanent home for:

- Core simulation logic.
- Inventory policy rules.
- Cost functions.
- Grid search algorithms.
- Monte Carlo engines.
- Validation functions.
- Sensitivity loops.

Those should be placed in `.py` files.

---

## 5. Why Use Python Modules and Classes?

Python modules and classes are better for reusable modeling logic. They allow me to separate the project into clean components.

For this project, `.py` files are useful because the same logic must be applied repeatedly to different product families:

- `GROCERY I`
- `BEVERAGES`
- `CLEANING`

The project also uses different policy types:

- Continuous review policy: `(s,Q)`
- Periodic review policy: `(R,S)`

A class-based design makes these policy types easier to represent.

For example:

```python
class SQPolicy:
    def __init__(self, reorder_point, order_quantity):
        self.s = reorder_point
        self.Q = order_quantity


class RSPolicy:
    def __init__(self, order_up_to_level, review_period):
        self.S = order_up_to_level
        self.R = review_period
```

Then a simulation engine can evaluate any policy object instead of rewriting separate simulation code for each family.

---

## 6. Recommended Coding Philosophy

The recommended design is:

> **Functional core + class-based structure.**

This means:

- Use **functions** for mathematical/statistical calculations.
- Use **classes** for major business/modeling objects.

This approach avoids two extremes:

1. Writing everything as loose functions with no structure.
2. Overengineering everything into complex classes.

---

## 7. What Should Be Written as Functions?

Use functions for calculations that take inputs and return outputs.

Recommended function-based components include:

| Function Type | Example Responsibility |
|---|---|
| Forecast-error functions | Calculate ratios and residuals |
| Bias-check functions | Check whether ratios center around 1 or residuals center around 0 |
| Demand simulation functions | Generate simulated weekly demand paths |
| Risk-period functions | Convert weekly demand into risk-period demand |
| Metric functions | Calculate fill rate, CSL, units short, average inventory, and total cost |
| Gamma functions | Estimate gamma parameters and calculate gamma loss |
| Utility functions | Cap ratios, clean data, format outputs, save tables |

Example:

```python
def calculate_fill_rate(total_demand, total_units_short):
    if total_demand <= 0:
        return 1.0
    return 1 - (total_units_short / total_demand)
```

This type of calculation does not need a class. A function is clearer.

---

## 8. What Should Be Written as Classes?

Use classes when the object has state, behavior, or a clear business meaning.

Recommended class-based components include:

| Class | Purpose |
|---|---|
| `SQPolicy` | Represents continuous review `(s,Q)` policy |
| `RSPolicy` | Represents periodic review `(R,S)` policy |
| `InventorySimulator` | Runs weekly inventory simulation under a chosen policy |
| `GridSearchOptimizer` | Searches for the lowest-cost feasible policy |
| `GammaBenchmark` | Runs analytical gamma benchmark calculations |
| `ValidationEngine` | Runs Monte Carlo validation and rolling backtest |
| `SensitivityAnalyzer` | Runs cost, service-level, lead-time, and uncertainty sensitivity scenarios |
| `ReportBuilder` | Exports final results into tables and report-ready files |

Example:

```python
class InventorySimulator:
    def __init__(self, lead_time, holding_cost, order_cost, shortage_cost):
        self.lead_time = lead_time
        self.holding_cost = holding_cost
        self.order_cost = order_cost
        self.shortage_cost = shortage_cost

    def simulate(self, demand_path, policy):
        # Weekly event sequence will be implemented here
        pass
```

This object deserves a class because it has parameters and repeated behavior.

---

## 9. Project Folder Structure

Use the following project structure:

```text
Inventory Optimization System/
│
├── notebooks/
│   ├── 01_data_preparation_check.ipynb
│   ├── 02_uncertainty_modeling.ipynb
│   ├── 03_policy_optimization.ipynb
│   ├── 04_validation_backtesting.ipynb
│   └── 05_sensitivity_analysis_reporting.ipynb
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py
│   ├── demand_uncertainty.py
│   ├── distributions.py
│   ├── policies.py
│   ├── simulation.py
│   ├── optimization.py
│   ├── validation.py
│   ├── sensitivity.py
│   ├── metrics.py
│   └── reporting.py
│
├── configs/
│   └── inventory_config.yaml
│
├── Demand Forecasting System/data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── outputs/
│   ├── tables/
│   ├── plots/
│   ├── policy_results/
│   └── sensitivity_results/
│
├── tests/
│   ├── test_metrics.py
│   ├── test_policies.py
│   ├── test_simulation.py
│   └── test_optimization.py
│
├── main.py
├── requirements.txt
└── README.md
```

This structure is suitable for the current project and can also be reused for future supply chain analytics projects.

---

## 10. Explanation of Each Folder

### 10.1 `notebooks/`

This folder contains analysis notebooks. Each notebook should focus on one major stage.

| Notebook | Purpose |
|---|---|
| `01_data_preparation_check.ipynb` | Confirm data availability, weekly scale, selected families, and input alignment |
| `02_uncertainty_modeling.ipynb` | Analyze ratios, residuals, bias, caps, bootstrap, KDE, and gamma assumptions |
| `03_policy_optimization.ipynb` | Run base-case optimization and inspect results |
| `04_validation_backtesting.ipynb` | Validate optimized policies using Monte Carlo and historical rolling backtest |
| `05_sensitivity_analysis_reporting.ipynb` | Run sensitivity scenarios and prepare final reporting tables/plots |

The notebooks should import from `src/`, for example:

```python
from src.data_loader import load_weekly_data
from src.demand_uncertainty import calculate_ratios, calculate_residuals
from src.simulation import InventorySimulator
from src.optimization import GridSearchOptimizer
```

The notebook should not contain the full permanent logic.

---

### 10.2 `src/`

This folder contains the reusable codebase.

Each file should have a clear responsibility.

| File | Responsibility |
|---|---|
| `config.py` | Default constants and configuration helpers |
| `data_loader.py` | Load and validate input datasets |
| `demand_uncertainty.py` | Forecast ratios, residuals, bias checks, caps, and simulation inputs |
| `distributions.py` | Bootstrap, KDE, gamma, shifted gamma, and distribution diagnostics |
| `policies.py` | Inventory policy classes and policy rules |
| `simulation.py` | Weekly inventory event-sequence simulation |
| `optimization.py` | EOQ initialization, coarse grid search, fine grid search, local search |
| `validation.py` | Monte Carlo validation and historical rolling backtest |
| `sensitivity.py` | Sensitivity scenario execution |
| `metrics.py` | Fill rate, CSL, cost, units short, inventory metrics |
| `reporting.py` | Export final tables, charts, and dashboard-ready outputs |

---

### 10.3 `configs/`

This folder stores model assumptions in a separate file. This is important because assumptions should not be scattered throughout the code.

Example `inventory_config.yaml`:

```yaml
project:
  demand_scale: weekly
  selected_families:
    - GROCERY I
    - BEVERAGES
    - CLEANING

service_level:
  target_fill_rate: 0.95

lead_time:
  base_weeks: 1

review_period:
  cleaning_weeks: 1

costs:
  unit_cost: 1
  annual_holding_rate: 0.15
  order_cost: 25
  shortage_cost:
    GROCERY I: 15
    BEVERAGES: 12
    CLEANING: 15

simulation:
  n_replications: 10000
  random_seed: 42

uncertainty:
  main_method: ratio_bootstrap
  ratio_cap: p1_p99

optimization:
  method: two_stage_grid_search
  safety_stock_max_sigma: 4
```

This allows I to reuse the same code for another project by changing only the configuration file.

---

### 10.4 `outputs/`

This folder stores project results.

Recommended outputs include:

| Output Type | Example File |
|---|---|
| Final policy table | `final_policy_results.csv` |
| Optimization results | `base_case_optimization_results.csv` |
| Validation results | `monte_carlo_validation_results.csv` |
| Rolling backtest results | `rolling_backtest_results.csv` |
| Sensitivity results | `sensitivity_summary.csv` |
| Power BI table | `powerbi_inventory_policy_table.csv` |
| Report charts | `.png` or `.svg` files |

These outputs can later be used in Power BI and PowerPoint.

---

### 10.5 `tests/`

This folder is optional at the beginning, but highly recommended as My project becomes more serious.

Testing is important because inventory simulation can easily contain hidden logic errors. For example, an error in order-arrival timing or inventory position calculation can completely change the fill rate and cost.

Recommended tests:

| Test File | Purpose |
|---|---|
| `test_metrics.py` | Test fill rate, CSL, and cost calculations |
| `test_policies.py` | Test `(s,Q)` and `(R,S)` policy decisions |
| `test_simulation.py` | Test inventory event sequence |
| `test_optimization.py` | Test grid-search feasibility filtering |

Example test idea:

```python
def test_fill_rate_no_shortage():
    total_demand = 100
    total_units_short = 0
    assert calculate_fill_rate(total_demand, total_units_short) == 1.0
```

---

## 11. Notebook Responsibilities

### Notebook 1: `01_data_preparation_check.ipynb`

Purpose:

- Confirm weekly data only.
- Confirm selected families.
- Confirm actual/fitted/forecasted alignment.
- Confirm missing values.
- Confirm cost assumptions.
- Confirm service-level assumptions.

Main outputs:

- Data readiness table.
- Family coverage check.
- Weekly date alignment check.

---

### Notebook 2: `02_uncertainty_modeling.ipynb`

Purpose:

- Calculate forecast ratios.
- Calculate forecast residuals.
- Check ratio bias.
- Check residual bias.
- Compare ratio and residual stability.
- Apply ratio caps if needed.
- Compare bootstrap, KDE, and gamma benchmark assumptions.

Main outputs:

- Ratio/residual diagnostic table.
- Bias check table.
- Upper-tail comparison table.
- Selected uncertainty-model decision.

---

### Notebook 3: `03_policy_optimization.ipynb`

Purpose:

- Generate simulated weekly demand.
- Construct risk-period demand.
- Calculate initial safety stock.
- Calculate EOQ for `(s,Q)` policies.
- Run coarse grid search.
- Run fine grid search.
- Run local search comparison.
- Select lowest-cost feasible policy.

Main outputs:

- Base-case optimization table.
- Candidate policy comparison table.
- Best policy by family.

---

### Notebook 4: `04_validation_backtesting.ipynb`

Purpose:

- Validate optimized policies using Monte Carlo simulation.
- Run historical rolling backtest.
- Compare simulated fill rate, CSL, cost, shortage, inventory, and order pattern.
- Diagnose validation failures.

Main outputs:

- Monte Carlo validation table.
- Rolling backtest table.
- Validation pass/fail decision.

---

### Notebook 5: `05_sensitivity_analysis_reporting.ipynb`

Purpose:

- Run holding cost sensitivity.
- Run ordering cost sensitivity.
- Run shortage cost sensitivity.
- Run fill-rate sensitivity.
- Run lead-time sensitivity.
- Run uncertainty-model sensitivity.
- Prepare final report tables and plots.

Main outputs:

- Sensitivity summary table.
- Final policy recommendation table.
- Power BI-ready output tables.
- Report-ready charts.

---

## 12. Python Module Responsibilities

### 12.1 `data_loader.py`

Responsibilities:

- Load weekly demand data.
- Load fitted forecast data.
- Load test forecast data.
- Filter selected product families.
- Validate required columns.
- Check weekly alignment.

Possible functions:

```python
def load_weekly_actuals(path):
    pass


def load_fitted_forecasts(path):
    pass


def load_test_forecasts(path):
    pass


def filter_families(df, selected_families):
    pass


def validate_weekly_alignment(actual_df, fitted_df):
    pass
```

---

### 12.2 `demand_uncertainty.py`

Responsibilities:

- Calculate forecast ratios.
- Calculate residuals.
- Check bias.
- Cap or winsorize extreme values.
- Generate uncertainty samples.

Possible functions:

```python
def calculate_ratios(actual, forecast, epsilon=1e-6):
    pass


def calculate_residuals(actual, forecast):
    pass


def check_ratio_bias(ratios):
    pass


def check_residual_bias(residuals):
    pass


def cap_by_percentile(values, lower_pct=1, upper_pct=99):
    pass
```

---

### 12.3 `distributions.py`

Responsibilities:

- Empirical bootstrap.
- KDE sampling.
- Gamma parameter estimation.
- Shifted gamma parameter estimation.
- Tail diagnostics.

Possible functions:

```python
def bootstrap_sample(values, size, random_state=None):
    pass


def fit_gamma_moments(values):
    pass


def fit_shifted_gamma(values, shift):
    pass


def calculate_tail_error(empirical_values, fitted_values, percentiles):
    pass
```

---

### 12.4 `policies.py`

Responsibilities:

- Define policy classes.
- Encapsulate policy ordering rules.

Possible classes:

```python
class SQPolicy:
    def __init__(self, reorder_point, order_quantity):
        self.s = reorder_point
        self.Q = order_quantity

    def order_quantity(self, inventory_position):
        if inventory_position <= self.s:
            return self.Q
        return 0


class RSPolicy:
    def __init__(self, order_up_to_level):
        self.S = order_up_to_level

    def order_quantity(self, inventory_position):
        return max(0, self.S - inventory_position)
```

---

### 12.5 `simulation.py`

Responsibilities:

- Simulate weekly inventory movement.
- Apply event sequence consistently.
- Track on-hand inventory.
- Track on-order inventory.
- Track orders.
- Track lost sales.
- Track cost.

The event sequence must be fixed:

1. Receive orders.
2. Observe demand.
3. Satisfy demand from on-hand inventory.
4. Record lost sales.
5. Update on-hand inventory.
6. Compute inventory position.
7. Apply policy rule.
8. Place order if needed.
9. Schedule order arrival after lead time.

Possible class:

```python
class InventorySimulator:
    def __init__(self, lead_time, holding_cost, order_cost, shortage_cost):
        self.lead_time = lead_time
        self.holding_cost = holding_cost
        self.order_cost = order_cost
        self.shortage_cost = shortage_cost

    def simulate(self, demand_path, policy, initial_inventory):
        pass
```

---

### 12.6 `metrics.py`

Responsibilities:

- Calculate service metrics.
- Calculate cost metrics.
- Calculate inventory metrics.

Possible functions:

```python
def calculate_fill_rate(total_demand, total_units_short):
    pass


def calculate_cycle_service_level(stockout_flags):
    pass


def calculate_total_cost(holding_cost, avg_inventory, order_cost, num_orders, shortage_cost, units_short):
    pass


def calculate_average_inventory(on_hand_history):
    pass
```

---

### 12.7 `optimization.py`

Responsibilities:

- Calculate EOQ.
- Generate coarse grid.
- Generate fine grid.
- Evaluate candidate policies.
- Reject infeasible candidates.
- Select lowest-cost feasible policy.

Possible classes/functions:

```python
def calculate_eoq(order_cost, weekly_demand, holding_cost):
    pass


class GridSearchOptimizer:
    def __init__(self, simulator, target_fill_rate):
        self.simulator = simulator
        self.target_fill_rate = target_fill_rate

    def optimize_sq_policy(self, demand_paths, ss_grid, q_grid):
        pass

    def optimize_rs_policy(self, demand_paths, ss_grid):
        pass
```

---

### 12.8 `validation.py`

Responsibilities:

- Monte Carlo validation.
- Historical rolling backtesting.
- Validation pass/fail logic.
- Failure diagnostics.

Possible class:

```python
class ValidationEngine:
    def __init__(self, simulator, target_fill_rate):
        self.simulator = simulator
        self.target_fill_rate = target_fill_rate

    def monte_carlo_validate(self, demand_paths, policy):
        pass

    def rolling_backtest(self, historical_data, policy):
        pass
```

---

### 12.9 `sensitivity.py`

Responsibilities:

- Create sensitivity scenarios.
- Rerun optimization under changed assumptions.
- Compare policy stability.

Possible class:

```python
class SensitivityAnalyzer:
    def __init__(self, base_config, optimizer, validator):
        self.base_config = base_config
        self.optimizer = optimizer
        self.validator = validator

    def run_cost_sensitivity(self):
        pass

    def run_service_level_sensitivity(self):
        pass

    def run_uncertainty_model_sensitivity(self):
        pass
```

---

### 12.10 `reporting.py`

Responsibilities:

- Save results.
- Format final tables.
- Export Power BI-ready CSV files.
- Create report-ready figures.

Possible functions:

```python
def export_policy_results(results, path):
    pass


def export_sensitivity_summary(results, path):
    pass


def create_policy_comparison_table(results):
    pass
```

---

## 13. Development Sequence

Use the following sequence while coding.

### Step 1: Start with a notebook, but do not keep everything there

Begin in `01_data_preparation_check.ipynb` and `02_uncertainty_modeling.ipynb` because I need to inspect the data carefully.

At this stage, code can be rough.

---

### Step 2: Convert repeated notebook logic into functions

Once a calculation is used more than once, move it into `src/`.

For example, if I calculate forecast ratios in multiple places, create:

```python
def calculate_ratios(actual, forecast, epsilon=1e-6):
    return actual / np.maximum(forecast, epsilon)
```

Then import it into the notebook.

---

### Step 3: Build policy classes

Create `SQPolicy` and `RSPolicy` before building the simulation engine. This makes the simulator more flexible.

---

### Step 4: Build the simulation engine

The simulation engine is the core of the project. It must follow the weekly event sequence exactly.

Do not optimize before the simulation logic is correct.

---

### Step 5: Test the simulation with simple artificial examples

Before using real demand data, test the simulator with simple cases.

Example:

- Constant weekly demand = 100.
- Lead time = 1.
- Reorder point = 100.
- Order quantity = 100.

Check whether inventory arrivals, shortages, and order timing behave correctly.

This step is very important because inventory simulation errors are often hidden.

---

### Step 6: Implement optimization

After the simulator works, implement:

1. EOQ initialization.
2. Coarse grid search.
3. Fine grid search.
4. Feasibility filtering using fill rate.
5. Lowest-cost feasible selection.

---

### Step 7: Implement validation

After optimization, run:

1. Monte Carlo validation.
2. Historical rolling backtest.
3. Validation failure diagnostics.

---

### Step 8: Implement sensitivity analysis

After the base-case model works, add sensitivity scenarios.

Sensitivity analysis should come after the main simulation and optimization are stable.

---

### Step 9: Create final reporting outputs

Export the final tables for:

- Power BI.
- PowerPoint.
- Markdown report.
- Resume/project portfolio evidence.

---

### Step 10: Create `main.py`

Once all pieces are stable, create a pipeline runner.

Example:

```python
def main():
    # 1. Load config
    # 2. Load data
    # 3. Build uncertainty model
    # 4. Simulate demand
    # 5. Optimize policies
    # 6. Validate policies
    # 7. Run sensitivity analysis
    # 8. Export results
    pass


if __name__ == "__main__":
    main()
```

This allows the full project to be rerun with one command.

---

## 14. How to Make the Code Reusable for Other Projects

To make the code reusable, avoid project-specific hard-coding.

### 14.1 Avoid Hard-Coding Product Families

Do not write logic like this throughout the code:

```python
if family == "GROCERY I":
    # specific logic
```

Instead, define family policies in a configuration file:

```yaml
policies:
  GROCERY I: SQ
  BEVERAGES: SQ
  CLEANING: RS
```

Then My code can read the policy type dynamically.

---

### 14.2 Avoid Hard-Coding Cost Parameters

Do not write this repeatedly:

```python
shortage_cost = 15
```

Instead, store cost values in config:

```yaml
shortage_cost:
  GROCERY I: 15
  BEVERAGES: 12
  CLEANING: 15
```

This allows another project to use different values without changing the code.

---

### 14.3 Keep Data Column Names Configurable When Possible

Different projects may use different column names.

For example, one dataset may use:

- `family`
- `date`
- `sales`

Another may use:

- `product_category`
- `week`
- `demand`

A reusable project can handle this through config mapping:

```yaml
columns:
  family: family
  date: date
  demand: sales
  forecast: forecast
```

---

### 14.4 Separate Business Logic from Data Loading

The simulator should not care where the data came from. It should only receive a demand path and a policy.

Good design:

```python
simulator.simulate(demand_path, policy, initial_inventory)
```

Bad design:

```python
simulator.simulate_from_csv("abcdef.csv")
```

The second design is less reusable because the simulator becomes tied to one project file.

---

### 14.5 Keep Outputs Standardized

For any project, final outputs should follow a consistent schema:

| Column | Meaning |
|---|---|
| `family` | Product family or SKU group |
| `policy_type` | `(s,Q)` or `(R,S)` |
| `lead_time` | Lead time used |
| `review_period` | Review period if applicable |
| `risk_period` | Protection interval |
| `safety_stock` | Optimized safety stock |
| `reorder_point` | `s` for `(s,Q)` |
| `order_quantity` | `Q` for `(s,Q)` |
| `order_up_to_level` | `S` for `(R,S)` |
| `fill_rate` | Realized or simulated fill rate |
| `cycle_service_level` | CSL |
| `total_cost` | Simulated total cost |
| `avg_inventory` | Average on-hand inventory |
| `num_orders` | Number of orders |
| `units_short` | Total shortage/lost sales |

This makes reporting and Power BI easier.

---

## 15. Recommended Implementation Order by File

The coding order should be:

| Order | File | Why This Comes First/Next |
|---:|---|---|
| 1 | `config.py` or `inventory_config.yaml` | Define assumptions before coding logic |
| 2 | `data_loader.py` | Load and validate required data |
| 3 | `metrics.py` | Basic calculations are needed everywhere |
| 4 | `demand_uncertainty.py` | Build uncertainty model before simulation |
| 5 | `distributions.py` | Add bootstrap, KDE, and gamma benchmark tools |
| 6 | `policies.py` | Define `(s,Q)` and `(R,S)` rules |
| 7 | `simulation.py` | Build the weekly inventory engine |
| 8 | `optimization.py` | Optimize only after simulation works |
| 9 | `validation.py` | Validate optimized policies |
| 10 | `sensitivity.py` | Test robustness after base model works |
| 11 | `reporting.py` | Export final results |
| 12 | `main.py` | Run everything end-to-end |

---

## 16. Recommended Practical Coding Rule

Use this rule while developing:

> If code is exploratory, keep it in a notebook. If code is used more than once, move it to a `.py` file. If code controls model assumptions, put it in a config file.

This rule prevents messy notebooks and keeps the project reusable.

---

## 17. Professional Value of This Structure

This coding architecture will make My project stronger for job applications because it demonstrates more than basic data analysis.

It shows that I can:

1. Design a reusable analytical pipeline.
2. Separate experimentation from production logic.
3. Build modular Python code.
4. Implement simulation-based decision models.
5. Validate model outputs instead of only producing calculations.
6. Run sensitivity analysis for assumed parameters.
7. Prepare outputs for business reporting tools such as Power BI and PowerPoint.

For a senior inventory analyst or supply chain analyst audience, this is important because they care about whether the model is reliable, explainable, and operationally useful.

---

## 18. Final Recommendation

The recommended coding method is:

```text
.ipynb notebooks = analysis, learning, diagnostics, explanation, visualization, reporting
.py modules       = reusable modeling engine, simulation, optimization, validation, sensitivity
.yaml config      = assumptions, parameters, families, policies, costs, service targets
.csv outputs      = final tables for reporting, Power BI, and PowerPoint
main.py           = end-to-end workflow execution
```

The final architecture should be:

> **A reusable Python inventory optimization engine controlled and explained through notebooks.**

This is the most appropriate structure because it supports My current project and also allows the same codebase to be reused for other datasets, other product families, different lead times, different service levels, different inventory policies, and future supply chain analytics projects.

