"""
Main Pipeline Runner for Inventory Optimization System.

Role:
  Main execution script that orchestrates the entire inventory optimization pipeline.
  It loads the configurations and datasets, validates date alignment, runs descriptive
  demand checks, executes the two-stage grid search optimization, performs analytical Gamma
  benchmarking, validates results via Monte Carlo and rolling historical backtests,
  runs cost/service/lead time sensitivity scenarios, and exports all CSV tables and plot figures.

Usage:
  /opt/miniconda3/bin/python main.py
"""

import os
import sys
import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List

# Add current folder to python path for modular imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.config import Config
from src.data_loader import load_train_data, load_test_data, filter_families, validate_weekly_alignment
from src.metrics import calculate_justification_statistics, calculate_total_cost, calculate_average_inventory, calculate_fill_rate
from src.demand_uncertainty import (
    calculate_ratios,
    calculate_residuals,
    check_ratio_bias,
    center_ratios,
    cap_by_percentile
)
from src.distributions import (
    bootstrap_sample,
    kde_sample,
    fit_gamma_moments,
    fit_shifted_gamma,
    solve_gamma_protection_level
)
from src.simulation import InventorySimulator
from src.policies import SQPolicy, RSPolicy
from src.optimization import GridSearchOptimizer, LocalSearchOptimizer
from src.validation import ValidationEngine
from src.sensitivity import SensitivityAnalyzer
import src.reporting as reporting

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Inventory Optimization System Pipeline...")

    # 1. Load Configurations
    config_path = os.path.join(os.path.dirname(__file__), "configs", "inventory_config.yaml")
    config = Config(config_path)
    logger.info(f"Configuration loaded from: {config_path}")

    # Define raw file paths relative to main.py
    train_path = os.path.join(os.path.dirname(__file__), "..", "Demand Forecasting System", "data", "actual_fitted_sales_on_train_final.csv")
    test_path = os.path.join(os.path.dirname(__file__), "..", "Demand Forecasting System", "data", "actual_fitted_sales_on_test_final.csv")

    # 2. Load and validate data
    logger.info("Loading train and test datasets...")
    train_df = load_train_data(train_path, config)
    test_df = load_test_data(test_path, config)
    
    # Filter datasets to keep only selected product families
    train_df = filter_families(train_df, config.selected_families, config)
    test_df = filter_families(test_df, config.selected_families, config)
    
    # Verify Sunday week-ending alignment
    validate_weekly_alignment(train_df, config)
    logger.info("Time series alignment checks passed successfully.")

    # 3. Calculate Policy-Choice Justification Statistics
    logger.info("Calculating policy choice justification statistics...")
    justification_df = calculate_justification_statistics(train_df, config)
    justification_csv_path = os.path.join(os.path.dirname(__file__), "outputs", "tables", "policy_justification_statistics.csv")
    os.makedirs(os.path.dirname(justification_csv_path), exist_ok=True)
    justification_df.to_csv(justification_csv_path, index=False)
    logger.info(f"Justification table saved to: {justification_csv_path}")

    # Extract historical arrays for validation and sensitivity
    col_date = config.columns.get("date", "date")
    col_family = config.columns.get("family", "family")
    col_actual = config.columns.get("train_actual", "Actual_Sales")
    col_fitted = config.columns.get("train_fitted", "Fitted_Sales")
    col_forecast = config.columns.get("test_forecast", "forecast_sales")

    historical_actuals = {}
    historical_forecasts = {}
    test_forecasts = {}
    
    for family in config.selected_families:
        historical_actuals[family] = train_df[train_df[col_family] == family][col_actual].values
        historical_forecasts[family] = train_df[train_df[col_family] == family][col_fitted].values
        test_forecasts[family] = test_df[test_df[col_family] == family][col_forecast].values

    # Pre-generate simulated weekly demand paths for main optimizations
    simulated_weekly_demand = {}
    n_reps = config.n_replications
    rng = np.random.default_rng(config.random_seed)

    logger.info(f"Generating {n_reps} Monte Carlo demand paths for each family...")
    for family in config.selected_families:
        hist_act = historical_actuals[family]
        hist_fit = historical_forecasts[family]
        test_f = test_forecasts[family]
        n_weeks_test = len(test_f)
        
        # Calculate forecast ratios
        ratios = calculate_ratios(hist_act, hist_fit, config.epsilon)
        
        # Center ratios
        mean_ratio = np.mean(ratios)
        ratios_centered = center_ratios(ratios, mean_ratio)
        
        # Cap ratios at p1/p99 to prevent outliers from disrupting metrics
        ratios_capped = cap_by_percentile(ratios_centered, 1.0, 99.0)
        
        # Pre-generate simulation paths (N, W)
        weekly_paths = np.zeros((n_reps, n_weeks_test))
        for i in range(n_reps):
            sampled_r = bootstrap_sample(ratios_capped, size=n_weeks_test, random_state=rng)
            weekly_paths[i, :] = np.maximum(0.0, test_f * sampled_r)
            
        simulated_weekly_demand[family] = weekly_paths

    # 4. Base Case Optimization and Validation per Family
    base_case_rows = []
    mc_validation_summary = []
    backtest_history_dfs = []
    
    # Store standard schema records for Power BI
    pbi_records = []

    logger.info("Running base-case policy optimizations and validations...")
    for family in config.selected_families:
        p_type = config.policies.get(family, "SQ")
        L = config.lead_times.get(family, 1)
        R = config.review_periods.get(family, 1)
        
        H_weekly = config.holding_cost_weekly
        K = config.order_cost
        B = config.shortage_costs.get(family, 15.0)
        
        weekly_paths = simulated_weekly_demand[family]
        test_f = test_forecasts[family]
        
        # Determine risk period length tau
        tau = L if p_type.upper() == "SQ" else (R + L)
        
        # Construct risk period demand
        risk_paths = np.sum(weekly_paths[:, :tau], axis=1)
        mean_risk = float(np.mean(risk_paths))
        std_risk = float(np.std(risk_paths, ddof=1))

        # Create simulator
        simulator = InventorySimulator(
            lead_time=L,
            holding_cost=H_weekly,
            order_cost=K,
            shortage_cost=B,
            backorder=config.backorder
        )
        
        optimizer = GridSearchOptimizer(simulator, target_fill_rate=config.target_fill_rate)
        validator = ValidationEngine(simulator, target_fill_rate=config.target_fill_rate)

        # 4.1 Run Grid Search Optimization
        if p_type.upper() == "SQ":
            q0 = float(np.sqrt((2.0 * K * np.mean(weekly_paths)) / H_weekly))
            q_grid = np.array([0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 1.75, 2.0]) * q0
            ss_grid = np.arange(0, 4.01 * std_risk, 0.25 * std_risk)
            
            # expected lead time demand
            mean_ltd = np.mean(weekly_paths) * L
            
            opt_ss, opt_q, opt_s, opt_metrics = optimizer.optimize_sq(
                demand_paths=weekly_paths,
                ss_grid=ss_grid,
                q_grid=q_grid,
                expected_lead_time_demand=mean_ltd
            )
            
            # Setup SQ Policy object
            policy = SQPolicy(reorder_point=opt_s, order_quantity=opt_q)
            initial_inv = opt_s
            opt_S = np.nan
            
            # Check Local Search comparison
            local_opt = LocalSearchOptimizer(simulator, target_fill_rate=config.target_fill_rate)
            loc_ss, loc_q, loc_s, loc_metrics = local_opt.optimize_sq(
                demand_paths=weekly_paths,
                initial_ss=opt_ss,
                initial_q=opt_q,
                step_ss=0.1 * std_risk,
                step_q=5.0,
                expected_lead_time_demand=mean_ltd
            )
            logger.info(f"{family} [Grid SQ s={opt_s:.2f}, Q={opt_q:.2f}, Cost={opt_metrics['total_cost']:.4f}]")
            logger.info(f"{family} [Local SQ s={loc_s:.2f}, Q={loc_q:.2f}, Cost={loc_metrics['total_cost']:.4f}]")
            
        else:
            # Periodic review RS
            ss_grid = np.arange(0, 4.01 * std_risk, 0.25 * std_risk)
            
            opt_ss, opt_S, opt_metrics = optimizer.optimize_rs(
                demand_paths=weekly_paths,
                ss_grid=ss_grid,
                expected_risk_period_demand=mean_risk
            )
            
            # Setup RS Policy object
            policy = RSPolicy(order_up_to_level=opt_S)
            initial_inv = opt_S
            opt_s = np.nan
            opt_q = np.nan
            
            # Local search comparison
            local_opt = LocalSearchOptimizer(simulator, target_fill_rate=config.target_fill_rate)
            loc_ss, loc_S, loc_metrics = local_opt.optimize_rs(
                demand_paths=weekly_paths,
                initial_ss=opt_ss,
                step_ss=0.1 * std_risk,
                expected_risk_period_demand=mean_risk
            )
            logger.info(f"{family} [Grid RS S={opt_S:.2f}, Cost={opt_metrics['total_cost']:.4f}]")
            logger.info(f"{family} [Local RS S={loc_S:.2f}, Cost={loc_metrics['total_cost']:.4f}]")

        # 4.2 Run Monte Carlo Validation on test path
        val_metrics = validator.monte_carlo_validate(weekly_paths, policy, initial_inv)
        logger.info(f"{family} validation fill rate: {val_metrics['fill_rate']:.4f} (passed: {val_metrics['validation_passed']})")

        # 4.3 Run Analytical Gamma Benchmark
        # Fit Gamma parameters to risk-period demand
        hist_act = historical_actuals[family]
        # Calculate risk period demand over training period for fitting
        hist_risk_demand = []
        for w in range(len(hist_act) - tau + 1):
            hist_risk_demand.append(np.sum(hist_act[w:w+tau]))
        hist_risk_demand = np.array(hist_risk_demand)
        
        # Fit Standard Gamma
        k_g, theta_g = fit_gamma_moments(hist_risk_demand)
        # Solve for protection level
        d_c_val = opt_q if p_type.upper() == "SQ" else np.mean(hist_act)
        try:
            iota_gamma = solve_gamma_protection_level(k_g, theta_g, d_c_val, config.target_fill_rate)
            gamma_ss = iota_gamma - np.mean(hist_risk_demand)
        except Exception:
            gamma_ss = np.nan
            
        # 4.4 Run Historical Rolling Backtest
        # Simulates continuously over training period using actual demand and fitted forecasts
        backtest_res = validator.rolling_backtest(
            historical_actuals=historical_actuals[family],
            historical_forecasts=historical_forecasts[family],
            policy_type=p_type,
            safety_stock=opt_ss,
            order_quantity=opt_q
        )
        logger.info(f"{family} historical backtest realized fill rate: {backtest_res['fill_rate']:.4f}")

        # Plot ending inventory distribution
        ending_plots_path = os.path.join(os.path.dirname(__file__), "outputs", "plots", f"ending_inventory_dist_{family.replace(' ', '_').lower()}.png")
        reporting.plot_ending_inventory_distribution(val_metrics["ending_inventory_distribution"], family, ending_plots_path)

        # Plot distribution fit visual checks
        dist_plots_path = os.path.join(os.path.dirname(__file__), "outputs", "plots", f"distribution_fit_comparison_{family.replace(' ', '_').lower()}.png")
        # generate comparison arrays
        gamma_samples = np.random.gamma(k_g, theta_g, size=5000)
        # KDE
        kde_samples = kde_sample(hist_risk_demand, size=5000, random_state=42)
        reporting.plot_uncertainty_distributions(hist_risk_demand, gamma_samples, kde_samples, family, dist_plots_path)

        # Compile summaries
        base_case_rows.append({
            "family": family,
            "policy_type": "(s,Q)" if p_type.upper() == "SQ" else "(R,S)",
            "safety_stock": opt_ss,
            "reorder_point": opt_s,
            "order_quantity": opt_q,
            "order_up_to_level": opt_S,
            "fill_rate": val_metrics["fill_rate"],
            "cycle_service_level": val_metrics["cycle_service_level"],
            "total_cost": val_metrics["total_cost"],
            "avg_inventory": val_metrics["avg_inventory"],
            "num_orders": val_metrics["num_orders"],
            "units_short": val_metrics["units_short"],
            "gamma_benchmark_safety_stock": gamma_ss
        })

        pbi_records.append({
            "family": family,
            "policy_type": "(s,Q)" if p_type.upper() == "SQ" else "(R,S)",
            "lead_time": L,
            "review_period": R if p_type.upper() == "RS" else np.nan,
            "risk_period": tau,
            "safety_stock": opt_ss,
            "reorder_point": opt_s,
            "order_quantity": opt_q,
            "order_up_to_level": opt_S,
            "fill_rate": val_metrics["fill_rate"],
            "cycle_service_level": val_metrics["cycle_service_level"],
            "total_cost": val_metrics["total_cost"],
            "avg_inventory": val_metrics["avg_inventory"],
            "num_orders": val_metrics["num_orders"],
            "units_short": val_metrics["units_short"]
        })

    # Save final base case results CSV
    base_case_df = pd.DataFrame(base_case_rows)
    opt_csv_path = os.path.join(os.path.dirname(__file__), "outputs", "policy_results", "base_case_optimization_results.csv")
    reporting.export_policy_results(base_case_df, opt_csv_path)

    # 5. Run Sensitivity Analysis Scenarios
    logger.info("Executing Sensitivity Analysis Scenarios...")
    sensitivity_analyzer = SensitivityAnalyzer(
        config=config,
        historical_actuals=historical_actuals,
        historical_forecasts=historical_forecasts,
        test_forecasts=test_forecasts,
        simulated_weekly_demand=simulated_weekly_demand
    )

    cost_sens_df = sensitivity_analyzer.run_cost_sensitivity()
    service_sens_df = sensitivity_analyzer.run_service_level_sensitivity()
    lt_sens_df = sensitivity_analyzer.run_lead_time_sensitivity()
    model_sens_df = sensitivity_analyzer.run_uncertainty_model_sensitivity()

    # Combine sensitivity records
    full_sensitivity_df = pd.concat([cost_sens_df, service_sens_df, lt_sens_df, model_sens_df], ignore_index=True)
    sens_csv_path = os.path.join(os.path.dirname(__file__), "outputs", "sensitivity_results", "sensitivity_summary.csv")
    reporting.export_sensitivity_summary(full_sensitivity_df, sens_csv_path)

    # Plot sensitivity summaries
    for family in config.selected_families:
        sens_plot_path = os.path.join(os.path.dirname(__file__), "outputs", "plots", f"sensitivity_cost_summary_{family.replace(' ', '_').lower()}.png")
        reporting.plot_sensitivity_summary(cost_sens_df, family, sens_plot_path)

    # 6. Save Power BI standardized table
    pbi_csv_path = os.path.join(os.path.dirname(__file__), "outputs", "tables", "powerbi_inventory_policy_table.csv")
    reporting.export_powerbi_table(pbi_records, pbi_csv_path)

    # Save final policy results CSV
    final_policy_csv_path = os.path.join(os.path.dirname(__file__), "outputs", "policy_results", "final_policy_results.csv")
    reporting.export_policy_results(base_case_df, final_policy_csv_path)

    logger.info("Inventory Optimization Pipeline Execution Completed Successfully!")


if __name__ == "__main__":
    main()
