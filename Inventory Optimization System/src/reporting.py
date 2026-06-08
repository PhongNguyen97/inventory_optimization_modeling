"""
Reporting Module for Inventory Optimization System.

Role:
  Handles result serialization, formatting, and visualization. It implements:
  1. Exporting optimization and final policy results to CSVs.
  2. Formatting the final policy table to match the 15-column standardized schema required
     for Power BI dashboard integration.
  3. Plotting utilities using matplotlib and seaborn to visualize distribution fits,
     simulation histories, safety stock distributions, and sensitivity analysis results.

Inputs:
  - DataFrames and dictionaries of results.
  - Slices of simulation histories.
  - Matplotlib parameters and paths.

Outputs:
  - Saved CSV data files in appropriate folder structures.
  - Visualization PNG images in the `outputs/plots/` folder.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List

# Set style for modern premium report aesthetics
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 16,
    "font.family": "sans-serif"
})

# Harmonious dark/vibrant color palette
COLOR_PRIMARY = "#2C3E50"  # Sleek dark blue
COLOR_SECONDARY = "#E74C3C" # Vibrant coral red
COLOR_ACCENT = "#3498DB"    # Sky blue
COLOR_MUTED = "#BDC3C7"     # Muted grey


def export_policy_results(results_df: pd.DataFrame, path: str):
    """
    Save the optimized base-case policy results table.
    
    Inputs:
        results_df (pd.DataFrame): Optimization results DataFrame.
        path (str): File destination path (e.g. outputs/policy_results/base_case_optimization_results.csv)
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    results_df.to_csv(path, index=False)
    print(f"Policy results exported successfully to: {path}")


def export_sensitivity_summary(sensitivity_df: pd.DataFrame, path: str):
    """
    Save the sensitivity analysis results table.
    
    Inputs:
        sensitivity_df (pd.DataFrame): Sensitivity summary DataFrame.
        path (str): Destination path (e.g. outputs/sensitivity_results/sensitivity_summary.csv)
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sensitivity_df.to_csv(path, index=False)
    print(f"Sensitivity summary exported successfully to: {path}")


def create_policy_comparison_table(base_results: pd.DataFrame) -> pd.DataFrame:
    """
    Format and clean optimization results into a comparison table.
    
    Inputs:
        base_results (pd.DataFrame): Optimization results.
        
    Outputs:
        pd.DataFrame: Formatted comparison table.
    """
    df = base_results.copy()
    
    # Columns to round
    round_cols = ["safety_stock", "reorder_point", "order_quantity", "order_up_to_level", "avg_inventory", "units_short", "total_cost"]
    for col in round_cols:
        if col in df.columns:
            df[col] = df[col].round(2)
            
    pct_cols = ["fill_rate", "cycle_service_level"]
    for col in pct_cols:
        if col in df.columns:
            df[col] = (df[col] * 100).round(2).astype(str) + "%"
            
    return df


def export_powerbi_table(results_list: List[Dict[str, Any]], path: str):
    """
    Export results in the strict 15-column standardized schema required for Power BI:
      family, policy_type, lead_time, review_period, risk_period, safety_stock,
      reorder_point, order_quantity, order_up_to_level, fill_rate, cycle_service_level,
      total_cost, avg_inventory, num_orders, units_short
      
    Inputs:
        results_list (List[Dict[str, Any]]): List of dicts, each representing a product family.
        path (str): Destination path (outputs/tables/powerbi_inventory_policy_table.csv)
    """
    standard_columns = [
        "family",
        "policy_type",
        "lead_time",
        "review_period",
        "risk_period",
        "safety_stock",
        "reorder_point",
        "order_quantity",
        "order_up_to_level",
        "fill_rate",
        "cycle_service_level",
        "total_cost",
        "avg_inventory",
        "num_orders",
        "units_short"
    ]
    
    formatted_rows = []
    
    for row in results_list:
        formatted_row = {}
        for col in standard_columns:
            # Get value, defaulting to np.nan if missing
            val = row.get(col, np.nan)
            
            # Convert periodic review order quantity to string/indicator if needed, 
            # or keep it nan as per policy requirements
            formatted_row[col] = val
            
        formatted_rows.append(formatted_row)
        
    pbi_df = pd.DataFrame(formatted_rows, columns=standard_columns)
    
    # Round columns for clean display
    float_cols = ["safety_stock", "reorder_point", "order_quantity", "order_up_to_level", "fill_rate", "cycle_service_level", "total_cost", "avg_inventory", "units_short"]
    for col in float_cols:
        pbi_df[col] = pbi_df[col].round(4)
        
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pbi_df.to_csv(path, index=False)
    print(f"Power BI standardized table exported successfully to: {path}")


# --- Plotting Utilities ---

def plot_ending_inventory_distribution(ending_invs: np.ndarray, family: str, path: str):
    """
    Plot ending inventory distribution from Monte Carlo validations.
    """
    plt.figure(figsize=(8, 5))
    sns.histplot(ending_invs, kde=True, color=COLOR_ACCENT, bins=30, edgecolor="w", alpha=0.85)
    plt.axvline(x=0.0, color=COLOR_SECONDARY, linestyle="--", linewidth=1.5, label="Stockout Boundary (0)")
    
    plt.title(f"Ending On-Hand Inventory Distribution - {family}")
    plt.xlabel("Ending Inventory Level (Units)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, dpi=300)
    plt.close()


def plot_sensitivity_summary(sensitivity_df: pd.DataFrame, family: str, path: str):
    """
    Plot total costs and safety stock levels across cost sensitivity scenarios.
    """
    fam_df = sensitivity_df[sensitivity_df["family"] == family].copy()
    if fam_df.empty:
        return
        
    # Set up subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 1. Total Cost Plot
    sns.barplot(
        data=fam_df, 
        x="scenario", 
        y="total_cost", 
        ax=axes[0], 
        palette="viridis",
        hue="scenario",
        legend=False
    )
    axes[0].set_title(f"Average Weekly Total Cost - {family}")
    axes[0].set_ylabel("Cost Index")
    axes[0].set_xlabel("")
    axes[0].tick_params(axis="x", rotation=45)
    
    # 2. Safety Stock Plot
    sns.barplot(
        data=fam_df, 
        x="scenario", 
        y="safety_stock", 
        ax=axes[1], 
        palette="magma",
        hue="scenario",
        legend=False
    )
    axes[1].set_title(f"Optimized Safety Stock Level - {family}")
    axes[1].set_ylabel("Safety Stock (Units)")
    axes[1].set_xlabel("")
    axes[1].tick_params(axis="x", rotation=45)
    
    plt.suptitle(f"Cost Sensitivity Analysis - {family}", y=1.02)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, dpi=300)
    plt.close()


def plot_uncertainty_distributions(
    ratios: np.ndarray,
    gamma_samples: np.ndarray,
    kde_samples: np.ndarray,
    family: str,
    path: str
):
    """
    Plot and compare forecast ratio distribution (empirical vs parametric Gamma vs KDE).
    """
    plt.figure(figsize=(9, 5))
    
    sns.kdeplot(ratios, label="Empirical (Ratios)", color=COLOR_PRIMARY, linewidth=2)
    sns.kdeplot(gamma_samples, label="Fitted Gamma", color=COLOR_SECONDARY, linestyle="--", linewidth=1.5)
    sns.kdeplot(kde_samples, label="Gaussian KDE", color=COLOR_ACCENT, linestyle=":", linewidth=2)
    
    plt.title(f"Demand Uncertainty Modeling Comparison - {family}")
    plt.xlabel("Forecast Ratio (Actual / Forecast)")
    plt.ylabel("Probability Density")
    plt.legend()
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, dpi=300)
    plt.close()
