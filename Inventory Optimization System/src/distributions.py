"""
Distributions Module for Inventory Optimization System.

Role:
  Contains statistical modeling tools for demand uncertainty. This includes
  empirical bootstrapping, Kernel Density Estimation (KDE) sampling, fitting Gamma
  and Shifted Gamma distributions using method of moments, calculating analytical
  Gamma expected units short (Gamma loss function), numerically solving for the
  protection level targeting a fill rate, and checking goodness-of-fit via RMSE,
  Kolmogorov-Smirnov (KS) tests, and Anderson-Darling tests.

Inputs:
  - Uncertainty values or demand paths.
  - Distribution parameters (k, theta, shift).
  - Target service level and cycle demand parameters.

Outputs:
  - Samples, fitted parameters, loss values, optimized protection levels, and goodness-of-fit stats.
"""

import numpy as np
import scipy.stats as stats
from scipy.optimize import minimize_scalar
from typing import Tuple, Dict, List, Callable, Union


def bootstrap_sample(
    values: np.ndarray, 
    size: int, 
    random_state: Union[int, np.random.Generator] = None
) -> np.ndarray:
    """
    Sample with replacement from empirical values.
    
    Inputs:
        values (np.ndarray): Historical values.
        size (int): Sample size to draw.
        random_state (int or np.random.Generator): Random state for reproducibility.
        
    Outputs:
        np.ndarray: Sampled values.
    """
    if len(values) == 0:
        return np.array([])
        
    if isinstance(random_state, np.random.Generator):
        rng = random_state
    else:
        rng = np.random.default_rng(random_state)
        
    return rng.choice(values, size=size, replace=True)


def kde_sample(
    values: np.ndarray, 
    size: int, 
    random_state: Union[int, np.random.Generator] = None,
    handle_negative: bool = True
) -> np.ndarray:
    """
    Fit a Gaussian Kernel Density Estimate (KDE) and draw samples.
    
    Inputs:
        values (np.ndarray): Historical values.
        size (int): Sample size to draw.
        random_state (int or np.random.Generator): Random state for reproducibility.
        handle_negative (bool): If True, clips negative samples to 0.0 (negative-mass handling).
        
    Outputs:
        np.ndarray: KDE-sampled values.
    """
    val_arr = np.array(values, dtype=float)
    if len(val_arr) == 0:
        return np.array([])
        
    # Fit KDE using scipy stats
    kde = stats.gaussian_kde(val_arr)
    
    # Configure custom bandwidth matching standard: factor = 0.9 * n**(-0.2)
    n = len(val_arr)
    factor = 0.9 * (n ** (-0.2))
    kde.covariance_factor = lambda: factor
    kde._compute_covariance()
    
    # Sample from KDE
    if isinstance(random_state, np.random.Generator):
        # scipy.stats.gaussian_kde.resample uses np.random.seed internally or standard generator
        # To make it robust, we set seed temporarily or draw manually using scipy resample
        # gaussian_kde resample takes seed or generator in newer scipy versions
        try:
            samples = kde.resample(size, seed=random_state)[0]
        except TypeError:
            # Fallback for older scipy versions
            np.random.seed(random_state) if isinstance(random_state, int) else None
            samples = kde.resample(size)[0]
    else:
        samples = kde.resample(size, seed=random_state)[0]
        
    if handle_negative:
        samples = np.maximum(samples, 0.0)
        
    return samples


def fit_gamma_moments(values: np.ndarray) -> Tuple[float, float]:
    """
    Fit standard Gamma distribution using Method of Moments.
    k = mean^2 / var, theta = var / mean.
    
    Inputs:
        values (np.ndarray): Historical values (non-negative).
        
    Outputs:
        Tuple[float, float]: Shape parameter (k), Scale parameter (theta).
    """
    val_arr = np.array(values, dtype=float)
    mean_val = np.mean(val_arr)
    var_val = np.var(val_arr, ddof=1) if len(val_arr) > 1 else 1.0
    
    if mean_val <= 0:
        raise ValueError("Mean of values must be positive to fit a Gamma distribution.")
    if var_val <= 0:
        var_val = 1e-6
        
    theta = var_val / mean_val
    k = (mean_val ** 2) / var_val
    
    return float(k), float(theta)


def fit_shifted_gamma(values: np.ndarray, shift: float) -> Tuple[float, float, float]:
    """
    Fit Shifted Gamma distribution using Method of Moments.
    k_c = (mean - shift)^2 / var, theta_c = var / (mean - shift).
    
    Inputs:
        values (np.ndarray): Historical values.
        shift (float): Shift parameter (lower bound of distribution).
        
    Outputs:
        Tuple[float, float, float]: Shape parameter (k_c), Scale parameter (theta_c), shift.
    """
    val_arr = np.array(values, dtype=float)
    mean_val = np.mean(val_arr)
    var_val = np.var(val_arr, ddof=1) if len(val_arr) > 1 else 1.0
    
    if mean_val <= shift:
        # If mean is below shift, adjust shift to be below mean (e.g. shift = 0.9 * mean)
        shift = 0.9 * mean_val
        
    mean_shifted = mean_val - shift
    if var_val <= 0:
        var_val = 1e-6
        
    theta_c = var_val / mean_shifted
    k_c = (mean_shifted ** 2) / var_val
    
    return float(k_c), float(theta_c), float(shift)


def gamma_loss_function(iota: float, k: float, theta: float) -> float:
    """
    Analytical expected units short for Gamma(k, theta) at protection level iota.
    Formula: L(iota; k, theta) = k * theta * [1 - F(iota; k+1, theta)] - iota * [1 - F(iota; k, theta)]
    
    Inputs:
        iota (float): Protection level.
        k (float): Shape parameter.
        theta (float): Scale parameter.
        
    Outputs:
        float: Expected units short.
    """
    if k <= 0 or theta <= 0:
        raise ValueError("Gamma shape and scale must be positive.")
        
    if iota <= 0:
        # If protection level is <= 0, expected units short is the expected demand (k * theta)
        return float(k * theta)
        
    cdf_kp1 = stats.gamma.cdf(iota, a=k+1, scale=theta)
    cdf_k = stats.gamma.cdf(iota, a=k, scale=theta)
    
    exp_short = k * theta * (1.0 - cdf_kp1) - iota * (1.0 - cdf_k)
    return float(np.maximum(exp_short, 0.0))


def solve_gamma_protection_level(
    k: float, 
    theta: float, 
    d_c: float, 
    beta: float,
    shift: float = 0.0
) -> float:
    """
    Solve for protection level iota* that achieves target fill rate beta under Gamma(k, theta) demand.
    Solves: L(iota - shift; k, theta) = d_c * (1 - beta).
    
    Inputs:
        k (float): Shape parameter.
        theta (float): Scale parameter.
        d_c (float): Expected demand over the cycle (Q or E[D_R]).
        beta (float): Target fill rate (e.g. 0.95).
        shift (float): Shift offset if using Shifted Gamma (default 0.0).
        
    Outputs:
        float: Solved protection level (iota* = iota_shifted + shift).
    """
    target_short = d_c * (1.0 - beta)
    
    # Objective function to minimize: squared error of expected short
    def objective(iota_shifted):
        val = gamma_loss_function(iota_shifted, k, theta)
        return (val - target_short) ** 2
        
    # Bounds for optimization: [0, expected demand + 10 standard deviations]
    mean_val = k * theta
    std_val = np.sqrt(k) * theta
    max_bound = max(mean_val + 10 * std_val, 1e-3)
    
    res = minimize_scalar(objective, bounds=(0, max_bound), method="bounded")
    return float(res.x + shift)


def calculate_tail_error(
    empirical: np.ndarray, 
    fitted: np.ndarray, 
    percentiles: List[float] = [90.0, 95.0, 97.5, 99.0]
) -> Dict[float, float]:
    """
    Calculate upper-tail quantile errors between empirical and fitted distributions.
    
    Inputs:
        empirical (np.ndarray): Empirical dataset.
        fitted (np.ndarray): Fitted/simulated dataset.
        percentiles (List[float]): List of percentiles to check.
        
    Outputs:
        Dict[float, float]: Dict mapping percentile -> (fitted_val - empirical_val)
    """
    errors = {}
    for pct in percentiles:
        emp_q = np.percentile(empirical, pct)
        fit_q = np.percentile(fitted, pct)
        errors[pct] = float(fit_q - emp_q)
    return errors


def calculate_rmse(empirical: np.ndarray, fitted: np.ndarray) -> float:
    """
    Calculate the Root Mean Squared Error (RMSE) of quantiles across a 100-point probability grid.
    
    Inputs:
        empirical (np.ndarray): Empirical dataset.
        fitted (np.ndarray): Fitted/simulated dataset.
        
    Outputs:
        float: RMSE value.
    """
    prob_grid = np.linspace(1, 99, 99)
    emp_q = np.percentile(empirical, prob_grid)
    fit_q = np.percentile(fitted, prob_grid)
    return float(np.sqrt(np.mean((emp_q - fit_q) ** 2)))


def run_kolmogorov_smirnov(
    empirical: np.ndarray, 
    fitted: np.ndarray
) -> Dict[str, float]:
    """
    Run a two-sample Kolmogorov-Smirnov test to measure distance between CDFs.
    
    Inputs:
        empirical (np.ndarray): Empirical dataset.
        fitted (np.ndarray): Fitted/simulated dataset.
        
    Outputs:
        Dict: Contains 'ks_stat' (D statistic) and 'p_value'.
    """
    res = stats.ks_2samp(empirical, fitted)
    return {
        "ks_stat": float(res.statistic),
        "p_value": float(res.pvalue)
    }


def run_anderson_darling(
    empirical: np.ndarray, 
    fitted: np.ndarray
) -> Dict[str, float]:
    """
    Compute an Anderson-Darling-like statistic (weighted distance prioritizing tails) between two samples.
    Here we compute the two-sample Anderson-Darling statistic.
    
    Inputs:
        empirical (np.ndarray): Empirical dataset.
        fitted (np.ndarray): Fitted/simulated dataset.
        
    Outputs:
        Dict: Contains 'ad_stat' and 'p_value' (if computed).
    """
    # scipy.stats.anderson_ksamp runs two-sample AD test
    try:
        res = stats.anderson_ksamp([empirical, fitted])
        return {
            "ad_stat": float(res.statistic),
            "p_value": float(res.significance_level)
        }
    except Exception:
        # Fallback if calculation fails due to sample size or duplicate points
        return {"ad_stat": -1.0, "p_value": -1.0}
