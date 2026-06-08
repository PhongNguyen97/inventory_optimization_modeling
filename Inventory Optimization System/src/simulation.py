"""
Simulation Module for Inventory Optimization System.

Role:
  Implements the core weekly inventory simulation engine. Given a demand path, an
  inventory policy object, and initial inventory state, it steps week-by-week through
  a strict 9-step event sequence to model inventory transitions. It supports both
  continuous review (s,Q) and periodic review (R,S) policies under a lost sales
  assumption.
  
  To optimize performance, it supports both 1D (scalar) demand paths and 2D (vectorized)
  demand paths (running N replications in parallel via NumPy vector operations).

Inputs:
  - Lead time (L).
  - Cost parameters (holding cost weekly H, ordering cost K, shortage cost B).
  - Demand path (np.ndarray, 1D or 2D).
  - Policy object (SQPolicy or RSPolicy).
  - Initial on-hand inventory level.

Outputs:
  - Dict containing full historical records (on-hand, on-order, inventory position,
    shortages, and orders placed) and summarized policy performance metrics.
"""

import numpy as np
from typing import Dict, Union
from src.policies import SQPolicy, RSPolicy
from src.metrics import (
    calculate_fill_rate,
    calculate_cycle_service_level,
    calculate_total_cost,
    calculate_average_inventory
)


class InventorySimulator:
    """
    Weekly Inventory Simulation Engine.
    Executes a step-by-step weekly simulation under lost sales logic.
    Supports scalar (1D) and vectorized (2D) demand inputs.
    """

    def __init__(
        self, 
        lead_time: int, 
        holding_cost: float, 
        order_cost: float, 
        shortage_cost: float,
        backorder: bool = False
    ):
        """
        Initialize the simulator with operational and cost settings.
        
        Inputs:
            lead_time (int): Replenishment lead time (L) in weeks.
            holding_cost (float): Weekly unit holding cost (H_week).
            order_cost (float): Fixed cost per order placed (K).
            shortage_cost (float): Shortage cost per unit short (B).
            backorder (bool): If True, backorders are allowed (unmet demand carries over).
                              If False, lost sales are assumed (default).
        """
        self.lead_time = int(lead_time)
        self.holding_cost = float(holding_cost)
        self.order_cost = float(order_cost)
        self.shortage_cost = float(shortage_cost)
        self.backorder = bool(backorder)

    def simulate(
        self, 
        demand_path: np.ndarray, 
        policy: Union[SQPolicy, RSPolicy], 
        initial_inventory: float
    ) -> Dict[str, Union[np.ndarray, float, int]]:
        """
        Run the week-by-week inventory simulation. Dispatches to scalar or vectorized
        implementations based on the dimensionality of demand_path.
        """
        demand_arr = np.array(demand_path, dtype=float)
        if demand_arr.ndim == 2:
            return self._simulate_vectorized(demand_arr, policy, initial_inventory)
        else:
            return self._simulate_scalar(demand_arr, policy, initial_inventory)

    def _simulate_scalar(
        self, 
        demand_path: np.ndarray, 
        policy: Union[SQPolicy, RSPolicy], 
        initial_inventory: float
    ) -> Dict[str, Union[np.ndarray, float, int]]:
        n_weeks = len(demand_path)
        if n_weeks == 0:
            raise ValueError("Demand path cannot be empty.")

        # State Variables
        on_hand = float(initial_inventory)
        on_order = 0.0
        backorders = 0.0
        
        arrivals = np.zeros(n_weeks + self.lead_time + 1)
        
        history_on_hand_start = np.zeros(n_weeks)
        history_on_hand_end = np.zeros(n_weeks)
        history_on_order = np.zeros(n_weeks)
        history_ip = np.zeros(n_weeks)
        history_demand = np.zeros(n_weeks)
        history_short = np.zeros(n_weeks)
        history_orders = np.zeros(n_weeks)
        history_stockout_flag = np.zeros(n_weeks)

        is_periodic = isinstance(policy, RSPolicy)

        for w in range(n_weeks):
            # Step 1: Receive orders
            arrived_qty = float(arrivals[w])
            on_hand += arrived_qty
            on_order = max(0.0, on_order - arrived_qty)
            
            history_on_hand_start[w] = on_hand
            
            # Step 2: Demand D_w
            dem = float(demand_path[w])
            history_demand[w] = dem
            
            # Step 3: Satisfy demand
            if self.backorder:
                total_req = dem + backorders
                satisfied = min(on_hand, total_req)
                short = total_req - satisfied
                backorders = short
                units_short_this_week = max(0.0, dem - (satisfied - (total_req - dem)))
                on_hand -= satisfied
            else:
                satisfied = min(on_hand, dem)
                short = dem - satisfied
                units_short_this_week = short
                on_hand -= satisfied
                
            history_on_hand_end[w] = on_hand
            history_short[w] = units_short_this_week
            history_stockout_flag[w] = 1.0 if units_short_this_week > 0.0 else 0.0
            
            # Step 6: Compute inventory position
            ip = on_hand + on_order - (backorders if self.backorder else 0.0)
            
            # Step 7: Apply policy
            ord_qty = policy.order_quantity(ip, week_idx=w)
                
            # Step 8: Place order
            if ord_qty > 0.0:
                history_orders[w] = ord_qty
                arrivals[w + self.lead_time] += ord_qty
                on_order += ord_qty
                ip = on_hand + on_order - (backorders if self.backorder else 0.0)
            else:
                history_orders[w] = 0.0
                
            history_on_order[w] = on_order
            history_ip[w] = ip

        avg_oh = calculate_average_inventory(history_on_hand_end)
        total_short = float(np.sum(history_short))
        total_dem = float(np.sum(history_demand))
        num_ords = int(np.sum(history_orders > 0))
        
        fill_rate = calculate_fill_rate(total_dem, total_short)
        csl = calculate_cycle_service_level(history_stockout_flag)
        tot_cost = calculate_total_cost(
            holding_cost_rate=self.holding_cost,
            avg_inventory=avg_oh,
            order_cost=self.order_cost,
            num_orders=num_ords,
            shortage_cost=self.shortage_cost,
            units_short=total_short
        )

        return {
            "on_hand_start": history_on_hand_start,
            "on_hand_end": history_on_hand_end,
            "on_order": history_on_order,
            "inventory_position": history_ip,
            "demand": history_demand,
            "units_short_history": history_short,
            "orders_placed_history": history_orders,
            "stockout_flag": history_stockout_flag,
            
            "avg_inventory": avg_oh,
            "units_short": total_short,
            "num_orders": num_ords,
            "fill_rate": fill_rate,
            "cycle_service_level": csl,
            "total_cost": tot_cost,
            "total_cost_std": 0.0,
            
            "ending_inventory_distribution": np.array([on_hand]),
            "order_quantity_distribution": history_orders[history_orders > 0]
        }

    def _simulate_vectorized(
        self, 
        demand_paths: np.ndarray, 
        policy: Union[SQPolicy, RSPolicy], 
        initial_inventory: float
    ) -> Dict[str, Union[np.ndarray, float, int]]:
        n_reps, n_weeks = demand_paths.shape

        on_hand = np.ones(n_reps, dtype=float) * initial_inventory
        on_order = np.zeros(n_reps, dtype=float)
        backorders = np.zeros(n_reps, dtype=float)
        
        arrivals = np.zeros((n_reps, n_weeks + self.lead_time + 1), dtype=float)
        
        history_on_hand_end = np.zeros((n_reps, n_weeks), dtype=float)
        history_short = np.zeros((n_reps, n_weeks), dtype=float)
        history_stockout_flag = np.zeros((n_reps, n_weeks), dtype=float)
        history_orders = np.zeros((n_reps, n_weeks), dtype=float)
        history_ip = np.zeros((n_reps, n_weeks), dtype=float)

        for w in range(n_weeks):
            # Step 1: Receive orders
            arrived_qty = arrivals[:, w]
            on_hand += arrived_qty
            on_order = np.maximum(0.0, on_order - arrived_qty)
            
            # Step 2: Demand
            dem = demand_paths[:, w]
            
            # Step 3: Satisfy demand
            if self.backorder:
                total_req = dem + backorders
                satisfied = np.minimum(on_hand, total_req)
                short = total_req - satisfied
                backorders = short
                units_short_this_week = np.maximum(0.0, dem - (satisfied - (total_req - dem)))
                on_hand -= satisfied
            else:
                satisfied = np.minimum(on_hand, dem)
                short = dem - satisfied
                units_short_this_week = short
                on_hand -= satisfied
                
            history_on_hand_end[:, w] = on_hand
            history_short[:, w] = units_short_this_week
            history_stockout_flag[:, w] = (units_short_this_week > 0.0).astype(float)
            
            # Step 6: IP
            ip = on_hand + on_order - (backorders if self.backorder else 0.0)
            
            # Step 7: Apply policy (passing vector of IPs)
            ord_qty = policy.order_quantity(ip, week_idx=w)
            
            # Step 8 & 9: Place and schedule orders
            arrivals[:, w + self.lead_time] += ord_qty
            on_order += ord_qty
            ip = on_hand + on_order - (backorders if self.backorder else 0.0)
            
            history_orders[:, w] = ord_qty
            history_ip[:, w] = ip
            
        # Summarize simulation performance metrics
        avg_oh_reps = np.mean(history_on_hand_end, axis=1)
        total_short_reps = np.sum(history_short, axis=1)
        total_dem_reps = np.sum(demand_paths, axis=1)
        num_ords_reps = np.sum(history_orders > 0, axis=1)
        stockout_pct_reps = np.mean(history_stockout_flag, axis=1)
        
        fill_rates = np.where(total_dem_reps > 0, 1.0 - (total_short_reps / total_dem_reps), 1.0)
        fill_rates = np.clip(fill_rates, 0.0, 1.0)
        csls = 1.0 - stockout_pct_reps
        
        costs = (self.holding_cost * avg_oh_reps) + (self.order_cost * num_ords_reps) + (self.shortage_cost * total_short_reps)
        
        return {
            "on_hand_end": np.mean(history_on_hand_end, axis=0),
            "inventory_position": np.mean(history_ip, axis=0),
            "units_short_history": np.mean(history_short, axis=0),
            "orders_placed_history": np.mean(history_orders, axis=0),
            "stockout_flag": np.mean(history_stockout_flag, axis=0),
            
            "avg_inventory": float(np.mean(avg_oh_reps)),
            "units_short": float(np.mean(total_short_reps)),
            "num_orders": float(np.mean(num_ords_reps)),
            "fill_rate": float(np.mean(fill_rates)),
            "cycle_service_level": float(np.mean(csls)),
            "total_cost": float(np.mean(costs)),
            "total_cost_std": float(np.std(costs)),
            
            "ending_inventory_distribution": history_on_hand_end[:, -1],
            "order_quantity_distribution": history_orders[history_orders > 0]
        }
