from typing import Dict, List

class OrderBook:
    def __init__(self):
        self.orders: Dict[int, dict] = {}
        self.index_orders: Dict[int, List[int]] = {}  # index_id -> [order_ids]
        
    def add_order(self, order: dict) -> bool:
        """
        Adds an order to the order book.
        ###Also updates the index_orders dictionary. 
        Returns True if successful, False if failed.
        """
        position_id = order.get('positionId')
        index_id = order.get('indexId')
        
        if position_id is None or index_id is None:
            return False
            
        self.orders[position_id] = order
        if index_id not in self.index_orders:
            self.index_orders[index_id] = []
        self.index_orders[index_id].append(position_id)
        return True
        
    def cancel_order(self, order_id: int) -> bool:
        """
        Cancels an existing order.
        Returns True if successful, False if order not found.
        """
        if order_id not in self.orders:
            return False
            
        order = self.orders[order_id]
        index_id = order.get('indexId')
        
        if index_id in self.index_orders:
            self.index_orders[index_id].remove(order_id)
        
        del self.orders[order_id]
        return True
        
    def get_orders(self, index_id: int) -> List[dict]:
        """
        Retrieves active orders for a given ETF index.
        """
        if index_id not in self.index_orders:
            return []
            
        return [self.orders[order_id] for order_id in self.index_orders[index_id]] 
    
