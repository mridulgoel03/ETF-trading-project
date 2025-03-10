# ETF Trading System

A sophisticated trading system for managing ETF indices on Binance, handling order execution, rebalancing, and reporting.

## Overview

This system manages ETF index trading with the following key features:
- Order execution (buy/sell/cancel) with rate limiting
- Monthly rebalancing of indices
- Liquidity management and loss minimization
- Comprehensive reporting

### Key Components

1. **Order Manager**: Handles order execution and cancellation
2. **Queue Manager**: Manages rate limits (100 orders/10s)
3. **Solver**: Optimizes order execution to minimize losses
4. **Rebalance Manager**: Handles monthly index rebalancing
5. **Reporting System**: Tracks fills, losses, and rebalancing costs

## Installation

```bash
git clone https://github.com/mridulgoel03/ETF_trading_system.git
cd ETF_trading_system
pip install -r requirements.txt
```

## Configuration

Create a `.env` file:
```env
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
```

## Usage

### Running the System

```bash
python src/main.py
```

### Testing with Fake Data

```bash
python -m pytest tests/
```

### Example Operations

1. Submit Buy Order:
```python
from src.main import ETFTradingSystem

system = ETFTradingSystem()
system.submit_order({
    "action": "buy",
    "positionId": 1,
    "indexId": 1,
    "quantity": 100,
    "indexPrice": 1000
})
```

2. Check Fill Report:
```python
report = system.get_fill_report(position_id=1)
print(f"Fill percentage: {report['fill_percentage']}%")
print(f"Total loss: ${report['loss']}")
```

## Testing

The system includes comprehensive test cases:

1. Basic order flow
2. Rate limit handling
3. Large order execution
4. Rebalancing scenarios
5. Edge cases

Run tests:
```bash
pytest tests/test_orders.py
pytest tests/test_solver.py
pytest tests/test_rebalance.py
```

## Architecture

### Order Flow
1. Order submission
2. Queue management (rate limiting)
3. Liquidity check
4. Execution strategy determination
5. Order execution
6. Reporting

### Rebalancing Process
1. Monthly trigger
2. Calculate new weights
3. Determine optimal execution strategy
4. Execute trades
5. Report costs

## Error Handling

The system handles various error scenarios:
- Insufficient liquidity
- Rate limit violations
- Partial fills
- Failed executions

## Monitoring

Access reports via:
```python
# Fill report
system.get_fill_report(position_id)

# Rebalance report
system.get_rebalance_report(index_id)
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License