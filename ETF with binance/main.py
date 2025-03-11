# Entry point for the system 
import json
from src.order_book import OrderBook
from src.liquidity_manager import LiquidityManager
import logging
from typing import List, Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETFTradingSystem:
    def __init__(self):
        self.order_book = OrderBook()
        self.liquidity_manager = LiquidityManager()
        self.orders_data = []
        
    def load_test_data(self, file_path: str = "data/fake_orders.json") -> None:
        """Load test orders from JSON file"""
        try:
            with open(file_path, 'r') as f:
                self.orders_data = json.load(f)
            logger.info(f"Successfully loaded {len(self.orders_data)} orders from {file_path}")
        except Exception as e:
            logger.error(f"Error loading test data: {str(e)}")
            raise

    def test_order_submission(self) -> None:
        """Test submitting various orders"""
        logger.info("Testing order submission...")
        
        for order in self.orders_data[:3]:  # Test first 3 orders
            success = self.order_book.add_order(order)
            logger.info(f"Order {order['positionId']} submission: {'Success' if success else 'Failed'}")
            
            # Check liquidity for the order
            if order['action'] in ['buy', 'sell']:
                fillable_quantity = self.liquidity_manager.check_liquidity(
                    order['indexId'],
                    order['quantity']
                )
                logger.info(f"Fillable quantity for order {order['positionId']}: {fillable_quantity}")

    def test_large_order_handling(self) -> None:
        """Test handling of large orders"""
        logger.info("Testing large order handling...")
        
        large_order = {
            "timestamp": 1012,
            "action": "buy",
            "positionId": 100,
            "indexId": 1,
            "quantity": 100000,
            "indexPrice": 1025.50
        }
        
        # Check liquidity before submission
        fillable_qty = self.liquidity_manager.check_liquidity(
            large_order['indexId'],
            large_order['quantity']
        )
        logger.info(f"Large order fillable quantity: {fillable_qty}")
        
        # Apply slippage
        adjusted_order = self.liquidity_manager.apply_slippage(large_order)
        logger.info(f"Original price: {large_order['indexPrice']}")
        logger.info(f"Adjusted price: {adjusted_order['executionPrice']}")

    def test_order_cancellation(self) -> None:
        """Test order cancellation functionality"""
        logger.info("Testing order cancellation...")
        
        # Add test order
        test_order = {
            "timestamp": 1013,
            "action": "buy",
            "positionId": 101,
            "indexId": 1,
            "quantity": 100,
            "indexPrice": 1020.50
        }
        
        # Add and then cancel the order
        self.order_book.add_order(test_order)
        logger.info(f"Orders for index 1 before cancellation: {len(self.order_book.get_orders(1))}")
        
        success = self.order_book.cancel_order(101)
        logger.info(f"Cancellation of order 101: {'Success' if success else 'Failed'}")
        logger.info(f"Orders for index 1 after cancellation: {len(self.order_book.get_orders(1))}")

    def test_rate_limits(self) -> None:
        """Test handling of rate limits"""
        logger.info("Testing rate limit handling...")
        
        # Create multiple orders with same timestamp
        rate_limit_orders = [
            {
                "timestamp": 1014,
                "action": "buy",
                "positionId": i,
                "indexId": 1,
                "quantity": 100,
                "indexPrice": 1020.50
            } for i in range(102, 105)  # 3 orders
        ]
        
        for order in rate_limit_orders:
            self.order_book.add_order(order)
            
        # Get all orders for index 1 at timestamp 1014
        orders = self.order_book.get_orders(1)
        same_timestamp_orders = [o for o in orders if o['timestamp'] == 1014]
        logger.info(f"Number of orders at timestamp 1014: {len(same_timestamp_orders)}")

    def run_all_tests(self) -> None:
        """Run all test scenarios"""
        try:
            self.load_test_data()
            
            # Run all test scenarios
            self.test_order_submission()
            self.test_large_order_handling()
            self.test_order_cancellation()
            self.test_rate_limits()
            
            logger.info("All tests completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during test execution: {str(e)}")
            raise

def main():
    # Create instance of trading system
    trading_system = ETFTradingSystem()
    
    # Run all tests
    trading_system.run_all_tests()

if __name__ == "__main__":
    main() 