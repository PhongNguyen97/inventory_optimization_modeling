"""
Optimization Module for Inventory Optimization System.

Role:
  Performs search to find the cost-optimal inventory policy parameters that
  satisfy the service level constraint (fill rate >= 0.95). It implements:
  1. Economic Order Quantity (EOQ) calculation.
  2. Coarse grid search (evaluating safety stock and order quantity combinations).
  3. Fine grid search (refining around the best candidate).
  4. Local search (neighborhood search as an alternative/exploratory optimizer).
  
Inputs:
  - Simulator object.
  - Demand paths (representing Monte Carlo replications of future demand).
  - Configuration settings for costs, standard deviations, and targets.

Outputs:
  - Optimized policy parameters (s, Q, S) and their simulated performance metrics.
"""

import numpy as np
import logging
from typing import Dict, Tuple, List, Union, Any
from src.policies import SQPolicy, RSPolicy
from src.simulation import InventorySimulator

# Set up logging for diagnostic feedback during optimization runs
logger = logging.getLogger(__name__)


def calculate_eoq(order_cost: float, weekly_demand: float, holding_cost: float) -> float:
    """
    Calculate the classical Economic Order Quantity (EOQ) as an initialization heuristic.
    Formula: Q0 = sqrt((2 * K * D_week) / H_week)
    
    Inputs:
        order_cost (float): Fixed transaction cost per order (K).
        weekly_demand (float): Expected weekly demand (E[D_w]).
        holding_cost (float): Weekly unit holding cost (H_week).
        
    Outputs:
        float: Initial order quantity Q0.
    """
    if holding_cost <= 0:
        return 0.0
    return float(np.sqrt((2.0 * order_cost * weekly_demand) / holding_cost))


class GridSearchOptimizer:
    """
    Two-Stage Grid Search Optimizer for SQ and RS inventory policies.
    """

    def __init__(self, simulator: InventorySimulator, target_fill_rate: float = 0.95):
        """
        Initialize the grid search optimizer.
        
        Inputs:
            simulator (InventorySimulator): The inventory simulator.
            target_fill_rate (float): Target fill rate beta (default 0.95).
        """
        self.simulator = simulator
        self.target_fill_rate = target_fill_rate

    def _evaluate_candidate(
        self, 
        demand_paths: np.ndarray, 
        policy: Union[SQPolicy, RSPolicy],
        initial_inv: float
    ) -> Dict[str, float]:
        """
        Evaluate a candidate policy across multiple demand paths and return average metrics.
        
        Inputs:
            demand_paths (np.ndarray): 2D array of demand paths (n_replications, n_weeks).
            policy (Union[SQPolicy, RSPolicy]): Policy object to evaluate.
            initial_inv (float): Initial on-hand inventory.
            
        Outputs:
            Dict: Aggregated average metrics.
        """
        # Delegate to simulator. If demand_paths is 2D, it runs the vectorized execution in parallel.
        return self.simulator.simulate(demand_paths, policy, initial_inv)

    def optimize_sq(
        self, 
        demand_paths: np.ndarray, 
        ss_grid: np.ndarray, 
        q_grid: np.ndarray, 
        expected_lead_time_demand: float
    ) -> Tuple[float, float, float, Dict[str, float]]:
        """
        Optimize continuous review (s, Q) policy using two-stage grid search.
        
        Inputs:
            demand_paths (np.ndarray): 2D array of demand paths.
            ss_grid (np.ndarray): Safety stock grid candidates.
            q_grid (np.ndarray): Order quantity grid candidates.
            expected_lead_time_demand (float): Expected demand over lead time.
            
        Outputs:
            Tuple: (best_safety_stock, best_order_quantity, best_reorder_point, best_metrics_dict)
        """
        best_cost = float("inf")
        best_ss = None
        best_q = None
        best_metrics = {}

        # Stage 1: Coarse Grid Search
        for ss in ss_grid:
            s = expected_lead_time_demand + ss
            for q in q_grid:
                policy = SQPolicy(reorder_point=s, order_quantity=q)
                
                # Match target initialization: start at s
                initial_inv = s
                
                metrics = self._evaluate_candidate(demand_paths, policy, initial_inv)
                
                # Feasibility Filter: realized average fill rate must satisfy target
                if metrics["fill_rate"] >= self.target_fill_rate:
                    if metrics["total_cost"] < best_cost:
                        best_cost = metrics["total_cost"]
                        best_ss = ss
                        best_q = q
                        best_metrics = metrics

        # If no coarse candidate was feasible, select the one with highest fill rate to prevent crash
        if best_ss is None:
            logger.warning("No feasible coarse SQ policy candidate found. Selecting highest fill rate candidate.")
            highest_fill = -1.0
            for ss in ss_grid:
                s = expected_lead_time_demand + ss
                for q in q_grid:
                    policy = SQPolicy(reorder_point=s, order_quantity=q)
                    metrics = self._evaluate_candidate(demand_paths, policy, s)
                    if metrics["fill_rate"] > highest_fill:
                        highest_fill = metrics["fill_rate"]
                        best_ss = ss
                        best_q = q
                        best_metrics = metrics
            best_cost = best_metrics["total_cost"]

        # Stage 2: Fine Grid Search around best coarse candidate
        ss_step = ss_grid[1] - ss_grid[0] if len(ss_grid) > 1 else 0.5
        q_step = q_grid[1] - q_grid[0] if len(q_grid) > 1 else 5.0
        
        fine_ss_grid = np.linspace(best_ss - 0.5 * ss_step, best_ss + 0.5 * ss_step, 5)
        # Prevent negative safety stock
        fine_ss_grid = np.maximum(fine_ss_grid, 0.0)
        
        fine_q_grid = np.linspace(best_q - 0.5 * q_step, best_q + 0.5 * q_step, 5)
        # Prevent zero or negative order quantities
        fine_q_grid = np.maximum(fine_q_grid, 1.0)

        for ss in fine_ss_grid:
            s = expected_lead_time_demand + ss
            for q in fine_q_grid:
                policy = SQPolicy(reorder_point=s, order_quantity=q)
                initial_inv = s
                metrics = self._evaluate_candidate(demand_paths, policy, initial_inv)
                
                if metrics["fill_rate"] >= self.target_fill_rate:
                    if metrics["total_cost"] < best_cost:
                        best_cost = metrics["total_cost"]
                        best_ss = ss
                        best_q = q
                        best_metrics = metrics

        best_s = expected_lead_time_demand + best_ss
        return float(best_ss), float(best_q), float(best_s), best_metrics

    def optimize_rs(
        self, 
        demand_paths: np.ndarray, 
        ss_grid: np.ndarray, 
        expected_risk_period_demand: float
    ) -> Tuple[float, float, Dict[str, float]]:
        """
        Optimize periodic review (R, S) policy using two-stage grid search.
        
        Inputs:
            demand_paths (np.ndarray): 2D array of demand paths.
            ss_grid (np.ndarray): Safety stock grid candidates.
            expected_risk_period_demand (float): Expected demand over review + lead time.
            
        Outputs:
            Tuple: (best_safety_stock, best_order_up_to, best_metrics_dict)
        """
        best_cost = float("inf")
        best_ss = None
        best_metrics = {}

        # Stage 1: Coarse Grid Search
        for ss in ss_grid:
            S = expected_risk_period_demand + ss
            policy = RSPolicy(order_up_to_level=S)
            
            # Match target initialization: start at S
            initial_inv = S
            
            metrics = self._evaluate_candidate(demand_paths, policy, initial_inv)
            
            # Feasibility Filter
            if metrics["fill_rate"] >= self.target_fill_rate:
                if metrics["total_cost"] < best_cost:
                    best_cost = metrics["total_cost"]
                    best_ss = ss
                    best_metrics = metrics

        # Fallback if no candidate is feasible
        if best_ss is None:
            logger.warning("No feasible coarse RS policy candidate found. Selecting highest fill rate candidate.")
            highest_fill = -1.0
            for ss in ss_grid:
                S = expected_risk_period_demand + ss
                policy = RSPolicy(order_up_to_level=S)
                metrics = self._evaluate_candidate(demand_paths, policy, S)
                if metrics["fill_rate"] > highest_fill:
                    highest_fill = metrics["fill_rate"]
                    best_ss = ss
                    best_metrics = metrics
            best_cost = best_metrics["total_cost"]

        # Stage 2: Fine Grid Search around best coarse candidate
        ss_step = ss_grid[1] - ss_grid[0] if len(ss_grid) > 1 else 0.5
        fine_ss_grid = np.linspace(best_ss - 0.5 * ss_step, best_ss + 0.5 * ss_step, 5)
        fine_ss_grid = np.maximum(fine_ss_grid, 0.0)

        for ss in fine_ss_grid:
            S = expected_risk_period_demand + ss
            policy = RSPolicy(order_up_to_level=S)
            initial_inv = S
            metrics = self._evaluate_candidate(demand_paths, policy, initial_inv)
            
            if metrics["fill_rate"] >= self.target_fill_rate:
                if metrics["total_cost"] < best_cost:
                    best_cost = metrics["total_cost"]
                    best_ss = ss
                    best_metrics = metrics

        best_S = expected_risk_period_demand + best_ss
        return float(best_ss), float(best_S), best_metrics


class LocalSearchOptimizer:
    """
    Local Search Optimizer evaluating neighborhood updates for comparison.
    """

    def __init__(self, simulator: InventorySimulator, target_fill_rate: float = 0.95):
        """
        Initialize local search optimizer.
        """
        self.simulator = simulator
        self.target_fill_rate = target_fill_rate
        self._grid_evaluator = GridSearchOptimizer(simulator, target_fill_rate)

    def optimize_sq(
        self, 
        demand_paths: np.ndarray, 
        initial_ss: float, 
        initial_q: float,
        step_ss: float,
        step_q: float,
        expected_lead_time_demand: float,
        max_rounds: int = 100,
        poor_threshold_ratio: float = 1.3
    ) -> Tuple[float, float, float, Dict[str, float]]:
        """
        Optimize (s, Q) via neighborhood search.
        
        Neighbors evaluated:
            (Ss + step_ss, Q), (Ss - step_ss, Q), (Ss, Q + step_q), (Ss, Q - step_q)
        """
        current_ss = initial_ss
        current_q = initial_q
        
        s = expected_lead_time_demand + current_ss
        best_policy = SQPolicy(reorder_point=s, order_quantity=current_q)
        best_metrics = self._grid_evaluator._evaluate_candidate(demand_paths, best_policy, s)
        best_cost = best_metrics["total_cost"] if best_metrics["fill_rate"] >= self.target_fill_rate else float("inf")

        no_improvement_rounds = 0
        
        for r in range(max_rounds):
            improved = False
            
            # Define neighbors
            neighbors = [
                (current_ss + step_ss, current_q),
                (max(0.0, current_ss - step_ss), current_q),
                (current_ss, current_q + step_q),
                (current_ss, max(1.0, current_q - step_q))
            ]
            
            for ss, q in neighbors:
                s_neigh = expected_lead_time_demand + ss
                policy = SQPolicy(reorder_point=s_neigh, order_quantity=q)
                metrics = self._grid_evaluator._evaluate_candidate(demand_paths, policy, s_neigh)
                
                # Check diagnostic flag for poor candidate
                cost_ratio = metrics["total_cost"] / max(best_cost, 1e-6)
                if cost_ratio > poor_threshold_ratio:
                    logger.debug(f"Local search round {r}: candidate (ss={ss:.2f}, q={q:.2f}) flagged as poor (ratio={cost_ratio:.2f})")
                
                if metrics["fill_rate"] >= self.target_fill_rate:
                    if metrics["total_cost"] < best_cost:
                        best_cost = metrics["total_cost"]
                        current_ss = ss
                        current_q = q
                        best_metrics = metrics
                        improved = True
                        
            if improved:
                no_improvement_rounds = 0
            else:
                no_improvement_rounds += 1
                if no_improvement_rounds >= 10:  # stop if no improvement for 10 rounds
                    break
                    
        best_s = expected_lead_time_demand + current_ss
        return float(current_ss), float(current_q), float(best_s), best_metrics

    def optimize_rs(
        self, 
        demand_paths: np.ndarray, 
        initial_ss: float, 
        step_ss: float,
        expected_risk_period_demand: float,
        max_rounds: int = 100,
        poor_threshold_ratio: float = 1.3
    ) -> Tuple[float, float, Dict[str, float]]:
        """
        Optimize (R, S) via neighborhood search.
        
        Neighbors evaluated:
            S_s + step_ss, S_s - step_ss
        """
        current_ss = initial_ss
        S = expected_risk_period_demand + current_ss
        best_policy = RSPolicy(order_up_to_level=S)
        best_metrics = self._grid_evaluator._evaluate_candidate(demand_paths, best_policy, S)
        best_cost = best_metrics["total_cost"] if best_metrics["fill_rate"] >= self.target_fill_rate else float("inf")

        no_improvement_rounds = 0
        
        for r in range(max_rounds):
            improved = False
            
            neighbors = [
                current_ss + step_ss,
                max(0.0, current_ss - step_ss)
            ]
            
            for ss in neighbors:
                S_neigh = expected_risk_period_demand + ss
                policy = RSPolicy(order_up_to_level=S_neigh)
                metrics = self._grid_evaluator._evaluate_candidate(demand_paths, policy, S_neigh)
                
                cost_ratio = metrics["total_cost"] / max(best_cost, 1e-6)
                if cost_ratio > poor_threshold_ratio:
                    logger.debug(f"Local search round {r}: candidate (ss={ss:.2f}) flagged as poor (ratio={cost_ratio:.2f})")
                
                if metrics["fill_rate"] >= self.target_fill_rate:
                    if metrics["total_cost"] < best_cost:
                        best_cost = metrics["total_cost"]
                        current_ss = ss
                        best_metrics = metrics
                        improved = True
                        
            if improved:
                no_improvement_rounds = 0
            else:
                no_improvement_rounds += 1
                if no_improvement_rounds >= 10:
                    break
                    
        best_S = expected_risk_period_demand + current_ss
        return float(current_ss), float(best_S), best_metrics
