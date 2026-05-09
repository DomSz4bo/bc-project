from datetime import datetime

from src.bank import Bank
from src.inventory import InvalidItemCode, Inventory, InventoryException


class VendingMachine:
    def __init__(self):
        self.selected_code: str | None = None
        self.inventory = Inventory(6, 8)
        self.bank = Bank(lambda x: print(self.inserted_coin(x)))
        self.transactions = []

    def select_item(self, code: str) -> str:
        if self.selected_code is not None:
            return "Cancel order to choose a different product"
        try:
            in_stock = self.inventory.is_in_stock(code)
            product_price = self.inventory.get_cent_price(code)
        except InvalidItemCode:
            return "Choose a valid item code."

        if not in_stock:
            return "Selected item is out of stock."

        self.selected_code = code
        whole, cents = self._get_print_price(product_price)
        return f"Insert {whole}.{cents}€"

    def inserted_coin(self, new_balance: int) -> str:
        if self.selected_code is None:
            self.bank.return_balance()
            return "Please select a product."

        product_price = self.inventory.get_cent_price(self.selected_code)
        if new_balance < product_price:
            difference = product_price - new_balance
            whole, cents = self._get_print_price(difference)
            return f"Remaining balance required: {whole}.{cents}€"

        change = new_balance - product_price
        if not self.bank.can_give_change(change):
            self.bank.return_balance()
            whole, cents = self._get_print_price(product_price)
            return f"Exact change required. Insert {whole}.{cents}€"

        try:
            self.inventory.dispense_product(self.selected_code)
        except InventoryException:
            self.cancel()
            return "Something went wrong. Transaction cancelled."
        self.bank.dispense_change(change)

        self.record_transaction()
        self.selected_code = None

        whole, cents = self._get_print_price(change)
        return f"Please take your product. Change: {whole}.{cents}€"

    def cancel(self):
        if self.selected_code is not None:
            self.selected_code = None
            self.bank.return_balance()

    def record_transaction(self):
        try:
            product = self.inventory.get_item(self.selected_code)
            name = product.name
            price = product.cent_price
        except InventoryException:
            name = f"Code:{self.selected_code}"
            price = 0

        self.transactions.append({"item": name, "price": price, "time": datetime.now()})

    def _get_print_price(self, cent_prince: int) -> tuple[int, int]:
        whole = cent_prince // 100
        cents = cent_prince % 100
        return (whole, cents)
