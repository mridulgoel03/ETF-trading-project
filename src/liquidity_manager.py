class LiquidityManager:
    def __init__(self):
        self.liquidity_thresholds = {
            1: 10000,  # Example threshold for index 1
            2: 20000   # Example threshold for index 2
        }
        
    def check_liquidity(self, index_id: int, quantity: float) -> float:
        """
        Checks how much of an order can be filled based on available liquidity.
        Returns the fillable quantity.
        ## implement more complexity and accuracy to the liquidity management system 
        """
        threshold = self.liquidity_thresholds.get(index_id, 0)
        return min(quantity, threshold)
        
    def apply_slippage(self, order: dict) -> dict:
        """
        Adjusts the final execution price based on liquidity constraints.
        Returns modified order with adjusted price.
        """
        quantity = order.get('quantity', 0)
        index_id = order.get('indexId')
        original_price = order.get('indexPrice', 0)
        
        # Simple slippage model: 0.1% per 1000 units
        slippage = (quantity / 1000) * 0.001
        
        # Cap slippage at 1%
        slippage = min(slippage, 0.01)
        
        # Apply slippage based on order type
        if order.get('action') == 'buy':
            order['executionPrice'] = original_price * (1 + slippage)
        else:
            order['executionPrice'] = original_price * (1 - slippage)
            
        return order 