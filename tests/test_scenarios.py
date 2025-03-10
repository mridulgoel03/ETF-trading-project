from datetime import datetime
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from main import ETFTradingSystem


class TestScenarios:
    @pytest.fixture
    def trading_system(self):
        return ETFTradingSystem()

    def test_basic_order_flow(self, trading_system):
        """Test basic buy/sell/cancel flow"""
        # Buy order
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
        result = trading_system.submit_order(buy_order)
        assert result['status'] == 'queued'

        # Check fill report
        fill_report = trading_system.get_fill_report(1)
        assert fill_report['fill_percentage'] > 0

    def test_rate_limit_handling(self, trading_system):
        """Test handling of rate limits (100 orders/10s)"""
        # Submit 120 orders rapidly
        orders = []
        for i in range(120):
            order = {
                "timestamp": 0,
                "action": "buy",
                "positionId": i,
                "indexId": 1,
                "quantity": 100,
                "indexPrice": 1000
            }
            orders.append(order)

        # Submit all orders
        results = [trading_system.submit_order(order) for order in orders]
        
        # Verify rate limiting
        queued = [r for r in results if r['status'] == 'queued']
        assert len(queued) <= 100

    def test_rebalancing(self, trading_system):
        """Test monthly rebalancing"""
        index_data = {
            "indexId": 1,
            "assets": [
                {"assetId": "A", "quantity": 1, "price_initial": 10, "price_current": 20},
                {"assetId": "B", "quantity": 2, "price_initial": 5, "price_current": 5},
                {"assetId": "C", "quantity": 5, "price_initial": 2, "price_current": 2}
            ]
        }
        
        # Force rebalance
        rebalance_result = trading_system.rebalance_manager.execute_rebalance(1, index_data)
        assert rebalance_result['status'] == 'executed'

        # Check rebalance report
        report = trading_system.get_rebalance_report(1)
        assert 'total_cost' in report

    def test_limit_order_partial_fills(self, trading_system):
        """Test partial fills and limit orders"""
        limit_order = {
            "timestamp": 0,
            "action": "buy",
            "positionId": 1,
            "indexId": 1,
            "quantity": 300000,  # 300k Index qty
            "indexPrice": 30,
            "assets": [
                {"assetId": "A", "quantity": 1, "price": 9},
                {"assetId": "B", "quantity": 2, "price": 4},
                {"assetId": "C", "quantity": 5, "price": 1.5}
            ]
        }
        
        result = trading_system.submit_order(limit_order)
        assert result['status'] == 'queued'
        
        # Check partial fills
        fill_report = trading_system.get_fill_report(1)
        assert fill_report['fill_percentage'] <= 20  # Should be limited by worst-case asset

    def test_cancel_partially_filled(self, trading_system):
        """Test cancellation of partially filled orders"""
        # Submit order
        order = {
            "timestamp": 0,
            "action": "buy",
            "positionId": 1,
            "indexId": 1,
            "quantity": 1000,
            "indexPrice": 1000
        }
        trading_system.submit_order(order)
        
        # Cancel after partial fill
        cancel_result = trading_system.cancel_order(1)
        assert cancel_result['status'] == 'cancelled'
        assert 'partial_fill' in cancel_result['details']

    def test_minimum_order_size(self, trading_system):
        """Test minimum order size constraints"""
        small_order = {
            "timestamp": 0,
            "action": "buy",
            "positionId": 1,
            "indexId": 1,
            "quantity": 0.1,  # Too small
            "indexPrice": 1000
        }
        
        result = trading_system.submit_order(small_order)
        assert result['status'] == 'failed'
        assert 'minimum order size' in result['error'].lower() 