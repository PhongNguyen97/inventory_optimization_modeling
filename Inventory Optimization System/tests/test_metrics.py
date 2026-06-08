"""
Unit Tests for Metrics Module.
"""

import numpy as np
import pandas as pd
from src.metrics import (
    calculate_fill_rate,
    calculate_cycle_service_level,
    calculate_total_cost,
    calculate_average_inventory
)


def test_fill_rate_no_shortage():
    assert calculate_fill_rate(100.0, 0.0) == 1.0
    assert calculate_fill_rate(0.0, 0.0) == 1.0


def test_fill_rate_complete_shortage():
    assert calculate_fill_rate(100.0, 100.0) == 0.0
    assert calculate_fill_rate(50.0, 60.0) == 0.0 # clamped to 0


def test_fill_rate_normal():
    assert calculate_fill_rate(100.0, 10.0) == 0.90
    assert calculate_fill_rate(200.0, 50.0) == 0.75


def test_cycle_service_level():
    flags = np.array([0, 0, 0, 0]) # zero stockout weeks
    assert calculate_cycle_service_level(flags) == 1.0
    
    flags_with_shortage = np.array([1, 0, 0, 1]) # 2 stockout weeks out of 4
    assert calculate_cycle_service_level(flags_with_shortage) == 0.5


def test_total_cost():
    # Cost = H * Avg_Inv + K * Orders + B * Short
    # H = 0.1, Avg_Inv = 50, K = 25, Orders = 2, B = 15, Short = 10
    # Expected = 0.1*50 + 25*2 + 15*10 = 5 + 50 + 150 = 205
    cost = calculate_total_cost(
        holding_cost_rate=0.1,
        avg_inventory=50.0,
        order_cost=25.0,
        num_orders=2,
        shortage_cost=15.0,
        units_short=10.0
    )
    assert cost == 205.0


def test_average_inventory():
    history = np.array([10.0, 20.0, 30.0, 40.0])
    assert calculate_average_inventory(history) == 25.0
    assert calculate_average_inventory(np.array([])) == 0.0
