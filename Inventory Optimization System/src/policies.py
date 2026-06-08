"""
Policies Module for Inventory Optimization System.

Role:
  Defines inventory policy classes that encapsulate replenishment rules. 
  It implements continuous review (s,Q) policies where orders are triggered when
  inventory position falls below a reorder point, and periodic review (R,S) policies
  where orders raise the inventory position to an order-up-to level at review epochs.

Inputs:
  - Policy parameters: reorder point (s), order quantity (Q), or order-up-to level (S).
  - Current inventory position (IP).

Outputs:
  - Replenishment order quantity to place.
"""


import numpy as np
from typing import Union

class SQPolicy:
    """
    Continuous Review (s, Q) Policy.
    An order of fixed size Q is placed whenever the inventory position (IP)
    falls to or below the reorder point s.
    """

    def __init__(self, reorder_point: Union[float, np.ndarray], order_quantity: float):
        """
        Initialize the (s, Q) policy parameters.
        
        Inputs:
            reorder_point (float or np.ndarray): Reorder point (s) or array of reorder points by week.
            order_quantity (float): Order quantity (Q).
        """
        self.s = reorder_point
        self.Q = order_quantity

    def order_quantity(self, inventory_position: Union[float, np.ndarray], week_idx: int = None) -> Union[float, np.ndarray]:
        """
        Determine the order quantity based on continuous review.
        Supports both scalar (1D) and vectorized (2D) inputs.
        
        Inputs:
            inventory_position (float or np.ndarray): Current inventory position (On Hand + On Order - Backorders).
            week_idx (int, optional): Index of the current simulation week for dynamic parameters.
            
        Outputs:
            float or np.ndarray: Order quantity.
        """
        s_val = self.s
        if isinstance(self.s, np.ndarray) and week_idx is not None:
            s_val = self.s[week_idx]
            
        if isinstance(inventory_position, np.ndarray):
            order_mask = inventory_position <= s_val
            n = np.ceil((s_val - inventory_position) / self.Q)
            n = np.maximum(1, n)
            return np.where(order_mask, n * self.Q, 0.0)
            
        if inventory_position <= s_val:
            # Calculate how many multiples of Q are needed to raise IP above s
            n = int(np.ceil((s_val - inventory_position) / self.Q))
            # Ensure we order at least one Q
            n = max(1, n)
            return n * self.Q
        return 0.0

    def __repr__(self) -> str:
        if isinstance(self.s, np.ndarray):
            return f"SQPolicy(s=[dynamic], Q={self.Q:.2f})"
        return f"SQPolicy(s={self.s:.2f}, Q={self.Q:.2f})"


class RSPolicy:
    """
    Periodic Review (R, S) Policy.
    At each review epoch (every R weeks), a variable order is placed to raise
    the inventory position (IP) back up to the target level S.
    """

    def __init__(self, order_up_to_level: Union[float, np.ndarray]):
        """
        Initialize the (R, S) policy parameters.
        
        Inputs:
            order_up_to_level (float or np.ndarray): Order-up-to level (S) or array of levels by week.
        """
        self.S = order_up_to_level

    def order_quantity(self, inventory_position: Union[float, np.ndarray], week_idx: int = None) -> Union[float, np.ndarray]:
        """
        Determine the order quantity to raise inventory position up to S.
        Supports both scalar (1D) and vectorized (2D) inputs.
        
        Inputs:
            inventory_position (float or np.ndarray): Current inventory position.
            week_idx (int, optional): Index of the current simulation week for dynamic parameters.
            
        Outputs:
            float or np.ndarray: Replenishment order size.
        """
        S_val = self.S
        if isinstance(self.S, np.ndarray) and week_idx is not None:
            S_val = self.S[week_idx]
            
        if isinstance(inventory_position, np.ndarray):
            return np.maximum(0.0, S_val - inventory_position)
            
        return max(0.0, S_val - inventory_position)

    def __repr__(self) -> str:
        if isinstance(self.S, np.ndarray):
            return "RSPolicy(S=[dynamic])"
        return f"RSPolicy(S={self.S:.2f})"

