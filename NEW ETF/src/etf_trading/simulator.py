from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import deque
from .models import (
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

    def create_index(self, index_id: str, assets: List[Tuple[str, float, float]]) -> Index:
        """Create a new index with initial assets"""
        now = datetime.now()
        index_assets = [
            Asset(symbol=symbol, quantity=qty, price_last_rebalance=price, current_price=price)
            for symbol, qty, price in assets
        ]
        index = Index(
            id=index_id,
            assets=index_assets,
            last_rebalance_time=now,
            creation_time=now
        )
        self.indices[index_id] = index
        return index

    def _check_rate_limit(self) -> bool:
        """Check if we've hit the rate limit"""
        now = datetime.now()
        if (now - self.last_execution_time) > timedelta(seconds=self.rate_limit_window):
            self.order_count_in_window = 0
            self.last_execution_time = now
        
        if self.order_count_in_window >= self.rate_limit_orders:
            return False
        
        self.order_count_in_window += 1
        return True

    def buy(self, position_id: int, index_id: str, quantity: float, index_price: float) -> Order:
        """Create a buy order for an index"""
        if quantity <= 0:
            return Order(
                position_id=position_id,
                index_id=index_id,
                order_type=OrderType.BUY,
                quantity=quantity,
                price=index_price,
                timestamp=datetime.now(),
                status=OrderStatus.REJECTED
            )

        if not self._check_rate_limit():
            return Order(
                position_id=position_id,
                index_id=index_id,
                order_type=OrderType.BUY,
                quantity=quantity,
                price=index_price,
                timestamp=datetime.now(),
                status=OrderStatus.REJECTED
            )

        order = Order(
            position_id=position_id,
            index_id=index_id,
            order_type=OrderType.BUY,
            quantity=quantity,
            price=index_price,
            timestamp=datetime.now()
        )
        
        self.orders[position_id] = order
        self.order_queue.append(order)
        return order

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

    def get_rate_limited_orders(self) -> List[Order]:
        """Get list of orders that were rate limited"""
        return [
            order for order in self.orders.values()
            if order.status == OrderStatus.REJECTED
        ]

    def process_queue(self) -> None:
        """Process the order queue"""
        while self.order_queue and self._check_rate_limit():
            order = self.order_queue.popleft()
            self._execute_order(order)

    def _execute_order(self, order: Order) -> None:
        """Simulate order execution"""
        if order.order_type == OrderType.BUY:
            # Simulate partial fills and slippage
            fill_rate = min(1.0, 0.8 + (0.2 * (1000 / order.quantity)))  # Larger orders get worse fills
            order.filled_quantity = order.quantity * fill_rate
            order.filled_price = order.price * (1 + 0.001)  # 0.1% slippage
            order.status = (
                OrderStatus.FILLED if fill_rate == 1.0
                else OrderStatus.PARTIALLY_FILLED
            )
            order.loss = abs(order.filled_quantity * (order.price - order.filled_price))

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