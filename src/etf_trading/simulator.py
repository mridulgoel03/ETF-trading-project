from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import deque
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.etf_trading.models import (
    Order, Index, Asset, OrderType, OrderStatus,
    CancelResult, FillReport, RebalanceReport
)   

class TradingSimulator:
    def __init__(self):
        self.indices: Dict[str, Index] = {}
        self.orders: Dict[int, Order] = {}
        self.order_queue = deque()
        self.rate_limit_window = 10  # seconds
        self.rate_limit_orders = 100  # orders per window
        self.min_order_value = 5.0  # minimum $5 per asset
        self.last_execution_time = datetime.now()
        self.order_count_in_window = 0
        self.liquidity_info: Dict[str, Dict[str, Dict]] = {}
        self.retainer: Dict[str, float] = {}

    def set_liquidity_info(self, index_id: str, liquidity_info: Dict[str, Dict]):
        """Set liquidity constraints for an index's assets"""
        self.liquidity_info[index_id] = liquidity_info

    def update_prices(self, index_id: str, prices: Dict[str, float]):
        """Update current prices for assets in an index"""
        if index_id not in self.indices:
            raise ValueError("Index not found")

        index = self.indices[index_id]
        for asset in index.assets:
            if asset.symbol in prices:
                asset.current_price = prices[asset.symbol]

    def get_index(self, index_id: str) -> Optional[Index]:
        """Get index by ID"""
        return self.indices.get(index_id)
    def create_index(self, index_id: str, assets: List[Tuple[str, float, float, float]]) -> Index:
        """Create a new index with initial assets"""
        now = datetime.now()
        index_assets = [
            Asset(symbol=symbol, quantity=qty, price_last_rebalance=p0, current_price=p)
            for symbol, qty, p0, p in assets
        ]
        index = Index(
            id=index_id,
            assets=index_assets,
            last_rebalance_time=now,
            creation_time=now
        )
        self.indices[index_id] = index
        self.retainer[index_id] = 0.0
        return index

    def _check_rate_limit(self) -> bool:
        """Check if we've hit the rate limit"""
        now = datetime.now()
        time_diff = now - self.last_execution_time

        # Reset counter if full window has passed
        if time_diff > timedelta(seconds=self.rate_limit_window):
            self.order_count_in_window = 0
            self.last_execution_time = now

        # If limit exceeded, return False
        if self.order_count_in_window >= self.rate_limit_orders:
            return False

        self.order_count_in_window += 1
        return True

    def get_rate_limited_orders(self) -> List[Order]:
        """Get list of orders that were rate-limited"""
        return [
            order for order in self.orders.values()
            if order.status == OrderStatus.REJECTED  # Ensure rejected orders are tracked
        ]

    def _calculate_fillable_amount(self, index_id: str, quantity: float) -> float:
        """Calculate fillable amount based on liquidity constraints"""
        if index_id not in self.liquidity_info:
            return quantity

        index = self.indices[index_id]
        liquidity_info = self.liquidity_info[index_id]
        
        # Find the most constraining asset
        min_fill_percentage = 1.0
        for asset in index.assets:
            if asset.symbol not in liquidity_info:
                continue
                
            asset_info = liquidity_info[asset.symbol]
            asset_notional = quantity * asset.current_price * asset.quantity
            if asset_notional > asset_info['max_fillable']:
                fill_percentage = asset_info['max_fillable'] / asset_notional
                min_fill_percentage = min(min_fill_percentage, fill_percentage)
        
        return quantity * min_fill_percentage

    def buy(self, position_id: int, index_id: str, quantity: float, index_price: float) -> Order:
        """Create a buy order for an index"""
    
        if quantity <= 0:
            order = Order(
                position_id=position_id,
                index_id=index_id,
                order_type=OrderType.BUY,
                quantity=quantity,
                price=index_price,
                timestamp=datetime.now(),
                status=OrderStatus.REJECTED
            )
            self.orders[position_id] = order
            return order

        # ✅ Reject orders if rate limit is exceeded
        if not self._check_rate_limit():
            order = Order(
                position_id=position_id,
                index_id=index_id,
                order_type=OrderType.BUY,
                quantity=quantity,
                price=index_price,
                timestamp=datetime.now(),
                status=OrderStatus.REJECTED
            )
            self.orders[position_id] = order
            return order

        order = Order(
            position_id=position_id,
            index_id=index_id,
            order_type=OrderType.BUY,
            quantity=quantity,
            price=index_price,
            timestamp=datetime.now(),
            status=OrderStatus.PENDING
        )

        self.orders[position_id] = order
        self.order_queue.append(order)  # Ensure the order is added to the queue
        print(f"Order added to queue: {order}")  # Debug statement
        return order

    def get_fill_report(self, position_id: int) -> Optional[FillReport]:
        """Get fill report for an order"""
        order = self.orders.get(position_id)
        if not order:
            return None
            
        return FillReport(
            position_id=position_id,
            fill_percentage=(order.filled_quantity / order.quantity * 100),
            loss=order.loss,
            timestamp=datetime.now()
        )

    def cancel(self, position_id: int) -> CancelResult:
        """Cancel an existing order"""
        if position_id not in self.orders:
            return CancelResult(success=False, message="Order not found")

        order = self.orders[position_id]
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return CancelResult(
                success=False,
                message=f"Order already {order.status.value}"
            )

        # Calculate potential loss for partially filled orders
        loss = 0.0
        if order.status == OrderStatus.PARTIALLY_FILLED:
            loss = abs(order.filled_quantity * (order.price - order.filled_price))

        order.status = OrderStatus.CANCELLED
        return CancelResult(success=True, message="Order cancelled", loss=loss)

    def get_order(self, position_id: int) -> Optional[Order]:
        """Retrieve an order by position ID"""
        return self.orders.get(position_id)

    def process_queue(self) -> None:
        """Process the order queue with batch execution and liquidity-based priority"""
        if not self.order_queue:
            print("Order queue is empty.")  # Debug statement
            return

        # Calculate how many orders we can process in this window
        now = datetime.now()
        time_diff = now - self.last_execution_time

        if time_diff > timedelta(seconds=self.rate_limit_window):
            self.order_count_in_window = 0
            self.last_execution_time = now

        available_slots = max(0, self.rate_limit_orders - self.order_count_in_window)

        # Collect all orders for processing
        all_orders = list(self.order_queue)
        self.order_queue.clear()

        # Sort orders by liquidity impact
        orders_with_impact = []
        for order in all_orders:
            index = self.indices[order.index_id]
            liquidity_info = self.liquidity_info.get(order.index_id, {})

            liquidity_impact = sum(
                (liquidity_info.get(asset.symbol, {}).get('price_impact', 0) * asset.current_price)
                for asset in index.assets
            )
            orders_with_impact.append((liquidity_impact, order))

        # Sort by liquidity impact (lowest first)
        orders_with_impact.sort(key=lambda x: x[0])

        executed_orders = []
        remaining_orders = []

        # Process orders up to rate limit
        for i, (_, order) in enumerate(orders_with_impact):
            if i < available_slots:
                self._execute_order(order)
                executed_orders.append(order)
                self.order_count_in_window += 1
            else:
                # Mark as rejected if beyond rate limit
                order.status = OrderStatus.PENDING
                remaining_orders.append(order)

        # Ensure unexecuted or rejected orders stay in queue
        for order in remaining_orders:
            if order.status == OrderStatus.PENDING or order.status == OrderStatus.REJECTED:
                self.order_queue.append(order)

        print(f"Processed orders: {executed_orders}")  # Debug statement
        print(f"Remaining orders in queue: {self.order_queue}")  # Debug statement

    def _execute_order(self, order: Order) -> None:
        """Execute a single order"""
        if order.order_type == OrderType.BUY:
            # Check rate limit first
            if self.order_count_in_window >= self.rate_limit_orders:
                order.status = OrderStatus.REJECTED
                return
            
            fillable_quantity = self._calculate_fillable_amount(
                order.index_id,
                order.quantity
            )
            
            fill_rate = fillable_quantity / order.quantity
            order.filled_quantity = fillable_quantity
            order.filled_price = order.price * (1 + 0.001)  # 0.1% slippage
            
            if fill_rate >= 0.99:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIALLY_FILLED
            
            order.loss = abs(order.filled_quantity * (order.price - order.filled_price))

            # Update retainer
            index = self.indices[order.index_id]
            filled_value = order.filled_quantity * order.filled_price
            self.retainer[order.index_id] += (
                order.quantity * order.price - filled_value
            )

    def rebalance(self, index_id: str, new_weights: Dict[str, float]) -> RebalanceReport:
        """Rebalance an index to new weights"""
        if index_id not in self.indices:
            raise ValueError("Index not found")

        index = self.indices[index_id]
        old_weights = {
            asset.symbol: (asset.quantity * asset.current_price) / index.calculate_nav()
            for asset in index.assets
        }
        
        total_cost = index.calculate_rebalance_cost(new_weights)
        
        # Update the index with new weights
        nav = index.calculate_nav()
        for asset in index.assets:
            if asset.symbol in new_weights:
                new_weight = new_weights[asset.symbol]
                target_value = nav * new_weight
                asset.quantity = target_value / asset.current_price
                asset.price_last_rebalance = asset.current_price

        index.last_rebalance_time = datetime.now()
        
        return RebalanceReport(
            index_id=index_id,
            old_weights=old_weights,
            new_weights=new_weights,
            total_cost=total_cost,
            timestamp=datetime.now()
        ) 
