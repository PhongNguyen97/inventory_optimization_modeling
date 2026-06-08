"""
Data Loader Module for Inventory Optimization System.

Role:
  Loads historical sales, fitted forecasts, and future test forecasts from raw CSV files.
  Applies filtering to focus on selected product families, checks data completeness and columns,
  and performs weekly date alignment checks to guarantee consistent timelines.

Inputs:
  - File paths to input CSV files.
  - Configuration settings for column mappings and selected product families.

Outputs:
  - Cleaned, filtered, and aligned pandas DataFrames for training and testing.
"""

import os
import pandas as pd
from typing import List
from src.config import Config


def load_train_data(path: str, config: Config) -> pd.DataFrame:
    """
    Load the historical training dataset containing actual and fitted sales.
    
    Inputs:
        path (str): File path to actual_fitted_sales_on_train_final.csv
        config (Config): Configuration object containing column mappings.
        
    Outputs:
        pd.DataFrame: Cleaned training dataset.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Training data file not found at: {path}")
        
    df = pd.read_csv(path)
    
    # Extract expected column names from config
    col_date = config.columns.get("date", "date")
    col_family = config.columns.get("family", "family")
    col_actual = config.columns.get("train_actual", "Actual_Sales")
    col_fitted = config.columns.get("train_fitted", "Fitted_Sales")
    
    # Basic validation of columns
    required_cols = [col_date, col_family, col_actual, col_fitted]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Training data is missing columns: {missing_cols}")
        
    # Convert date column to datetime
    df[col_date] = pd.to_datetime(df[col_date])
    
    # Sort chronologically by date
    df = df.sort_values(by=[col_family, col_date]).reset_index(drop=True)
    return df


def load_test_data(path: str, config: Config) -> pd.DataFrame:
    """
    Load the test dataset containing future forecast sales.
    
    Inputs:
        path (str): File path to actual_fitted_sales_on_test_final.csv
        config (Config): Configuration object containing column mappings.
        
    Outputs:
        pd.DataFrame: Cleaned test dataset.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Test data file not found at: {path}")
        
    df = pd.read_csv(path)
    
    # Extract expected column names from config
    col_date = config.columns.get("date", "date")
    col_family = config.columns.get("family", "family")
    col_forecast = config.columns.get("test_forecast", "forecast_sales")
    
    # Basic validation of columns
    required_cols = [col_date, col_family, col_forecast]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Test data is missing columns: {missing_cols}")
        
    # Convert date column to datetime
    df[col_date] = pd.to_datetime(df[col_date])
    
    # Sort chronologically by date
    df = df.sort_values(by=[col_family, col_date]).reset_index(drop=True)
    return df


def filter_families(df: pd.DataFrame, families: List[str], config: Config) -> pd.DataFrame:
    """
    Filter a DataFrame to contain only the selected product families.
    
    Inputs:
        df (pd.DataFrame): Input DataFrame.
        families (List[str]): List of product families to retain.
        config (Config): Configuration object containing column mappings.
        
    Outputs:
        pd.DataFrame: Filtered DataFrame.
    """
    col_family = config.columns.get("family", "family")
    if col_family not in df.columns:
        raise ValueError(f"Family column '{col_family}' not found in DataFrame.")
        
    return df[df[col_family].isin(families)].copy().reset_index(drop=True)


def validate_weekly_alignment(train_df: pd.DataFrame, config: Config) -> bool:
    """
    Validate that all weeks are aligned properly (e.g., they fall on Sundays) and 
    there are no gaps or duplicates in the time series for each family.
    
    Inputs:
        train_df (pd.DataFrame): Training DataFrame containing historical actual and fitted sales.
        config (Config): Configuration object.
        
    Outputs:
        bool: True if validation passes, raises ValueError otherwise.
    """
    col_date = config.columns.get("date", "date")
    col_family = config.columns.get("family", "family")
    
    # Check that date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(train_df[col_date]):
        train_df[col_date] = pd.to_datetime(train_df[col_date])
        
    # Check if dates fall on the same day of the week (Sunday is weekday 6 in pandas)
    weekdays = train_df[col_date].dt.weekday.unique()
    if len(weekdays) > 1:
        raise ValueError(f"Data contains mixed weekdays: {weekdays}. It should be weekly aligned.")
        
    # Check completeness and alignment per family
    for family, group in train_df.groupby(col_family):
        # Check for duplicate dates
        if group[col_date].duplicated().any():
            duplicates = group[group[col_date].duplicated()][col_date].tolist()
            raise ValueError(f"Duplicate dates found for family {family}: {duplicates}")
            
        # Check spacing is exactly 7 days
        sorted_dates = group[col_date].sort_values()
        date_diffs = sorted_dates.diff().dropna()
        non_7_day_diffs = date_diffs[date_diffs != pd.Timedelta(days=7)]
        if not non_7_day_diffs.empty:
            raise ValueError(f"Gaps or non-weekly spacing detected in time-series for family {family}: {non_7_day_diffs}")
            
    return True
