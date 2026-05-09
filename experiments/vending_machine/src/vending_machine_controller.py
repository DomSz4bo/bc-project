from src.ports import InventoryPort, CoinHandlerPort

class VendingMachineController:
    def __init__(self, inventory: InventoryPort, coin_handler: CoinHandlerPort):
        self.inventory = inventory
        self.coin_handler = coin_handler
        self.current_balance = 0.0
        self.selected_product_id = None
        self.product_price = 0.0

    def select_product(self, product_id: str) -> None:
        price = self.inventory.validate_availability(product_id)
        if price is not None:
            self.selected_product_id = product_id
            self.product_price = price
        else:
            self.selected_product_id = None

    def request_cancel(self) -> None:
        if self.current_balance > 0:
            self.coin_handler.return_coins(self.current_balance)
        self.reset()

    def insert_coins(self, amount: float) -> None:
        self.current_balance += amount
        self.coin_handler.notify_currency_inserted(amount)

    def process_transaction(self) -> None:
        if not self.selected_product_id or self.current_balance < self.product_price:
            return

        change_due = self.current_balance - self.product_price
        if not self.coin_handler.check_change_capacity(change_due):
            self.coin_handler.return_coins(self.current_balance)
            self.reset()
            return

        self.inventory.dispense_product(self.selected_product_id)
        if change_due > 0:
            self.coin_handler.return_coins(change_due)
        self.reset()

    def reset(self) -> None:
        self.current_balance = 0.0
        self.selected_product_id = None
        self.product_price = 0.0
