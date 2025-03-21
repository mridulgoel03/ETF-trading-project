import json
import pytest
from datetime import datetime, timedelta
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.etf_trading.models import Order, Index, OrderType, OrderStatus
from src.etf_trading.simulator import TradingSimulator

class TestOrderScenarios:
    @pytest.fixture
    def test_data(self):
        with open('tests/test_data/scenarios.json', 'r') as f:
            return json.load(f)

    @pytest.fixture
    def simulator(self):
        return TradingSimulator()

    def test_high_frequency_orders(self, simulator, test_data):
        """Test 100 orders in <10 seconds to trigger rate limit"""
        scenario = test_data['edge_cases_scenarios'][0]

        # Setup index
        index_data = scenario['initial_index']
        index_assets = [
            (asset[0], asset[1], asset[2], asset[3])
            for asset in index_data['assets']
        ]
        simulator.create_index(index_data['id'], index_assets)

        # Submit 100 orders quickly
        for i, event in enumerate(scenario['timeline']):
            if 'repeat' in event:
                for _ in range(event['repeat']):
                    params = event['params'].copy()
                    params["position_id"] = len(simulator.orders) + 1
                    order = simulator.buy(**params)
                    assert order.status == OrderStatus.PENDING
            else:
                order = simulator.buy(**event['params'])
                assert order.status == OrderStatus.PENDING

        # Process orders and check rate limit
        simulator.process_queue()
        rate_limited_orders = simulator.get_rate_limited_orders()
        assert len(rate_limited_orders) > 0  # Some orders must have been rate-limited

    def test_large_order_price_impact(self, simulator, test_data):
        """Test large buy order moving market price"""
        scenario = test_data['edge_cases_scenarios'][1]

        # Setup index
        index_data = scenario['initial_index']
        index_assets = [
            (asset[0], asset[1], asset[2], asset[3])
            for asset in index_data['assets']
        ]
        simulator.create_index(index_data['id'], index_assets)

        # Place large buy order
        order = simulator.buy(**scenario['timeline'][0]['params'])
        assert order.status == OrderStatus.PENDING

        # Process queue
        simulator.process_queue()

        # Update market prices
        simulator.update_prices(index_data['id'], scenario['timeline'][1]['asset_prices'])

        # Verify new asset prices reflect impact
        for asset in simulator.indices[index_data['id']].assets:
            expected_price = scenario['timeline'][1]['asset_prices'].get(asset.symbol)
            if expected_price:
                assert asset.current_price == expected_price


    def test_basic_order_flow(self, simulator, test_data):
        """Test case 1a: Basic order flow with sequential operations"""
        scenario = test_data['basic_scenarios'][0]
 
        # Setup initial index
        index_data = scenario['initial_index']
        index_assets = [
            (asset[0], asset[1], asset[2], asset[3])
            for asset in index_data['assets']
        ]
        simulator.create_index(index_data['id'], index_assets)

        # Execute timeline
        for event in scenario['timeline']:
            if event['action'] == 'buy':
                order = simulator.buy(**event['params'])
                assert order.status.value == event['expected_status']
            elif event['action'] == 'cancel':
                result = simulator.cancel(**event['params'])
                assert simulator.get_order(event['params']['position_id']).status.value == event['expected_status']

    def test_liquidity_scenario(self, simulator, test_data):
        """Test case 1b: Edge case with limited liquidity"""
        scenario = test_data['liquidity_scenarios'][0]
 
        # Setup initial index with liquidity info
        index_data = scenario['initial_index']
        index_assets = [
            (asset[0], asset[1], asset[2], asset[3])
            for asset in index_data['assets']
        ]
        index = simulator.create_index(index_data['id'], index_assets)
        
        # Set liquidity constraints
        simulator.set_liquidity_info(
            index_data['id'],
            index_data['liquidity_info']
        )

        # Execute timeline
        for event in scenario['timeline']:
            if 'action' not in event:
                continue
                
            if event['action'] == 'buy':
                order = simulator.buy(**event['params'])
                assert order.status.value == event['expected_status']
            
            # Update asset prices if specified
            if 'asset_prices' in event:
                simulator.update_prices(
                    index_data['id'],
                    event['asset_prices']
                )
            
            # Verify fill percentage if specified
            if 'expected_fill_percentage' in event:
                fill_report = simulator.get_fill_report(event['params']['position_id'])
                assert abs(fill_report.fill_percentage - event['expected_fill_percentage']) < 0.1

    def test_rebalance_scenario(self, simulator, test_data):
        """Test monthly rebalance with asset changes"""
        scenario = test_data['rebalance_scenarios'][0]

        # Setup initial index
        index_data = scenario['initial_index']
        index_assets = [
            (asset[0], asset[1], asset[2], asset[3])
            for asset in index_data['assets']
        ]
        simulator.create_index(index_data['id'], index_assets)

        # Execute timeline
        for event in scenario['timeline']:
            if 'asset_prices' in event:
                simulator.update_prices(
                    index_data['id'],
                    event['asset_prices']
                )
            
            if 'action' in event and event['action'] == 'rebalance':
                report = simulator.rebalance(**event['params'])
                index = simulator.get_index(event['params']['index_id'])
                assert abs(index.calculate_nav() - event['expected_nav']) < 0.1

    def test_batch_processing(self, simulator, test_data):
        """Test batch processing of multiple index orders"""
        scenario = test_data['batch_processing_scenarios'][0]
        
        # Setup indices
        for index_data in scenario['indices']:
            simulator.create_index(
                index_data['id'],
                [(asset, 1, 100, 100) for asset in index_data['assets']]
            )

        # Execute timeline
        for event in scenario['timeline']:
            # Submit all orders
            for order_data in event['orders']:
                simulator.buy(
                    position_id=len(simulator.orders) + 1,
                    index_id=order_data['index_id'],
                    quantity=order_data['amount'] / order_data['price'],
                    index_price=order_data['price']
                )
            
            # Process queue
            simulator.process_queue()
            
            # Verify queue state
            queued_indices = [
                order.index_id for order in simulator.order_queue
            ]
            assert queued_indices == event['expected_queue'] 
