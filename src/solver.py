from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class AssetPosition:
    asset_id: str
    quantity: float
    price_initial: float
    price_current: float
    
    @property
    def value(self) -> float:
        return self.quantity * self.price_current

class Solver:
    def __init__(self):
        self.fee_rate = 0.001  # 0.1% fee
        self.min_asset_value = 5  # $5 minimum per asset on Binance
        
    def calculate_index_price(self, assets: List[AssetPosition]) -> float:
        """Calculate current index price based on constituent assets"""
        return sum(asset.value for asset in assets)
        
    def determine_fill_strategy(self, order: dict, liquidity_data: dict) -> Dict:
        """
        Determine optimal fill strategy for an order considering liquidity constraints
        Returns fill quantities for each asset
        """
        index_assets = order['assets']
        total_fillable_pct = float('inf')
        
        # Find the limiting asset based on liquidity
        asset_fill_pcts = {}
        for asset in index_assets:
            asset_id = asset['assetId']
            required_qty = asset['quantity'] * order['quantity']
            
            # Get available liquidity for this asset
            available_liquidity = liquidity_data.get(asset_id, {}).get('orderbook', [])
            fillable_qty = self._calculate_fillable_quantity(
                available_liquidity,
                required_qty,
                order['indexPrice']
            )
            
            fill_pct = fillable_qty / required_qty
            asset_fill_pcts[asset_id] = fill_pct
            total_fillable_pct = min(total_fillable_pct, fill_pct)
        
        # Calculate fills using the minimum fill percentage
        return {
            'fill_percentage': total_fillable_pct,
            'asset_fills': {
                asset_id: {
                    'quantity': index_assets[i]['quantity'] * order['quantity'] * total_fillable_pct,
                    'expected_price': self._estimate_fill_price(
                        liquidity_data[asset_id]['orderbook'],
                        index_assets[i]['quantity'] * order['quantity'] * total_fillable_pct
                    )
                }
                for i, asset_id in enumerate(asset_fill_pcts.keys())
            }
        }
    
    def _calculate_fillable_quantity(
        self, 
        orderbook: List[dict], 
        required_qty: float,
        limit_price: float
    ) -> float:
        """Calculate how much can be filled given orderbook depth"""
        fillable_qty = 0
        for level in orderbook:
            if level['price'] > limit_price:
                break
            fillable_qty += level['quantity']
        return min(fillable_qty, required_qty)
    
    def _estimate_fill_price(self, orderbook: List[dict], quantity: float) -> float:
        """Estimate average fill price for a given quantity"""
        remaining_qty = quantity
        total_cost = 0
        
        for level in orderbook:
            level_qty = min(remaining_qty, level['quantity'])
            total_cost += level_qty * level['price']
            remaining_qty -= level_qty
            
            if remaining_qty <= 0:
                break
                
        return total_cost / quantity if quantity > 0 else 0
    
    def match_buy_sell_orders(
        self, 
        buy_orders: List[dict], 
        sell_orders: List[dict]
    ) -> List[Tuple[dict, dict]]:
        """Match internal buy and sell orders to avoid unnecessary market trades"""
        matches = []
        
        # Sort orders by price (best prices first)
        buy_orders = sorted(buy_orders, key=lambda x: x['indexPrice'], reverse=True)
        sell_orders = sorted(sell_orders, key=lambda x: x['indexPrice'])
        
        for buy in buy_orders:
            for sell in sell_orders:
                if sell['quantity'] == 0:
                    continue
                    
                if buy['indexPrice'] >= sell['indexPrice']:
                    match_qty = min(buy['quantity'], sell['quantity'])
                    matches.append((
                        {**buy, 'quantity': match_qty},
                        {**sell, 'quantity': match_qty}
                    ))
                    
                    buy['quantity'] -= match_qty
                    sell['quantity'] -= match_qty
                    
                    if buy['quantity'] == 0:
                        break
                        
        return matches 