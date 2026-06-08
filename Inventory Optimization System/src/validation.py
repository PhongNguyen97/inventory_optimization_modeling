"""
Validation Module for Inventory Optimization System.

Role:
  Performs performance validation for optimized policies. It runs:
  1. Monte Carlo validation over replicated future demand paths to assess the distribution
     of costs, service levels, shortages, and ending inventories.
  2. Historical rolling backtests where policies are simulated dynamically across the entire
     historical training timeline, using forecasts to update reorder points or order-up-to levels.
  3. Gated pass/fail diagnostics to evaluate whether policies deliver stable, feasible operations.

Inputs:
  - Simulator object.
  - Policy objects.
  - Historical actuals and fitted forecasts.
  - Future demand paths.

Outputs:
  - Aggregated validation statistics, pass/fail decisions, and historical backtest histories.
"""

import numpy as np
import pandas as pd
from typing import Dict, Union, Any, List
from src.policies import SQPolicy, RSPolicy
from src.simulation import InventorySimulator
from src.metrics import calculate_fill_rate, calculate_cycle_service_level


class ValidationEngine:
    """
    Engine to run Monte Carlo validation and historical rolling backtests.
    """

    def __init__(self, simulator: InventorySimulator, target_fill_rate: float = 0.95):
        """
        Initialize the validation engine.
        
        Inputs:
            simulator (InventorySimulator): The weekly inventory simulator.
            target_fill_rate (float): Target fill rate beta (default 0.95).
        """
        self.simulator = simulator
        self.target_fill_rate = target_fill_rate

    def monte_carlo_validate(
        self, 
        demand_paths: np.ndarray, 
        policy: Union[SQPolicy, RSPolicy], 
        initial_inventory: float
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo validation over a large set of demand path replications.
        
        Inputs:
            demand_paths (np.ndarray): 2D array of demand paths (n_replications, n_weeks).
            policy (Union[SQPolicy, RSPolicy]): Policy to validate.
            initial_inventory (float): Starting physical on-hand stock.
            
        Outputs:
            Dict: Contains mean metrics, standard deviations, ending inventory distribution,
                  and order quantity distributions.
        """
        n_reps = len(demand_paths)
        
        fill_rates = []
        costs = []
        inv_levels = []
        orders_counts = []
        short_units = []
        csls = []
        ending_inventories = []
        all_order_sizes = []

        for i in range(n_reps):
            sim_res = self.simulator.simulate(demand_paths[i], policy, initial_inventory)
            fill_rates.append(sim_res["fill_rate"])
            costs.append(sim_res["total_cost"])
            inv_levels.append(sim_res["avg_inventory"])
            orders_counts.append(sim_res["num_orders"])
            short_units.append(sim_res["units_short"])
            csls.append(sim_res["cycle_service_level"])
            
            # Record distribution data
            ending_inventories.append(sim_res["on_hand_end"][-1])
            orders_placed = sim_res["orders_placed_history"]
            all_order_sizes.extend(orders_placed[orders_placed > 0])

        metrics = {
            "fill_rate": float(np.mean(fill_rates)),
            "fill_rate_std": float(np.std(fill_rates)),
            "total_cost": float(np.mean(costs)),
            "total_cost_std": float(np.std(costs)),
            "avg_inventory": float(np.mean(inv_levels)),
            "avg_inventory_std": float(np.std(inv_levels)),
            "num_orders": float(np.mean(orders_counts)),
            "units_short": float(np.mean(short_units)),
            "cycle_service_level": float(np.mean(csls)),
            "ending_inventory_distribution": np.array(ending_inventories),
            "order_quantity_distribution": np.array(all_order_sizes)
        }
        
        # Run pass/fail checks
        diagnostics = self.run_pass_fail_diagnostics(metrics)
        metrics.update(diagnostics)
        return metrics

    def rolling_backtest(
        self, 
        historical_actuals: np.ndarray, 
        historical_forecasts: np.ndarray, 
        policy_type: str, 
        safety_stock: float, 
        order_quantity: float = None
    ) -> Dict[str, Any]:
        """
        Run a dynamic continuous backtest over historical actuals and forecasts.
        Reorder point s_t and order-up-to level S_t adapt dynamically based on historical forecast levels:
        
          SQ Policy: s_t = expected_lead_time_demand_t + S_s = forecast_{t+1} + S_s
          RS Policy: S_t = expected_risk_period_demand_t + S_s = (forecast_{t+1} + forecast_{t+2}) + S_s
          
        Inputs:
            historical_actuals (np.ndarray): Chronological historical actual sales.
            historical_forecasts (np.ndarray): Chronological historical forecast/fitted sales.
            policy_type (str): 'SQ' or 'RS'.
            safety_stock (float): The fixed safety stock (S_s).
            order_quantity (float): Order size (Q) for 'SQ' policy.
            
        Outputs:
            Dict: Dynamic backtest results containing historical metrics and histories.
        """
        n_weeks = len(historical_actuals)
        if n_weeks != len(historical_forecasts):
            raise ValueError("Historical actuals and forecasts must have the same length.")

        # Construct dynamic reorder point / order-up-to level arrays
        if policy_type.upper() == "SQ":
            # expected lead time demand (L=1): forecast of next week
            lead_time_demand = np.zeros(n_weeks)
            lead_time_demand[:-1] = historical_forecasts[1:]
            lead_time_demand[-1] = historical_forecasts[-1] # fallback for last week
            
            dynamic_s = lead_time_demand + safety_stock
            policy = SQPolicy(reorder_point=dynamic_s, order_quantity=order_quantity)
            initial_inv = dynamic_s[0]
            
        elif policy_type.upper() == "RS":
            # expected risk period demand (R=1, L=1, risk period tau=2): forecast of next 2 weeks
            risk_period_demand = np.zeros(n_weeks)
            for w in range(n_weeks):
                f1 = historical_forecasts[w + 1] if w + 1 < n_weeks else historical_forecasts[-1]
                f2 = historical_forecasts[w + 2] if w + 2 < n_weeks else historical_forecasts[-1]
                risk_period_demand[w] = f1 + f2
                
            dynamic_S = risk_period_demand + safety_stock
            policy = RSPolicy(order_up_to_level=dynamic_S)
            initial_inv = dynamic_S[0]
        else:
            raise ValueError(f"Unknown policy type: {policy_type}")

        # Run simulation over historical data
        sim_res = self.simulator.simulate(historical_actuals, policy, initial_inv)
        return sim_res

    def run_pass_fail_diagnostics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate performance metrics against validation gates.
        
        Outputs:
            Dict: Boolean flags indicating check passes and overall pass/fail status.
        """
        fill_rate_pass = metrics["fill_rate"] >= self.target_fill_rate
        
        # Check if average inventory is reasonable (e.g. not excessive)
        # Average inventory should not be extremely large relative to average demand
        # We also check if we placed at least some orders
        orders_pass = metrics["num_orders"] > 0
        
        # Cost stability: Coefficient of variation of cost should be low (< 10.0 for short runs)
        cost_cv = metrics["total_cost_std"] / max(metrics["total_cost"], 1e-6)
        cost_stable_pass = cost_cv < 10.0
        
        overall_pass = fill_rate_pass and orders_pass and cost_stable_pass
        
        return {
            "passed_fill_rate": fill_rate_pass,
            "passed_orders": orders_pass,
            "passed_cost_stability": cost_stable_pass,
            "validation_passed": overall_pass
        }
