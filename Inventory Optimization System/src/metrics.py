"""
Metrics Module for Inventory Optimization System.

Role:
  Contains all metric calculations for evaluating inventory policies. This includes
  simulated fill rate, analytical fill rate, cycle service level (CSL), average inventory,
  total inventory-related cost, and descriptive statistics used to justify the selection
  of continuous review (s,Q) vs periodic review (R,S) policies.

Inputs:
  - Demand history and shortage history (arrays or values).
  - Cost rates and histories.

Outputs:
  - Float metric values or summary DataFrames.
"""

import numpy as np
import pandas as pd
from src.config import Config


def calculate_fill_rate(total_demand: float, total_units_short: float) -> float:
    """
    Calculate the realized fill rate (fraction of demand met from on-hand inventory).
    Formula: beta = 1 - (total_units_short / total_demand)
    This helps evaluate the performance at the individual scenario level 
    during the 10,000-replication Monte Carlo simulation.
    
    Inputs:
        total_demand (float): Sum of demand over the simulation period.
        total_units_short (float): Sum of lost sales/shortages over the simulation period.
        
    Outputs:
        float: Realized fill rate (clamped between 0.0 and 1.0).
    """
    if total_demand <= 0:
        return 1.0
    
    fill_rate = 1.0 - (total_units_short / total_demand)
    return float(np.clip(fill_rate, 0.0, 1.0))


def calculate_analytical_fill_rate(expected_units_short: float, cycle_demand: float) -> float:
    """
    Calculate the analytical fill rate for a given cycle.
    Formula: beta = 1 - (expected_units_short / cycle_demand)
    This helps answer "If I hold X units of safety stock, what theoretical service level (fill rate) will it deliver?"
    
    Inputs:
        expected_units_short (float): Analytical expected units short.
        cycle_demand (float): Expected demand over the cycle (Q for continuous, E[D_R] for periodic).
        
    Outputs:
        float: Analytical fill rate.
    """
    if cycle_demand <= 0:
        return 1.0
        
    fill_rate = 1.0 - (expected_units_short / cycle_demand)
    return float(np.clip(fill_rate, 0.0, 1.0))


def calculate_cycle_service_level(stockout_flags: np.ndarray) -> float:
    """
    Calculate the Cycle Service Level (CSL) as the percentage of cycles (or weeks) without stockouts.
    Formula: CSL = 1 - (number of stockout events / total periods)
    
    Inputs:
        stockout_flags (np.ndarray): Boolean or 0/1 array indicating stockout events in each cycle/week.
        
    Outputs:
        float: Cycle service level.
    """
    if len(stockout_flags) == 0:
        return 1.0
    return float(1.0 - np.mean(stockout_flags))


def calculate_total_cost(
    holding_cost_rate: float, 
    avg_inventory: float, 
    order_cost: float, 
    num_orders: int, 
    shortage_cost: float, 
    units_short: float
) -> float:
    """
    Calculate the total inventory-related cost.
    Formula: Total Cost = H * Avg_Inventory + K * Num_Orders + B * Units_Short
    
    Inputs:
        holding_cost_rate (float): Weekly unit holding cost (H_week).
        avg_inventory (float): Average physical on-hand inventory.
        order_cost (float): Fixed transaction cost per order (K).
        num_orders (int): Number of replenishment orders placed.
        shortage_cost (float): Unit shortage/lost-sales penalty (B).
        units_short (float): Total units short/lost sales.
        
    Outputs:
        float: Total inventory cost.
    """
    tc = (holding_cost_rate * avg_inventory) + (order_cost * num_orders) + (shortage_cost * units_short)
    return float(tc)


def calculate_average_inventory(on_hand_history: np.ndarray) -> float:
    """
    Calculate the average physical on-hand inventory level.
    
    Inputs:
        on_hand_history (np.ndarray): Array tracking on-hand inventory level at each week's step.
        
    Outputs:
        float: Average inventory.
    """
    if len(on_hand_history) == 0:
        return 0.0
    return float(np.mean(on_hand_history))


def calculate_justification_statistics(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Calculate descriptive demand statistics by family to defend policy selection.
    
    Inputs:
        df (pd.DataFrame): Training demand DataFrame.
        config (Config): Configuration containing column mappings.
        
    Outputs:
        pd.DataFrame: Table with columns [family, Mean_Weekly, Std_Weekly, CV, Demand_Freq, Zero_Demand_Freq]
    """
    col_family = config.columns.get("family", "family")
    col_actual = config.columns.get("train_actual", "Actual_Sales")
    
    results = []
    
    for family, group in df.groupby(col_family):
        demand = group[col_actual].values
        n = len(demand)
        
        if n == 0:
            continue
            
        mean_demand = np.mean(demand)
        std_demand = np.std(demand, ddof=1) if n > 1 else 0.0
        cv = std_demand / mean_demand if mean_demand > 0 else 0.0
        
        num_positive = np.sum(demand > 0)
        num_zero = np.sum(demand == 0)
        
        demand_freq = num_positive / n
        zero_freq = num_zero / n
        
        results.append({
            "family": family,
            "Mean Weekly Demand": mean_demand,
            "Weekly Standard Deviation": std_demand,
            "Weekly CV": cv,
            "Weekly Demand Frequency": demand_freq,
            "Weekly Zero-Demand Frequency": zero_freq,
            "Chosen Policy": config.policies.get(family, "Unknown")
        })
        
    return pd.DataFrame(results)
