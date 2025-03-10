Enhanced fake_orders.json with edge cases
Basic implementation of OrderBook with core functionality
Basic implementation of LiquidityManager with simple slippage model
Empty files for all other components
The edge cases in the orders now include:
Rate limit testing (multiple orders at same timestamp)
Very large orders requiring partial fills
Orders exceeding liquidity thresholds
Cancellation of partially filled orders


This main.py file includes several test functions:
load_test_data(): Loads orders from the fake_orders.json file
test_order_submission(): Tests basic order submission functionality
test_large_order_handling(): Tests how the system handles large orders and slippage
test_order_cancellation(): Tests order cancellation functionality
test_rate_limits(): Tests handling of multiple orders at the same timestamp
run_all_tests(): Runs all test scenarios in sequence
To run the tests:
The output will show detailed logging of each test scenario, including:
Order submission results
Liquidity checks
Price adjustments for large orders
Order cancellation confirmations
Rate limit handling
This test harness will help you:
Verify the basic functionality of your order book
Test liquidity management
Ensure proper handling of edge cases
Debug issues in the system