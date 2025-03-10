# ETF Trading System

A comprehensive system for managing ETF indices on Binance with sophisticated order execution, rebalancing, and reporting capabilities.

## Table of Contents
1. [Installation](#installation)
2. [System Components](#system-components)
3. [Testing Framework](#testing-framework)
4. [Usage Examples](#usage-examples)
5. [Demo Scenarios](#demo-scenarios)
6. [Monitoring & Reporting](#monitoring--reporting)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/etf_trading_system.git
cd etf_trading_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## System Components

### 1. Order Management
```python
# Submit a buy order
python -m src.main submit-order \
    --action buy \
    --position-id 1 \
    --index-id 1 \
    --quantity 100 \
    --price 1000

# Cancel an order
python -m src.main cancel-order --position-id 1
```

### 2. Queue Management
```python
# View current queue status
python -m src.main show-queue

# View rate limit status
python -m src.main show-rate-limits
```

### 3. Solver Operations
```python
# Check fill strategy for an order
python -m src.main check-strategy \
    --position-id 1 \
    --index-id 1 \
    --quantity 100000

# View current solver status
python -m src.main solver-status
```

### 4. Rebalancing
```python
# Trigger rebalance for an index
python -m src.main rebalance --index-id 1

# View rebalance history
python -m src.main rebalance-history --index-id 1
```

## Testing Framework

### 1. Run All Tests
```bash
pytest tests/
```

### 2. Run Specific Test Categories
```bash
# Basic order flow tests
pytest tests/test_scenarios.py -k "test_basic_order_flow"

# Rate limit tests
pytest tests/test_scenarios.py -k "test_rate_limit"

# Rebalancing tests
pytest tests/test_scenarios.py -k "test_rebalance"

# Edge cases
pytest tests/test_scenarios.py -k "test_edge"
```

### 3. Run Demo Scenarios
```bash
# Run all demo scenarios
python -m src.demo_scenarios

# Run specific scenario
python -m src.demo_scenarios --scenario limit_order_partial_fill
```

## Usage Examples

### 1. Basic Order Flow
```python
from src.main import ETFTradingSystem

# Initialize system
system = ETFTradingSystem()

# Submit buy order
order = {
    "action": "buy",
    "positionId": 1,
    "indexId": 1,
    "quantity": 100,
    "indexPrice": 1000,
    "assets": [
        {"assetId": "A", "quantity": 1, "price": 10},
        {"assetId": "B", "quantity": 2, "price": 5}
    ]
}
result = system.submit_order(order)

# Check fill report
fill_report = system.get_fill_report(1)
print(f"Fill percentage: {fill_report['fill_percentage']}%")
```

### 2. Handling Large Orders
```python
# Submit large order
large_order = {
    "action": "buy",
    "positionId": 2,
    "indexId": 1,
    "quantity": 1000000,
    "indexPrice": 1000
}
result = system.submit_order(large_order)

# Monitor execution
while True:
    status = system.get_order_status(2)
    if status['state'] == 'completed':
        break
    time.sleep(1)
```

### 3. Rebalancing Example
```python
# Check if rebalancing is needed
if system.should_rebalance(index_id=1):
    result = system.execute_rebalance(1)
    print(f"Rebalance cost: ${result['total_cost']}")
```

## Demo Scenarios

### 1. Run Complete Demo
```bash
python -m src.demo_scenarios --run-all
```

This will demonstrate:
- Basic order execution
- Rate limit handling
- Partial fills
- Rebalancing
- Error scenarios

### 2. Run Specific Scenarios
```bash
# Test rate limiting
python -m src.demo_scenarios --scenario rate_limit

# Test large order handling
python -m src.demo_scenarios --scenario large_order

# Test rebalancing
python -m src.demo_scenarios --scenario rebalance
```

## Monitoring & Reporting

### 1. Fill Reports
```python
# Get fill report
report = system.get_fill_report(position_id=1)
print(f"Fill percentage: {report['fill_percentage']}%")
print(f"Average fill price: ${report['avg_price']}")
print(f"Total cost: ${report['total_cost']}")
```

### 2. Rebalance Reports
```python
# Get rebalance report
report = system.get_rebalance_report(index_id=1)
print(f"Rebalance cost: ${report['total_cost']}")
print(f"Asset changes: {report['asset_changes']}")
```

### 3. Performance Monitoring
```python
# Get system metrics
metrics = system.get_metrics()
print(f"Average fill time: {metrics['avg_fill_time']}s")
print(f"Success rate: {metrics['success_rate']}%")
```

## Configuration

### 1. Environment Variables
Create a `.env` file:
```env
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
MAX_BATCH_SIZE=100
BATCH_INTERVAL=10
MIN_ORDER_SIZE=5
```

### 2. System Parameters
```python
# Update system parameters
system.update_config({
    'max_batch_size': 100,
    'batch_interval': 10,
    'min_order_size': 5,
    'fee_rate': 0.001
})
```

## Error Handling

Common error scenarios and their handling:
1. Insufficient liquidity
2. Rate limit exceeded
3. Invalid order parameters
4. Rebalance failures
5. Network issues

## Logging

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request