# Handles order queueing 
from typing import Dict, List, Optional
import time
import heapq
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class OrderPriority(Enum):
    REBALANCE = 1
    CANCEL = 2
    MARKET = 3
    LIMIT = 4

@dataclass
class QueueItem:
    timestamp: int
    priority: OrderPriority
    order: dict
    batch_id: Optional[int] = None
    
    def __lt__(self, other):
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp
        return self.priority.value < other.priority.value

class BatchManager:
    def __init__(self):
        self.current_batch: List[dict] = []
        self.current_batch_size = 0
        self.max_batch_size = 100  # Binance rate limit
        self.batch_window = 10  # seconds
        self.last_batch_time = time.time()

    def can_add_to_batch(self) -> bool:
        return self.current_batch_size < self.max_batch_size

    def add_to_batch(self, order: dict) -> bool:
        if not self.can_add_to_batch():
            return False
        self.current_batch.append(order)
        self.current_batch_size += 1
        return True

    def should_execute_batch(self) -> bool:
        return (time.time() - self.last_batch_time >= self.batch_window or 
                self.current_batch_size >= self.max_batch_size)

    def clear_batch(self) -> None:
        self.current_batch = []
        self.current_batch_size = 0
        self.last_batch_time = time.time()

class QueueManager:
    def __init__(self):
        self.order_queue: List[QueueItem] = []
        self.batch_manager = BatchManager()
        self.index_queues: Dict[int, List[QueueItem]] = {}
        
    def add_to_queue(self, order: dict) -> bool:
        """Add an order to the appropriate queue"""
        try:
            priority = self._determine_priority(order)
            queue_item = QueueItem(
                timestamp=order['timestamp'],
                priority=priority,
                order=order
            )
            
            # Add to main queue
            heapq.heappush(self.order_queue, queue_item)
            
            # Add to index-specific queue
            index_id = order.get('indexId')
            if index_id:
                if index_id not in self.index_queues:
                    self.index_queues[index_id] = []
                heapq.heappush(self.index_queues[index_id], queue_item)
                
            logger.info(f"Added order {order['positionId']} to queue with priority {priority}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add order to queue: {str(e)}")
            return False

    def _determine_priority(self, order: dict) -> OrderPriority:
        """Determine order priority based on type and conditions"""
        if order.get('action') == 'rebalance':
            return OrderPriority.REBALANCE
        elif order.get('action') == 'cancel':
            return OrderPriority.CANCEL
        elif order.get('orderType') == 'market':
            return OrderPriority.MARKET
        return OrderPriority.LIMIT

    def execute_batch(self) -> List[dict]:
        """Execute a batch of orders respecting rate limits"""
        if not self.batch_manager.should_execute_batch():
            return []

        executed_orders = []
        while (self.order_queue and 
               self.batch_manager.can_add_to_batch()):
            order_item = heapq.heappop(self.order_queue)
            if self.batch_manager.add_to_batch(order_item.order):
                executed_orders.append(order_item.order)

        # Process the batch
        if executed_orders:
            logger.info(f"Executing batch of {len(executed_orders)} orders")
            self.batch_manager.clear_batch()

        return executed_orders

    def get_index_queue(self, index_id: int) -> List[dict]:
        """Get all orders for a specific index"""
        return [item.order for item in self.index_queues.get(index_id, [])]

    def cleanup_old_orders(self, max_age: int = 3600) -> None:
        """Remove orders older than max_age seconds"""
        current_time = time.time()
        self.order_queue = [
            item for item in self.order_queue 
            if (current_time - item.timestamp) <= max_age
        ] 