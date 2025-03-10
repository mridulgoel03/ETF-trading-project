import logging
from typing import Dict, Optional
from datetime import datetime
from .order_manager import OrderManager
from .queue_manager import QueueManager
from .solver import Solver
from .rebalance import RebalanceManager
from .reporting import ReportingSystem
from .binance_api import BinanceAPI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETFTradingSystem:
    def __init__(self):
        self.binance = BinanceAPI()
        self.order_manager = OrderManager()
        self.queue_manager = QueueManager()
        self.solver = Solver()
        self.rebalance_manager = RebalanceManager()
        self.reporting = ReportingSystem()
        
    def submit_order(self, order: Dict) -> Dict:
        """
        Submit a new order to the system
        """
        try:
            # Validate order
            self._validate_order(order)
            
            # Check if it's time for rebalancing
            if self._should_rebalance(order['indexId']):
                self._handle_rebalancing(order['indexId'])
            
            # Determine execution strategy
            strategy = self.solver.determine_fill_strategy(
                order,
                self.binance.get_liquidity_data(order['indexId'])
            )
            
            # Add to queue
            self.queue_manager.add_to_queue({
                **order,
                'strategy': strategy,
                'timestamp': datetime.now().timestamp()
            })
            
            return {
                'status': 'queued',
                'orderId': order['positionId'],
                'estimatedFill': strategy['fill_percentage']
            }
            
        except Exception as e:
            logger.error(f"Order submission failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def cancel_order(self, position_id: int) -> Dict:
        """
        Cancel an existing order
        """
        try:
            result = self.order_manager.cancel_order(position_id)
            self.reporting.record_cancellation(position_id, result)
            return {'status': 'cancelled', 'details': result}
        except Exception as e:
            logger.error(f"Cancel failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def get_fill_report(self, position_id: int) -> Dict:
        """
        Get fill report for a position
        """
        return self.reporting.get_fill_report(position_id)
    
    def get_rebalance_report(self, index_id: int) -> Dict:
        """
        Get rebalancing report for an index
        """
        return self.reporting.get_rebalance_report(index_id)
    
    def _validate_order(self, order: Dict) -> bool:
        """
        Validate order parameters
        """
        required_fields = ['action', 'positionId', 'indexId', 'quantity']
        if not all(field in order for field in required_fields):
            raise ValueError("Missing required order fields")
        
        if order['quantity'] <= 0:
            raise ValueError("Quantity must be positive")
            
        return True
    
    def _should_rebalance(self, index_id: int) -> bool:
        """
        Check if index needs rebalancing
        """
        return self.rebalance_manager.should_rebalance(index_id)
    
    def _handle_rebalancing(self, index_id: int) -> None:
        """
        Handle index rebalancing
        """
        try:
            rebalance_result = self.rebalance_manager.execute_rebalance(
                index_id,
                self.binance.get_index_data(index_id)
            )
            self.reporting.record_rebalance(index_id, rebalance_result)
        except Exception as e:
            logger.error(f"Rebalancing failed: {str(e)}")
            raise

    def process_queued_orders(self) -> None:
        """
        Process orders in the queue
        """
        while True:
            batch = self.queue_manager.get_next_batch()
            if not batch:
                break
                
            for order in batch:
                try:
                    result = self.order_manager.execute_order(order)
                    self.reporting.record_execution(order['positionId'], result)
                except Exception as e:
                    logger.error(f"Order execution failed: {str(e)}")
                    self.reporting.record_error(order['positionId'], str(e))

if __name__ == "__main__":
    system = ETFTradingSystem()
    # Add any initialization or test code here 