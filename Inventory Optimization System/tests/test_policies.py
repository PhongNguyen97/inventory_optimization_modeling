"""
Unit Tests for Policies Module.
"""

import numpy as np
from src.policies import SQPolicy, RSPolicy


def test_sq_policy_static():
    policy = SQPolicy(reorder_point=100.0, order_quantity=50.0)
    
    # IP is above reorder point s -> order 0
    assert policy.order_quantity(110.0) == 0.0
    
    # IP is at reorder point s -> order Q
    assert policy.order_quantity(100.0) == 50.0
    
    # IP is below s -> order Q
    assert policy.order_quantity(80.0) == 50.0


def test_sq_policy_dynamic():
    s_array = np.array([100.0, 80.0, 120.0])
    policy = SQPolicy(reorder_point=s_array, order_quantity=50.0)
    
    # Week 0 (s = 100)
    assert policy.order_quantity(90.0, week_idx=0) == 50.0
    assert policy.order_quantity(110.0, week_idx=0) == 0.0
    
    # Week 1 (s = 80)
    assert policy.order_quantity(90.0, week_idx=1) == 0.0
    assert policy.order_quantity(75.0, week_idx=1) == 50.0
    
    # Week 2 (s = 120)
    assert policy.order_quantity(110.0, week_idx=2) == 50.0


def test_rs_policy_static():
    policy = RSPolicy(order_up_to_level=150.0)
    
    # IP is below order-up-to level S -> order S - IP
    assert policy.order_quantity(100.0) == 50.0
    
    # IP is above target S -> order 0
    assert policy.order_quantity(160.0) == 0.0
    
    # IP is at target S -> order 0
    assert policy.order_quantity(150.0) == 0.0


def test_rs_policy_dynamic():
    S_array = np.array([150.0, 120.0])
    policy = RSPolicy(order_up_to_level=S_array)
    
    # Week 0 (S = 150)
    assert policy.order_quantity(100.0, week_idx=0) == 50.0
    
    # Week 1 (S = 120)
    assert policy.order_quantity(100.0, week_idx=1) == 20.0
    assert policy.order_quantity(130.0, week_idx=1) == 0.0
