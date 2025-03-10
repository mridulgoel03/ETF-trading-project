import argparse
import logging
from typing import Dict, Optional
from datetime import datetime
import sys
import os
from order_manager import OrderManager

from queue_manager import QueueManager
from solver import Solver
from rebalance import RebalanceManager
from reporting import ReportingSystem
from binance_api import BinanceAPI

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

    def run_test_scenario(self, scenario_name: str):
        """Run specific test scenarios"""
        if scenario_name == "basic_order":
            self._test_basic_order_flow()
        elif scenario_name == "rate_limit":
            self._test_rate_limit()
        elif scenario_name == "rebalance":
            self._test_rebalance()
        elif scenario_name == "large_order":
            self._test_large_order()
        else:
            logger.error(f"Unknown scenario: {scenario_name}")

    def _test_basic_order_flow(self):
        """Test basic buy/sell order flow"""
        logger.info("Testing basic order flow...")
        
        # Sample buy order
        buy_order = {
            "timestamp": 0,
            "action": "buy",
            "positionId": 1,
            "indexId": 1,
            "quantity": 100,
            "indexPrice": 1000,
            "assets": [
                {"assetId": "A", "quantity": 1, "price": 10},
                {"assetId": "B", "quantity": 2, "price": 5},
                {"assetId": "C", "quantity": 5, "price": 2}
            ]
        }
        
        result = self.submit_order(buy_order)
        logger.info(f"Buy order result: {result}")
        
        # Check fill report
        fill_report = self.get_fill_report(1)
        logger.info(f"Fill report: {fill_report}")

    def _test_rate_limit(self):
        """Test rate limit handling"""
        logger.info("Testing rate limit handling...")
        
        # Submit multiple orders rapidly
        for i in range(120):  # More than rate limit
            order = {
                "timestamp": 0,
                "action": "buy",
                "positionId": i,
                "indexId": 1,
                "quantity": 100,
                "indexPrice": 1000
            }
            result = self.submit_order(order)
            logger.info(f"Order {i} result: {result}")

    def _test_rebalance(self):
        """Test rebalancing functionality"""
        logger.info("Testing rebalance...")
        
        index_data = {
            "indexId": 1,
            "assets": [
                {"assetId": "A", "quantity": 1, "price_initial": 10, "price_current": 20},
                {"assetId": "B", "quantity": 2, "price_initial": 5, "price_current": 5},
                {"assetId": "C", "quantity": 5, "price_initial": 2, "price_current": 2}
            ]
        }
        
        result = self.rebalance_manager.execute_rebalance(1, index_data)
        logger.info(f"Rebalance result: {result}")

    def _test_large_order(self):
        """Test large order handling"""
        logger.info("Testing large order handling...")
        
        large_order = {
            "timestamp": 0,
            "action": "buy",
            "positionId": 1,
            "indexId": 1,
            "quantity": 1000000,
            "indexPrice": 30,
            "assets": [
                {"assetId": "A", "quantity": 1, "price": 10},
                {"assetId": "B", "quantity": 2, "price": 5},
                {"assetId": "C", "quantity": 5, "price": 2}
            ]
        }
        
        result = self.submit_order(large_order)
        logger.info(f"Large order result: {result}")

def main():
    parser = argparse.ArgumentParser(description='ETF Trading System')
    parser.add_argument('--scenario', type=str, help='Test scenario to run')
    parser.add_argument('--action', type=str, help='Action to perform (buy/sell/cancel)')
    parser.add_argument('--position-id', type=int, help='Position ID')
    parser.add_argument('--index-id', type=int, help='Index ID')
    parser.add_argument('--quantity', type=float, help='Order quantity')
    parser.add_argument('--price', type=float, help='Order price')
    
    args = parser.parse_args()
    
    system = ETFTradingSystem()
    
    if args.scenario:
        system.run_test_scenario(args.scenario)
    elif args.action:
        if args.action == 'buy':
            order = {
                "action": "buy",
                "positionId": args.position_id,
                "indexId": args.index_id,
                "quantity": args.quantity,
                "indexPrice": args.price
            }
            result = system.submit_order(order)
            print(f"Order result: {result}")
        elif args.action == 'cancel':
            result = system.cancel_order(args.position_id)
            print(f"Cancel result: {result}")

if __name__ == "__main__":
    main() 