"""
Unit Tests for Simulation Module.
"""

import numpy as np
from src.simulation import InventorySimulator
from src.policies import SQPolicy, RSPolicy


def test_constant_demand_sq_policy():
    """
    Test continuous review SQPolicy with simple constant demand.
    Scenario:
      - Demand = 100 every week
      - L = 1
      - s = 100, Q = 100
      - Initial Inventory = 100
      
    Expected:
      - Placed order of 100 at every week's end
      - Incoming orders arrive on-time
      - Zero shortages, realized fill rate = 1.0
      - Average inventory = 0 (since it drops to 0 at the end of each week after satisfying demand)
    """
    demand_path = np.array([100.0, 100.0, 100.0, 100.0, 100.0])
    policy = SQPolicy(reorder_point=100.0, order_quantity=100.0)
    
    # H_weekly = 0.1, K = 25.0, B = 15.0
    sim = InventorySimulator(
        lead_time=1,
        holding_cost=0.1,
        order_cost=25.0,
        shortage_cost=15.0,
        backorder=False
    )
    
    res = sim.simulate(demand_path, policy, initial_inventory=100.0)
    
    # Assertions
    assert res["fill_rate"] == 1.0
    assert res["units_short"] == 0.0
    assert res["num_orders"] == 5 # places an order in week 0, 1, 2, 3, 4
    
    # Check physical inventory drops to 0 at end of each week
    np.testing.assert_array_equal(res["on_hand_end"], np.zeros(5))
    
    # Check inventory position returns to 100 at the end of every week (after placing order)
    np.testing.assert_array_equal(res["inventory_position"], np.ones(5) * 100.0)
    
    # Check order quantities placed each week are 100
    np.testing.assert_array_equal(res["orders_placed_history"], np.ones(5) * 100.0)


def test_constant_demand_rs_policy():
    """
    Test periodic review RSPolicy with simple constant demand.
    Scenario:
      - Demand = 100 every week
      - L = 1, R = 1 -> Risk period = 2 weeks
      - S = 200 (expected risk demand = 200, safety stock = 0)
      - Initial Inventory = 200
      
    Expected:
      - Placed order of 100 at every week's end (raising IP from 100 to 200)
      - Zero shortages, realized fill rate = 1.0
      - Ending physical inventory is 100 at each week's end
      - Average inventory = 100
    """
    demand_path = np.array([100.0, 100.0, 100.0, 100.0])
    policy = RSPolicy(order_up_to_level=200.0)
    
    sim = InventorySimulator(
        lead_time=1,
        holding_cost=0.1,
        order_cost=25.0,
        shortage_cost=15.0,
        backorder=False
    )
    
    res = sim.simulate(demand_path, policy, initial_inventory=200.0)
    
    # Assertions
    assert res["fill_rate"] == 1.0
    assert res["units_short"] == 0.0
    assert res["num_orders"] == 4
    
    # On-hand at week's end should be 100 (200 start + 0 arrived - 100 demand)
    np.testing.assert_array_equal(res["on_hand_end"], np.ones(4) * 100.0)
    
    # IP at week's end should be raised back to 200 after ordering
    np.testing.assert_array_equal(res["inventory_position"], np.ones(4) * 200.0)
    
    # Placed orders should be 100 each week to raise from 100 to 200
    np.testing.assert_array_equal(res["orders_placed_history"], np.ones(4) * 100.0)
    assert res["avg_inventory"] == 100.0
