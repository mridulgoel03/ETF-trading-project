# Handles rebalancing logic 
from typing import Dict, List
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class RebalanceTarget:
    asset_id: str
    target_quantity: float
    current_quantity: float
    target_price: float
    current_price: float

class RebalanceManager:
    def __init__(self):
        self.rebalance_interval = timedelta(days=30)
        self.last_rebalance: Dict[int, datetime] = {}
        self.fee_rate = 0.001
        
    def calculate_new_weights(self, index_id: int, current_assets: List[dict]) -> Dict:
        """
        Calculate new asset weights after rebalancing
        Returns target quantities for each asset
        """
        total_value = sum(
            asset['quantity'] * asset['price_current'] 
            for asset in current_assets
        )
        
        targets = []
        for asset in current_assets:
            target = RebalanceTarget(
                asset_id=asset['asset_id'],
                target_quantity=self._calculate_target_quantity(
                    asset, total_value
                ),
                current_quantity=asset['quantity'],
                target_price=asset['price_current'],
                current_price=asset['price_current']
            )
            targets.append(target)
            
        return {
            'index_id': index_id,
            'total_value': total_value,
            'targets': targets
        }
    
    def _calculate_target_quantity(self, asset: dict, total_value: float) -> float:
        """Calculate target quantity for an asset during rebalancing"""
        target_weight = asset['target_weight']
        target_value = total_value * target_weight
        return target_value / asset['price_current']
    
    def execute_rebalance(
        self, 
        index_id: int, 
        current_assets: List[dict],
        liquidity_data: dict
    ) -> Dict:
        """Execute rebalancing transactions"""
        if not self._should_rebalance(index_id):
            return {'status': 'skipped', 'reason': 'Not time for rebalance'}
            
        rebalance_targets = self.calculate_new_weights(index_id, current_assets)
        
        trades = []
        total_cost = 0
        
        for target in rebalance_targets['targets']:
            quantity_diff = target.target_quantity - target.current_quantity
            
            if abs(quantity_diff) > 0:
                trade = {
                    'asset_id': target.asset_id,
                    'quantity': abs(quantity_diff),
                    'side': 'buy' if quantity_diff > 0 else 'sell',
                    'target_price': target.target_price
                }
                
                # Calculate trade cost including slippage
                cost = self._calculate_trade_cost(
                    trade,
                    liquidity_data.get(target.asset_id, {})
                )
                
                trades.append({**trade, 'estimated_cost': cost})
                total_cost += cost
                
        self.last_rebalance[index_id] = datetime.now()
        
        return {
            'status': 'executed',
            'trades': trades,
            'total_cost': total_cost,
            'timestamp': datetime.now().isoformat()
        }
    
    def _should_rebalance(self, index_id: int) -> bool:
        """Check if it's time to rebalance the index"""
        if index_id not in self.last_rebalance:
            return True
            
        time_since_last = datetime.now() - self.last_rebalance[index_id]
        return time_since_last >= self.rebalance_interval
    
    def _calculate_trade_cost(self, trade: dict, liquidity_data: dict) -> float:
        """Calculate the cost of a trade including fees and slippage"""
        orderbook = liquidity_data.get('orderbook', [])
        quantity = trade['quantity']
        target_price = trade['target_price']
        
        # Calculate slippage
        executed_value = 0
        remaining_qty = quantity
        
        for level in orderbook:
            if remaining_qty <= 0:
                break
                
            level_qty = min(remaining_qty, level['quantity'])
            executed_value += level_qty * level['price']
            remaining_qty -= level_qty
            
        if remaining_qty > 0:
            # Couldn't fill entire order in orderbook
            executed_value += remaining_qty * target_price
            
        avg_price = executed_value / quantity
        slippage_cost = abs(avg_price - target_price) * quantity
        fee_cost = executed_value * self.fee_rate
        
        return slippage_cost + fee_cost 