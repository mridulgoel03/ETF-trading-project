from datetime import datetime
from src.etf_trading import TradingSimulator
import json
import time

def load_test_scenarios():
    with open('tests/test_data/scenarios.json', 'r') as f:
        return json.load(f)

def run_basic_scenario(simulator, scenario):
    print("\n=== Running Basic Scenario ===")
    
    # Setup initial index
    index_data = scenario['initial_index']
    index_assets = [
        (asset[0], asset[1], asset[2], asset[3])
        for asset in index_data['assets']
    ]
    simulator.create_index(index_data['id'], index_assets)
    print(f"Created index {index_data['id']} with assets: {index_assets}")

    # Execute timeline
    for event in scenario['timeline']:
        print(f"\nTimestamp {event.get('timestamp', 'N/A')}:")
        
        if 'action' in event:
            if event['action'] == 'buy':
                order = simulator.buy(**event['params'])
                print(f"Buy order {order.position_id}: Status = {order.status.value}")
            elif event['action'] == 'cancel':
                result = simulator.cancel(**event['params'])
                order = simulator.get_order(event['params']['position_id'])
                print(f"Cancel order {event['params']['position_id']}: Status = {order.status.value}")

def run_liquidity_scenario(simulator, scenario):
    print("\n=== Running Liquidity Scenario ===")
    
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
    print(f"Created index {index_data['id']} with liquidity constraints")

    # Execute timeline
    for event in scenario['timeline']:
        print(f"\nTimestamp {event.get('timestamp', 'N/A')}:")
        
        if 'asset_prices' in event:
            simulator.update_prices(index_data['id'], event['asset_prices'])
            print(f"Updated prices: {event['asset_prices']}")
        
        if 'action' in event:
            if event['action'] == 'buy':
                order = simulator.buy(**event['params'])
                print(f"Buy order {order.position_id}: Status = {order.status.value}")
                
                # Process the order queue
                simulator.process_queue()
                
                # Get fill report
                if 'expected_fill_percentage' in event:
                    fill_report = simulator.get_fill_report(event['params']['position_id'])
                    print(f"Fill report: {fill_report.fill_percentage:.1f}% filled, Loss: ${fill_report.loss:.2f}")

def run_rebalance_scenario(simulator, scenario):
    print("\n=== Running Rebalance Scenario ===")
    
    # Setup initial index
    index_data = scenario['initial_index']
    index_assets = [
        (asset[0], asset[1], asset[2], asset[3])
        for asset in index_data['assets']
    ]
    simulator.create_index(index_data['id'], index_assets)
    print(f"Created index {index_data['id']}")

    # Execute timeline
    for event in scenario['timeline']:
        print(f"\nTimestamp {event.get('timestamp', 'N/A')}:")
        
        if 'asset_prices' in event:
            simulator.update_prices(index_data['id'], event['asset_prices'])
            index = simulator.get_index(index_data['id'])
            print(f"Updated prices, new NAV: ${index.calculate_nav():.2f}")
        
        if 'action' in event and event['action'] == 'rebalance':
            report = simulator.rebalance(**event['params'])
            print(f"Rebalance cost: ${report.total_cost:.2f}")
            print(f"New weights: {report.new_weights}")

def run_batch_processing_scenario(simulator, scenario):
    print("\n=== Running Batch Processing Scenario ===")
    
    # Setup indices
    for index_data in scenario['indices']:
        simulator.create_index(
            index_data['id'],
            [(asset, 1, 100, 100) for asset in index_data['assets']]
        )
        print(f"Created index {index_data['id']} with assets: {index_data['assets']}")

    # Execute timeline
    for event in scenario['timeline']:
        print(f"\nTimestamp {event.get('timestamp', 'N/A')}:")
        
        # Submit all orders
        for order_data in event['orders']:
            order = simulator.buy(
                position_id=len(simulator.orders) + 1,
                index_id=order_data['index_id'],
                quantity=order_data['amount'] / order_data['price'],
                index_price=order_data['price']
            )
            print(f"Submitted order for {order_data['index_id']}: ${order_data['amount']}")
        
        # Process queue
        print("\nProcessing order queue...")
        simulator.process_queue()
        
        # Show queue state
        queued_indices = [order.index_id for order in simulator.order_queue]
        print(f"Remaining in queue: {queued_indices}")

def main():
    # Initialize simulator
    simulator = TradingSimulator()
    
    # Load test scenarios
    scenarios = load_test_scenarios()
    
    # Run different scenarios
    run_basic_scenario(simulator, scenarios['basic_scenarios'][0])
    
    simulator = TradingSimulator()  # Reset simulator
    run_liquidity_scenario(simulator, scenarios['liquidity_scenarios'][0])
    
    simulator = TradingSimulator()  # Reset simulator
    run_rebalance_scenario(simulator, scenarios['rebalance_scenarios'][0])
    
    simulator = TradingSimulator()  # Reset simulator
    run_batch_processing_scenario(simulator, scenarios['batch_processing_scenarios'][0])

if __name__ == "__main__":
    main() 