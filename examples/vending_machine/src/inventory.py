from typing import NamedTuple


class Item(NamedTuple):
    name: str
    cent_price: int
    quantity: int


EMPTY = Item("EMPTY", 0, -1)

ROW_SIZE = 6


class Inventory:
    def __init__(self, number_of_rows: int, row_length: int):
        self.number_of_rows = max(1, number_of_rows)
        self.row_length = max(1, row_length)
        self._stock = [[EMPTY] * self.row_length for _ in range(self.number_of_rows)]

    def get_item(self, code: str) -> Item:
        row_idx, item_idx = self._parse_code(code)
        return self._stock[row_idx][item_idx]

    def _parse_code(self, code: str) -> tuple[int, int]:
        if not isinstance(code, str) or len(code) < 2:
            raise InvalidItemCode("Expected code format <ROW: A, B..><CELL: number>.")

        row_idx = ord(code[0].upper()) - ord("A")
        if row_idx < 0 or row_idx >= self.number_of_rows:
            max_row_code = chr(ord("A") + self.number_of_rows - 1)
            raise InvalidItemCode(
                f"Incorrect row symbol: {code[0]}. Expected 'A'-'{max_row_code}'."
            )

        try:
            cell_number = int(code[1:])
            if cell_number < 1 or cell_number > self.row_length:
                raise ValueError()
        except ValueError:
            raise InvalidItemCode(
                f"Incorrect cell number: {code[1:]}. Expected 1 - {self.row_length}."
            )

        item_idx = cell_number - 1
        return row_idx, item_idx

    def set_item(self, code: str, item: Item) -> None:
        row_idx, item_idx = self._parse_code(code)
        self._stock[row_idx][item_idx] = item

    def clear_item(self, code: str) -> None:
        self.set_item(code, EMPTY)

    def is_in_stock(self, code: str) -> bool:
        in_stock = self.get_item(code).quantity > 0
        return in_stock

    def get_cent_price(self, code: str) -> int:
        return self.get_item(code).cent_price

    def dispense_product(self, code: str) -> Item:
        if not self.is_in_stock(code):
            raise NotInStockError("Can not dispense product that is not in stock.")
        self.decrement_item(code)
        return self.get_item(code)

    def decrement_item(self, code: str):
        item = self.get_item(code)
        if item.quantity <= 0:
            return 0

        new_item = Item(item.name, item.cent_price, item.quantity - 1)
        self.set_item(code, new_item)


class InventoryException(Exception):
    pass


class InvalidItemCode(InventoryException):
    pass


class NotInStockError(InventoryException):
    pass
