"""
Sensitivity Analysis Module for Inventory Optimization System.

Role:
  Evaluates policy robustness under varying cost assumptions, service level targets,
  lead times, and uncertainty models. It implements:
  1. Cost sensitivity analysis (holding rate, order cost, shortage cost).
  2. Service level sensitivity analysis (beta = 0.90, 0.95, 0.98).
  3. Lead time sensitivity analysis (L = 1 vs 2, R = 1 vs 2).
  4. Uncertainty model sensitivity analysis (ratio bootstrap vs residual bootstrap vs KDE).
  
  For each scenario, it systematically varies the tested parameter, recalculates
  weekly cost parameters and risk-period demand distributions, reruns the grid search
  optimization, validates the resulting policy parameters, and records all performance metrics.

Inputs:
  - Base configuration.
  - Historical data and test forecasts.
  - Base demand paths and estimators.

Outputs:
  - Detailed Pandas DataFrames containing sensitivity scenario results.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List, Tuple
from src.config import Config
from src.policies import SQPolicy, RSPolicy
from src.simulation import InventorySimulator
from src.optimization import GridSearchOptimizer, calculate_eoq
from src.validation import ValidationEngine
from src.distributions import bootstrap_sample, kde_sample

logger = logging.getLogger(__name__)


class SensitivityAnalyzer:
    """
    Sensitivity Analysis Engine that runs scenario analysis on cost, service,
    lead time, and distribution model variations.
    """

    def __init__(
        self, 
        config: Config, 
        historical_actuals: Dict[str, np.ndarray], 
        historical_forecasts: Dict[str, np.ndarray],
        test_forecasts: Dict[str, np.ndarray],
        simulated_weekly_demand: Dict[str, np.ndarray] # Dict mapping family -> 2D array of weekly simulated demand
    ):
        """
        Initialize the sensitivity analyzer.
        
        Inputs:
            config (Config): Configuration object.
            historical_actuals (Dict[str, np.ndarray]): Historical actual sales per family.
            historical_forecasts (Dict[str, np.ndarray]): Historical fitted forecasts per family.
            test_forecasts (Dict[str, np.ndarray]): Future test forecasts per family.
            simulated_weekly_demand (Dict[str, np.ndarray]): Pre-generated future weekly demand paths (N, W) per family.
        """
        self.config = config
        self.historical_actuals = historical_actuals
        self.historical_forecasts = historical_forecasts
        self.test_forecasts = test_forecasts
        self.simulated_weekly_demand = simulated_weekly_demand

    def _generate_risk_period_demand(
        self, 
        weekly_paths: np.ndarray, 
        lead_time: int, 
        review_period: int, 
        policy_type: str
    ) -> Tuple[np.ndarray, float, float]:
        """
        Construct risk-period demand paths based on lead time and review period.
        
        Outputs:
            Tuple: (risk_period_paths (N,), mean_demand, std_demand)
        """
        n_reps, n_weeks = weekly_paths.shape
        
        # Risk period tau
        if policy_type.upper() == "SQ":
            tau = lead_time
        else:
            tau = review_period + lead_time
            
        risk_paths = np.zeros(n_reps)
        for i in range(n_reps):
            # Sum demand over the risk period starting from the forecast horizon
            # If path is shorter than tau, cap tau at path length
            tau_actual = min(tau, n_weeks)
            risk_paths[i] = np.sum(weekly_paths[i, :tau_actual])
            
        return risk_paths, float(np.mean(risk_paths)), float(np.std(risk_paths, ddof=1))

    def _run_optimization_and_validation(
        self,
        family: str,
        policy_type: str,
        lead_time: int,
        review_period: int,
        holding_cost: float,
        order_cost: float,
        shortage_cost: float,
        target_fill: float,
        weekly_paths: np.ndarray
    ) -> Dict[str, Any]:
        """
        Helper method to run simulation-based optimization and validation for a scenario.
        """
        # Create simulator
        simulator = InventorySimulator(
            lead_time=lead_time,
            holding_cost=holding_cost,
            order_cost=order_cost,
            shortage_cost=shortage_cost,
            backorder=self.config.backorder
        )
        
        # Compute risk-period demand details
        risk_paths, mean_risk, std_risk = self._generate_risk_period_demand(
            weekly_paths, lead_time, review_period, policy_type
        )
        
        # Setup safety stock grid: 0 to 4 sigma in steps of 0.25 sigma
        ss_grid = np.arange(0, 4.01 * std_risk, 0.25 * std_risk)
        
        optimizer = GridSearchOptimizer(simulator, target_fill_rate=target_fill)
        validator = ValidationEngine(simulator, target_fill_rate=target_fill)
        
        if policy_type.upper() == "SQ":
            # Continuous review SQ
            # Calculate EOQ using average demand level
            mean_demand_week = float(np.mean(weekly_paths))
            q0 = calculate_eoq(order_cost, mean_demand_week, holding_cost)
            q_grid = np.array([0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 1.75, 2.0]) * q0
            
            # Lead time demand (L weeks)
            mean_lead_time_demand = mean_demand_week * lead_time
            
            # Optimize SQ
            opt_ss, opt_q, opt_s, opt_metrics = optimizer.optimize_sq(
                demand_paths=weekly_paths,
                ss_grid=ss_grid,
                q_grid=q_grid,
                expected_lead_time_demand=mean_lead_time_demand
            )
            
            # Validate SQ
            policy = SQPolicy(reorder_point=opt_s, order_quantity=opt_q)
            val_metrics = validator.monte_carlo_validate(weekly_paths, policy, opt_s)
            
            return {
                "policy_type": "(s,Q)",
                "safety_stock": opt_ss,
                "reorder_point": opt_s,
                "order_quantity": opt_q,
                "order_up_to_level": np.nan,
                "fill_rate": val_metrics["fill_rate"],
                "cycle_service_level": val_metrics["cycle_service_level"],
                "total_cost": val_metrics["total_cost"],
                "avg_inventory": val_metrics["avg_inventory"],
                "num_orders": val_metrics["num_orders"],
                "units_short": val_metrics["units_short"]
            }
        else:
            # Periodic review RS
            # Optimize RS
            opt_ss, opt_S, opt_metrics = optimizer.optimize_rs(
                demand_paths=weekly_paths,
                ss_grid=ss_grid,
                expected_risk_period_demand=mean_risk
            )
            
            # Validate RS
            policy = RSPolicy(order_up_to_level=opt_S)
            val_metrics = validator.monte_carlo_validate(weekly_paths, policy, opt_S)
            
            return {
                "policy_type": "(R,S)",
                "safety_stock": opt_ss,
                "reorder_point": np.nan,
                "order_quantity": np.nan, # order quantity is variable weekly
                "order_up_to_level": opt_S,
                "fill_rate": val_metrics["fill_rate"],
                "cycle_service_level": val_metrics["cycle_service_level"],
                "total_cost": val_metrics["total_cost"],
                "avg_inventory": val_metrics["avg_inventory"],
                "num_orders": val_metrics["num_orders"],
                "units_short": val_metrics["units_short"]
            }

    def run_cost_sensitivity(self) -> pd.DataFrame:
        """
        Evaluate holding, ordering, and shortage cost variations.
        
        Holding Rate: {0.10, 0.15, 0.25}
        Order Cost K: {10, 25, 50}
        Shortage Cost B: {50% of base, base, 150% of base}
        """
        results = []
        
        # Scenarios defined as combinations
        # We test cost parameters changing one-by-one or in standard groupings
        scenarios = [
            # Base Case
            {"name": "Base Case", "h": self.config.annual_holding_rate, "K": self.config.order_cost, "B_factor": 1.0},
            
            # Holding cost sensitivity
            {"name": "Holding Rate 10%", "h": 0.10, "K": self.config.order_cost, "B_factor": 1.0},
            {"name": "Holding Rate 25%", "h": 0.25, "K": self.config.order_cost, "B_factor": 1.0},
            
            # Ordering cost sensitivity
            {"name": "Order Cost K=10", "h": self.config.annual_holding_rate, "K": 10.0, "B_factor": 1.0},
            {"name": "Order Cost K=50", "h": self.config.annual_holding_rate, "K": 50.0, "B_factor": 1.0},
            
            # Shortage cost sensitivity
            {"name": "Shortage Cost 50%", "h": self.config.annual_holding_rate, "K": self.config.order_cost, "B_factor": 0.5},
            {"name": "Shortage Cost 150%", "h": self.config.annual_holding_rate, "K": self.config.order_cost, "B_factor": 1.5}
        ]

        for family in self.config.selected_families:
            p_type = self.config.policies.get(family, "SQ")
            L = self.config.lead_times.get(family, 1)
            R = self.config.review_periods.get(family, 1)
            base_B = self.config.shortage_costs.get(family, 15.0)
            weekly_paths = self.simulated_weekly_demand[family]

            for sc in scenarios:
                h_weekly = self.config.unit_cost * sc["h"] / 52.0
                B_scenario = base_B * sc["B_factor"]
                
                res_dict = self._run_optimization_and_validation(
                    family=family,
                    policy_type=p_type,
                    lead_time=L,
                    review_period=R,
                    holding_cost=h_weekly,
                    order_cost=sc["K"],
                    shortage_cost=B_scenario,
                    target_fill=self.config.target_fill_rate,
                    weekly_paths=weekly_paths
                )
                
                res_dict.update({
                    "family": family,
                    "scenario": sc["name"],
                    "holding_rate_annual": sc["h"],
                    "order_cost_K": sc["K"],
                    "shortage_cost_B": B_scenario,
                    "target_fill_rate": self.config.target_fill_rate,
                    "lead_time": L,
                    "review_period": R
                })
                results.append(res_dict)

        return pd.DataFrame(results)

    def run_service_level_sensitivity(self) -> pd.DataFrame:
        """
        Evaluate fill-rate target service level variations (beta = 0.90, 0.95, 0.98).
        """
        results = []
        targets = [0.90, 0.95, 0.98]

        for family in self.config.selected_families:
            p_type = self.config.policies.get(family, "SQ")
            L = self.config.lead_times.get(family, 1)
            R = self.config.review_periods.get(family, 1)
            H_weekly = self.config.holding_cost_weekly
            K = self.config.order_cost
            B = self.config.shortage_costs.get(family, 15.0)
            weekly_paths = self.simulated_weekly_demand[family]

            for beta in targets:
                scenario_name = f"Service Target beta={beta:.2f}"
                
                res_dict = self._run_optimization_and_validation(
                    family=family,
                    policy_type=p_type,
                    lead_time=L,
                    review_period=R,
                    holding_cost=H_weekly,
                    order_cost=K,
                    shortage_cost=B,
                    target_fill=beta,
                    weekly_paths=weekly_paths
                )
                
                res_dict.update({
                    "family": family,
                    "scenario": scenario_name,
                    "holding_rate_annual": self.config.annual_holding_rate,
                    "order_cost_K": K,
                    "shortage_cost_B": B,
                    "target_fill_rate": beta,
                    "lead_time": L,
                    "review_period": R
                })
                results.append(res_dict)

        return pd.DataFrame(results)

    def run_lead_time_sensitivity(self) -> pd.DataFrame:
        """
        Evaluate replenishment lead time and review period variations.
        Continuous (SQ): L = 1 vs L = 2
        Periodic (RS): L = 1, R = 1 vs L = 2, R = 1 vs L = 2, R = 2
        """
        results = []

        for family in self.config.selected_families:
            p_type = self.config.policies.get(family, "SQ")
            H_weekly = self.config.holding_cost_weekly
            K = self.config.order_cost
            B = self.config.shortage_costs.get(family, 15.0)
            weekly_paths = self.simulated_weekly_demand[family]

            # Define lead time scenarios based on policy type
            if p_type.upper() == "SQ":
                scenarios = [
                    {"name": "Lead Time L=1", "L": 1, "R": 1},
                    {"name": "Lead Time L=2", "L": 2, "R": 1}
                ]
            else:
                scenarios = [
                    {"name": "Lead Time L=1, R=1", "L": 1, "R": 1},
                    {"name": "Lead Time L=2, R=1", "L": 2, "R": 1},
                    {"name": "Lead Time L=2, R=2", "L": 2, "R": 2}
                ]

            for sc in scenarios:
                res_dict = self._run_optimization_and_validation(
                    family=family,
                    policy_type=p_type,
                    lead_time=sc["L"],
                    review_period=sc["R"],
                    holding_cost=H_weekly,
                    order_cost=K,
                    shortage_cost=B,
                    target_fill=self.config.target_fill_rate,
                    weekly_paths=weekly_paths
                )
                
                res_dict.update({
                    "family": family,
                    "scenario": sc["name"],
                    "holding_rate_annual": self.config.annual_holding_rate,
                    "order_cost_K": K,
                    "shortage_cost_B": B,
                    "target_fill_rate": self.config.target_fill_rate,
                    "lead_time": sc["L"],
                    "review_period": sc["R"]
                })
                results.append(res_dict)

        return pd.DataFrame(results)

    def run_uncertainty_model_sensitivity(self, epsilon: float = 1e-6) -> pd.DataFrame:
        """
        Evaluate different forecast uncertainty models (ratio bootstrap, residual bootstrap, ratio KDE).
        This requires re-generating simulated weekly demand paths under the alternative models.
        """
        results = []
        n_reps = self.config.n_replications
        
        # Load date/family details to retrieve actuals and fitted forecasts
        col_actual = self.config.columns.get("train_actual", "Actual_Sales")
        col_fitted = self.config.columns.get("train_fitted", "Fitted_Sales")
        
        # We test three models:
        uncertainty_models = ["Ratio Bootstrap", "Residual Bootstrap", "Ratio KDE"]

        for family in self.config.selected_families:
            p_type = self.config.policies.get(family, "SQ")
            L = self.config.lead_times.get(family, 1)
            R = self.config.review_periods.get(family, 1)
            H_weekly = self.config.holding_cost_weekly
            K = self.config.order_cost
            B = self.config.shortage_costs.get(family, 15.0)
            
            # Retrieve actual and fitted arrays for the training period
            hist_act = self.historical_actuals[family]
            hist_fit = self.historical_forecasts[family]
            
            # Retrieve the test forecast path (expected demand path)
            test_f = self.test_forecasts[family]
            n_weeks_test = len(test_f)
            
            # Generate forecast ratios and residuals
            ratios = hist_act / np.maximum(hist_fit, epsilon)
            # Center ratios
            mean_ratio = np.mean(ratios)
            ratios_centered = ratios / mean_ratio
            # Cap ratios at p1/p99
            low_r = np.percentile(ratios_centered, 1.0)
            high_r = np.percentile(ratios_centered, 99.0)
            ratios_capped = np.clip(ratios_centered, low_r, high_r)
            
            residuals = hist_act - hist_fit
            # Center residuals
            mean_res = np.mean(residuals)
            residuals_centered = residuals - mean_res
            # Cap residuals
            low_e = np.percentile(residuals_centered, 1.0)
            high_e = np.percentile(residuals_centered, 99.0)
            residuals_capped = np.clip(residuals_centered, low_e, high_e)

            # Seeded generator for replications
            rng = np.random.default_rng(self.config.random_seed)

            for model_name in uncertainty_models:
                # Re-generate demand paths (N, W)
                weekly_paths = np.zeros((n_reps, n_weeks_test))
                
                for i in range(n_reps):
                    if model_name == "Ratio Bootstrap":
                        sampled_r = bootstrap_sample(ratios_capped, size=n_weeks_test, random_state=rng)
                        weekly_paths[i, :] = np.maximum(0.0, test_f * sampled_r)
                    elif model_name == "Residual Bootstrap":
                        sampled_e = bootstrap_sample(residuals_capped, size=n_weeks_test, random_state=rng)
                        weekly_paths[i, :] = np.maximum(0.0, test_f + sampled_e)
                    else: # Ratio KDE
                        sampled_r = kde_sample(ratios_capped, size=n_weeks_test, random_state=rng, handle_negative=True)
                        weekly_paths[i, :] = np.maximum(0.0, test_f * sampled_r)
                
                res_dict = self._run_optimization_and_validation(
                    family=family,
                    policy_type=p_type,
                    lead_time=L,
                    review_period=R,
                    holding_cost=H_weekly,
                    order_cost=K,
                    shortage_cost=B,
                    target_fill=self.config.target_fill_rate,
                    weekly_paths=weekly_paths
                )
                
                res_dict.update({
                    "family": family,
                    "scenario": f"Uncertainty: {model_name}",
                    "holding_rate_annual": self.config.annual_holding_rate,
                    "order_cost_K": K,
                    "shortage_cost_B": B,
                    "target_fill_rate": self.config.target_fill_rate,
                    "lead_time": L,
                    "review_period": R
                })
                results.append(res_dict)

        return pd.DataFrame(results)
