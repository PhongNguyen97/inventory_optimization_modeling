"""
Demand Uncertainty Module for Inventory Optimization System.

Role:
  Separates expected weekly demand from unexpected demand uncertainty by calculating
  forecast errors (residuals) and forecast ratios. It includes functions to check for
  forecast bias, center ratios, calibrate forecasts, and winsorize (cap) extreme ratio/residual
  values to prevent outliers from distorting the simulation.

Inputs:
  - Actual weekly sales array.
  - Fitted weekly forecast array.
  - Capping and epsilon parameters.

Outputs:
  - Ratio and residual arrays, bias diagnostic dictionaries, and capped values.
"""

import numpy as np
from typing import Dict, Union


def calculate_ratios(
    actual: np.ndarray, 
    forecast: np.ndarray, 
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Calculate forecast ratios: r_w = actual_w / max(forecast_w, epsilon).
    
    Inputs:
        actual (np.ndarray): Array of actual sales.
        forecast (np.ndarray): Array of forecast or fitted sales.
        epsilon (float): Small value to prevent division by zero or near-zero forecasts.
        
    Outputs:
        np.ndarray: Array of multiplicative forecast ratios.
    """
    act_arr = np.array(actual, dtype=float)
    fore_arr = np.array(forecast, dtype=float)
    
    if act_arr.shape != fore_arr.shape:
        raise ValueError(f"Actual shape {act_arr.shape} and Forecast shape {fore_arr.shape} must be identical.")
        
    denominator = np.maximum(fore_arr, epsilon)
    return act_arr / denominator


def calculate_residuals(actual: np.ndarray, forecast: np.ndarray) -> np.ndarray:
    """
    Calculate forecast residuals: e_w = actual_w - forecast_w.
    
    Inputs:
        actual (np.ndarray): Array of actual sales.
        forecast (np.ndarray): Array of forecast or fitted sales.
        
    Outputs:
        np.ndarray: Array of additive forecast residuals.
    """
    act_arr = np.array(actual, dtype=float)
    fore_arr = np.array(forecast, dtype=float)
    
    if act_arr.shape != fore_arr.shape:
        raise ValueError(f"Actual shape {act_arr.shape} and Forecast shape {fore_arr.shape} must be identical.")
        
    return act_arr - fore_arr


def check_ratio_bias(ratios: np.ndarray, tolerance: float = 0.05) -> Dict[str, Union[float, bool]]:
    """
    Check if forecast ratios are biased (mean ratio significantly deviates from 1.0).
    
    Inputs:
        ratios (np.ndarray): Multiplicative forecast ratios.
        tolerance (float): Allowable deviation from 1.0 (default 0.05, meaning [0.95, 1.05]).
        
    Outputs:
        Dict: Contains "mean_ratio", "deviation", and boolean "passed_bias_check".
    """
    mean_val = float(np.mean(ratios))
    dev = abs(mean_val - 1.0)
    passed = dev <= tolerance
    
    return {
        "mean_ratio": mean_val,
        "deviation": dev,
        "passed_bias_check": passed
    }


def check_residual_bias(
    residuals: np.ndarray, 
    mean_demand: float = 1.0, 
    tolerance_pct: float = 0.05
) -> Dict[str, Union[float, bool]]:
    """
    Check if forecast residuals are biased (mean residual significantly deviates from 0.0).
    Bias is checked relative to the mean demand level (deviation / mean_demand <= tolerance_pct).
    
    Inputs:
        residuals (np.ndarray): Additive forecast residuals.
        mean_demand (float): Mean demand level, used for scaling tolerance.
        tolerance_pct (float): Permissible relative bias (default 0.05, meaning 5% of mean demand).
        
    Outputs:
        Dict: Contains "mean_residual", "relative_deviation", and boolean "passed_bias_check".
    """
    mean_val = float(np.mean(residuals))
    scaled_tol = max(mean_demand, 1e-6) * tolerance_pct
    passed = abs(mean_val) <= scaled_tol
    
    return {
        "mean_residual": mean_val,
        "relative_deviation": abs(mean_val) / max(mean_demand, 1e-6),
        "passed_bias_check": passed
    }


def center_ratios(ratios: np.ndarray, mean_ratio: float) -> np.ndarray:
    """
    Center forecast ratios: r_centered = ratios / mean_ratio, calibrating them to center around 1.0.
    
    Inputs:
        ratios (np.ndarray): Raw forecast ratios.
        mean_ratio (float): Observed mean ratio.
        
    Outputs:
        np.ndarray: Calibrated centered ratios.
    """
    if mean_ratio <= 0:
        return ratios
    return ratios / mean_ratio


def calibrate_forecast(forecast: np.ndarray, mean_ratio: float) -> np.ndarray:
    """
    Calibrate the forecast path: forecast_calibrated = forecast * mean_ratio.
    
    Inputs:
        forecast (np.ndarray): Raw forecast path.
        mean_ratio (float): Observed historical forecast ratio bias.
        
    Outputs:
        np.ndarray: Calibrated forecast path.
    """
    return forecast * mean_ratio


def cap_by_percentile(
    values: np.ndarray, 
    lower_pct: float = 1.0, 
    upper_pct: float = 99.0
) -> np.ndarray:
    """
    Winsorize (cap) the values using percentile boundaries.
    
    Inputs:
        values (np.ndarray): Input uncertainty values (ratios or residuals).
        lower_pct (float): Lower percentile limit (e.g. 1.0 or 2.5).
        upper_pct (float): Upper percentile limit (e.g. 99.0 or 97.5).
        
    Outputs:
        np.ndarray: Capped values.
    """
    val_arr = np.array(values, dtype=float)
    if len(val_arr) == 0:
        return val_arr
        
    lower_bound = np.percentile(val_arr, lower_pct)
    upper_bound = np.percentile(val_arr, upper_pct)
    
    return np.clip(val_arr, lower_bound, upper_bound)
