"""
Configuration Module for Inventory Optimization System.

Role:
  Loads, parses, and validates the YAML configuration file containing model assumptions,
  cost values, policy mapping, service level targets, and simulation details. It also
  computes derived values such as weekly holding costs to prevent repetitive recalculations.

Inputs:
  Path to `inventory_config.yaml` (typically in `configs/` folder).

Outputs:
  Configuration dictionary and derived parameters available for the entire package.
"""

import os
import yaml


class Config:
    """
    Config class that loads inventory configuration from a YAML file,
    exposes parameters as attributes, and computes derived constants.
    """

    def __init__(self, config_path: str):
        """
        Initialize the configuration object by reading a YAML file.
        
        Input:
            config_path (str): Absolute or relative path to the YAML config file.
        """
        self.config_path = config_path
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
            
        with open(config_path, "r") as f:
            self._raw_config = yaml.safe_load(f)

        # Basic Project Settings
        project_cfg = self._raw_config.get("project", {})
        self.demand_scale = project_cfg.get("demand_scale", "weekly")
        self.selected_families = project_cfg.get("selected_families", ["GROCERY I", "BEVERAGES", "CLEANING"])

        # Policy Mapping
        self.policies = self._raw_config.get("policies", {
            "GROCERY I": "SQ",
            "BEVERAGES": "SQ",
            "CLEANING": "RS"
        })

        # Service Levels
        service_cfg = self._raw_config.get("service_level", {})
        self.target_fill_rate = service_cfg.get("target_fill_rate", 0.95)

        # Lead Times and Review Periods
        self.lead_times = self._raw_config.get("lead_time", {
            "GROCERY I": 1,
            "BEVERAGES": 1,
            "CLEANING": 1
        })
        self.review_periods = self._raw_config.get("review_period", {
            "CLEANING": 1
        })

        # Costs and Derived Weekly Holding Cost
        costs_cfg = self._raw_config.get("costs", {})
        self.unit_cost = costs_cfg.get("unit_cost", 1.0)
        self.annual_holding_rate = costs_cfg.get("annual_holding_rate", 0.15)
        self.order_cost = costs_cfg.get("order_cost", 25.0)
        self.shortage_costs = costs_cfg.get("shortage_cost", {
            "GROCERY I": 15.0,
            "BEVERAGES": 12.0,
            "CLEANING": 15.0
        })

        # Derived Weekly Holding Cost per Unit: H_week = c * h_annual / 52
        self.holding_cost_weekly = self.unit_cost * self.annual_holding_rate / 52.0

        # Simulation settings
        sim_cfg = self._raw_config.get("simulation", {})
        self.n_replications = sim_cfg.get("n_replications", 10000)
        self.random_seed = sim_cfg.get("random_seed", 42)
        self.initial_inventory_rule = sim_cfg.get("initial_inventory_rule", "match_target")
        self.backorder = sim_cfg.get("backorder", False)

        # Uncertainty settings
        uncertainty_cfg = self._raw_config.get("uncertainty", {})
        self.uncertainty_method = uncertainty_cfg.get("main_method", "ratio_bootstrap")
        self.ratio_cap = uncertainty_cfg.get("ratio_cap", "p1_p99")
        self.epsilon = float(uncertainty_cfg.get("epsilon", 1e-6))

        # Optimization settings
        opt_cfg = self._raw_config.get("optimization", {})
        self.optimization_method = opt_cfg.get("method", "two_stage_grid_search")
        self.safety_stock_max_sigma = opt_cfg.get("safety_stock_max_sigma", 4.0)
        self.local_search_max_rounds = opt_cfg.get("local_search_max_rounds", 100)
        self.local_search_threshold = opt_cfg.get("local_search_threshold", 1.3)

        # Columns
        self.columns = self._raw_config.get("columns", {
            "family": "family",
            "date": "date",
            "train_actual": "Actual_Sales",
            "train_fitted": "Fitted_Sales",
            "test_forecast": "forecast_sales"
        })

    def get_raw_config(self) -> dict:
        """Return the raw config dictionary."""
        return self._raw_config
