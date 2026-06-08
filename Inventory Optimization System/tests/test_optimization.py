"""
Unit Tests for Optimization Module.
"""

import numpy as np
from src.simulation import InventorySimulator
from src.optimization import GridSearchOptimizer, calculate_eoq


def test_calculate_eoq():
    # EOQ = sqrt((2 * K * D) / H)
    # K = 25.0, D = 100.0, H = 0.5
    # Expected = sqrt((2 * 25 * 100) / 0.5) = sqrt(5000 / 0.5) = sqrt(10000) = 100.0
    eoq = calculate_eoq(order_cost=25.0, weekly_demand=100.0, holding_cost=0.5)
    assert eoq == 100.0


def test_grid_search_feasibility_filtering():
    """
    Test that candidates failing the service level target (fill rate >= 0.95)
    are filtered out, and the lowest cost feasible candidate is selected.
    """
    # Create 3 demand paths of 3 weeks where demand is constant at 100
    demand_paths = np.ones((3, 3)) * 100.0
    
    # Setup simulator: H_weekly = 0.1, K = 25.0, B = 1000.0 (very high shortage cost to penalize stockouts)
    sim = InventorySimulator(
        lead_time=1,
        holding_cost=0.1,
        order_cost=25.0,
        shortage_cost=1000.0,
        backorder=False
    )
    
    optimizer = GridSearchOptimizer(sim, target_fill_rate=0.95)
    
    # We test two safety stock values:
    #   ss = 0.0 -> s = 100 -> policy is SQPolicy(100, 100). Realized fill rate = 1.0 (feasible)
    #   ss = -50.0 -> s = 50 -> policy is SQPolicy(50, 100).
    #     At week 0, demand is 100. Inventory drops to 0. IP = 0 <= s (50) -> order 100.
    #     Wait, initial inventory is 50. Demand is 100. Satisfied = 50, Shortage = 50.
    #     Fill rate is 50/100 = 0.50 (infeasible, rejected!)
    # We set expected lead time demand as 100.0
    expected_ltd = 100.0
    
    ss_grid = np.array([-50.0, 0.0]) # ss=-50 is s=50 (infeasible), ss=0 is s=100 (feasible)
    q_grid = np.array([100.0])
    
    best_ss, best_q, best_s, metrics = optimizer.optimize_sq(
        demand_paths=demand_paths,
        ss_grid=ss_grid,
        q_grid=q_grid,
        expected_lead_time_demand=expected_ltd
    )
    
    # Assertions
    # It must select ss = 0.0 (which is feasible) over ss = -50.0 (which fails service level)
    assert best_ss == 0.0
    assert best_q == 100.0
    assert best_s == 100.0
    assert metrics["fill_rate"] == 1.0
