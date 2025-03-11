# ETF Trading System

A Python-based ETF trading system that simulates the creation, management, and trading of ETF indices without direct Binance integration.

## Features

- Create and manage ETF indices with multiple assets
- Process buy, sell, and cancel orders with rate limiting (100 orders/10 seconds)
- Handle rebalancing of indices with cost calculation
- Simulate market conditions including partial fills and slippage
- Test scenarios for normal operations and edge cases

## Project Structure

```
.
├── src/
│   └── etf_trading/
│       ├── __init__.py
│       ├── models.py
│       └── simulator.py
├── tests/
│   └── unit/
│       └── __init__.py
│       └── test_order_scenarios.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.8+
- Dependencies listed in requirements.txt

## Installation

```bash
pip install -r requirements.txt
```

## Testing

```bash
pytest tests/
```

## Usage Example

```python
from etf_trading import TradingSimulator

# Create a simulator instance
simulator = TradingSimulator()

# Create an index
index_assets = [
    ("BTC", 1, 10000),  # (symbol, quantity, price)
    ("ETH", 2, 2000),
    ("BNB", 5, 200)
]
simulator.create_index("TEST_INDEX", index_assets)

# Place a buy order
order = simulator.buy(
    position_id=1,
    index_id="TEST_INDEX",
    quantity=1.5,
    index_price=15000
)

# Process the order queue
simulator.process_queue()

# Check order status
order = simulator.get_order(1)
print(f"Order status: {order.status}")
```

## Features Implemented

1. Order Management
   - Buy orders with rate limiting
   - Cancel orders with loss calculation
   - Order queue processing

2. Index Management
   - Create indices with multiple assets
   - Calculate NAV (Net Asset Value)
   - Rebalance indices with cost tracking

3. Market Simulation
   - Partial fills based on order size
   - Price slippage simulation
   - Rate limiting (100 orders/10 seconds)

4. Test Cases
   - Basic order flow scenarios
   - Edge cases (large orders, zero quantity, rapid cancellations)
   - Rate limiting verification

## Notes

- The system simulates market behavior without actual Binance integration
- All timestamps are handled in local time
- Minimum order value per asset is $5
- Trading fee is set at 0.1%
- Fill rates are simulated based on order size 
