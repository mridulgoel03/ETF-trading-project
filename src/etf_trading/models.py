from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"    
    CANCEL = "CANCEL"
    REBALANCE = "REBALANCE" 

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Asset:
    symbol: str
    quantity: float
    price_last_rebalance: float
    current_price: float

@dataclass
class Index:
    id: str 
    assets: List[Asset]
    last_rebalance_time: datetime
    creation_time: datetime
    
    def calculate_nav(self) -> float:
        """Calculate the Net Asset Value of the index"""
        return sum(asset.quantity * asset.current_price for asset in self.assets)
    
    def calculate_rebalance_cost(self, new_weights: Dict[str, float]) -> float:
        """Calculate the cost of rebalancing to new weights"""
        current_nav = self.calculate_nav()
        total_cost = 0.0
                                  
        for asset in self.assets:
            new_weight = new_weights.get(asset.symbol, 0)
            target_value = current_nav * new_weight
            current_value = asset.quantity * asset.current_price
            diff_value = abs(target_value - current_value)
            # Assuming 0.1% trading fee
            total_cost += diff_value * 0.001
            
        return total_cost

@dataclass
class Order:
    position_id: int
    index_id: str
    order_type: OrderType
    quantity: float
    price: float
    timestamp: datetime
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    loss: float = 0.0

@dataclass
class CancelResult:
    success: bool
    message: str
    loss: float = 0.0

@dataclass
class FillReport:
    position_id: int
    fill_percentage: float
    loss: float
    timestamp: datetime

@dataclass
class RebalanceReport:
    index_id: str
    old_weights: Dict[str, float]
    new_weights: Dict[str, float]
    total_cost: float
    timestamp: datetime 