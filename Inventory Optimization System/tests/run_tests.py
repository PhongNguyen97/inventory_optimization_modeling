"""
Test runner script to execute all unit tests.
This script is used to verify implementation correctness without requiring external test runners.
"""

import sys
import os

# Add the project root and src directory to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import test functions
from tests.test_metrics import (
    test_fill_rate_no_shortage,
    test_fill_rate_complete_shortage,
    test_fill_rate_normal,
    test_cycle_service_level,
    test_total_cost,
    test_average_inventory
)
from tests.test_policies import (
    test_sq_policy_static,
    test_sq_policy_dynamic,
    test_rs_policy_static,
    test_rs_policy_dynamic
)
from tests.test_simulation import (
    test_constant_demand_sq_policy,
    test_constant_demand_rs_policy
)
from tests.test_optimization import (
    test_calculate_eoq,
    test_grid_search_feasibility_filtering
)


def run_all_tests():
    print("==================================================")
    print("Running Inventory Optimization Project Unit Tests")
    print("==================================================")
    
    test_funcs = [
        test_fill_rate_no_shortage,
        test_fill_rate_complete_shortage,
        test_fill_rate_normal,
        test_cycle_service_level,
        test_total_cost,
        test_average_inventory,
        test_sq_policy_static,
        test_sq_policy_dynamic,
        test_rs_policy_static,
        test_rs_policy_dynamic,
        test_constant_demand_sq_policy,
        test_constant_demand_rs_policy,
        test_calculate_eoq,
        test_grid_search_feasibility_filtering
    ]
    
    passed = 0
    failed = 0
    
    for func in test_funcs:
        try:
            print(f"Running {func.__name__:45} ... ", end="")
            func()
            print("PASSED")
            passed += 1
        except AssertionError as e:
            print("FAILED (AssertionError)")
            import traceback
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print("FAILED (Exception)")
            import traceback
            traceback.print_exc()
            failed += 1
            
    print("==================================================")
    print(f"Test Summary: {passed} passed, {failed} failed.")
    print("==================================================")
    
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_all_tests()
