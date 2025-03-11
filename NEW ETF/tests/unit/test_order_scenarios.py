import pytest
from datetime import datetime, timedelta
from src.etf_trading.models import Order, Index, OrderType, OrderStatus
from src.etf_trading.simulator import TradingSimulator

class TestOrderScenarios:
    @pytest.fixture
    def simulator(self):
        return TradingSimulator()

    def test_basic_order_flow(self, simulator):
        """Test case 1a: Basic order flow with sequential operations"""
        # Setup test index
        index_assets = [
            ("BTC", 1, 10000),
            ("ETH", 2, 2000),
            ("BNB", 5, 200)
        ]
        index_id = "TEST_INDEX_1"
        simulator.create_index(index_id, index_assets)

        # Test scenario timeline
        base_time = datetime.now()
        
        # Timestamp 1: Initial buy order
        order1 = simulator.buy(
            position_id=1,
            index_id=index_id,
            quantity=1.5,
            index_price=15000
        )
        assert order1.status == OrderStatus.PENDING

        # Timestamp 2: Second buy order
        order2 = simulator.buy(
            position_id=2,
            index_id=index_id,
            quantity=2.0,
            index_price=15100
        )
        assert order2.status == OrderStatus.PENDING

        # Timestamp 3: Cancel first order
        cancel_result = simulator.cancel(position_id=1)
        assert cancel_result.success
        assert simulator.get_order(1).status == OrderStatus.CANCELLED

    def test_edge_cases(self, simulator):
        """Test case 1b: Edge cases for order handling"""
        index_id = "TEST_INDEX_2"
        index_assets = [
            ("BTC", 0.1, 10000),  # Small position
            ("ETH", 10, 2000),    # Large position
            ("BNB", 0.001, 200)   # Minimal position
        ]
        simulator.create_index(index_id, index_assets)

        # Edge case 1: Extremely large order
        large_order = simulator.buy(
            position_id=3,
            index_id=index_id,
            quantity=1000000,  # Very large quantity
            index_price=15000
        )
        assert large_order.status == OrderStatus.REJECTED  # Should reject due to size

        # Edge case 2: Zero quantity order
        zero_order = simulator.buy(
            position_id=4,
            index_id=index_id,
            quantity=0,
            index_price=15000
        )
        assert zero_order.status == OrderStatus.REJECTED

        # Edge case 3: Rapid order/cancel sequence
        orders = []
        for i in range(5):
            order = simulator.buy(
                position_id=10+i,
                index_id=index_id,
                quantity=1.0,
                index_price=15000
            )
            orders.append(order)
            simulator.cancel(position_id=10+i)  # Immediate cancel

        # Verify rate limiting is enforced
        assert len(simulator.get_rate_limited_orders()) > 0 