import pytest

from src.inventory import EMPTY, InvalidItemCode, Inventory, Item, NotInStockError


@pytest.fixture
def stocked_inventory() -> Inventory:
    inventory = Inventory(6, 9)
    inventory.set_item("A1", Item("prodA1", 150, 2))
    inventory.set_item("C7", Item("prodC7", 210, 5))
    inventory.set_item("D4", Item("prodD4", 110, 9))
    inventory.set_item("B2", Item("prodB2", 130, 0))
    return inventory


@pytest.fixture
def empty_inventory() -> Inventory:
    return Inventory(5, 6)


class TestInventory:
    def test_is_in_stock(self, stocked_inventory: Inventory):
        in_stock_code = "A1"
        res = stocked_inventory.is_in_stock(in_stock_code)
        assert res

        not_in_stock_code = "A2"
        res2 = stocked_inventory.is_in_stock(not_in_stock_code)
        assert not res2

    def test_getting_price(self, stocked_inventory: Inventory):
        in_stock_code = "A1"
        price = stocked_inventory.get_cent_price(in_stock_code)
        assert price == 150

        in_stock_code2 = "C7"
        price2 = stocked_inventory.get_cent_price(in_stock_code2)
        assert price2 == 210

        empty_code = "A2"
        empty_price = stocked_inventory.get_cent_price(empty_code)
        assert empty_price == 0

    def test_dispense_product_in_stock(self, stocked_inventory: Inventory):
        code = "A1"
        before_quant = stocked_inventory.get_item(code).quantity

        stocked_inventory.dispense_product(code)
        after_quant = stocked_inventory.get_item(code).quantity

        assert before_quant == (after_quant + 1)

    def test_dispense_empty(self, empty_inventory: Inventory):
        with pytest.raises(NotInStockError):
            empty_inventory.dispense_product("C1")

    def test_dispense_product_out_of_stock(self, stocked_inventory: Inventory):
        with pytest.raises(NotInStockError):
            stocked_inventory.dispense_product("B2")

    def test_invalid_item_codes(self, stocked_inventory: Inventory):
        # Invalid type
        with pytest.raises(InvalidItemCode):
            stocked_inventory.get_item(123)
        # Too short
        with pytest.raises(InvalidItemCode):
            stocked_inventory.get_item("A")
        # Row out of range (G is 7th, inventory has 6 rows A-F)
        with pytest.raises(InvalidItemCode):
            stocked_inventory.get_item("G1")
        # Cell not a number
        with pytest.raises(InvalidItemCode):
            stocked_inventory.get_item("AX")
        # Cell out of range (0 or > 9)
        with pytest.raises(InvalidItemCode):
            stocked_inventory.get_item("A0")
        with pytest.raises(InvalidItemCode):
            stocked_inventory.get_item("A10")

    def test_case_insensitivity(self, stocked_inventory: Inventory):
        assert stocked_inventory.get_cent_price("a1") == 150
        assert stocked_inventory.is_in_stock("c7") is True

    def test_inventory_initialization_boundaries(self):
        inv = Inventory(0, -5)
        assert inv.number_of_rows == 1
        assert inv.row_length == 1
        assert inv.get_item("A1") == EMPTY
        with pytest.raises(InvalidItemCode):
            inv.get_item("A2")
        with pytest.raises(InvalidItemCode):
            inv.get_item("B1")

    def test_clear_item(self, stocked_inventory: Inventory):
        code = "A1"
        assert stocked_inventory.get_item(code).name == "prodA1"
        stocked_inventory.clear_item(code)
        assert stocked_inventory.get_item(code) == EMPTY

    def test_decrement_at_zero(self, stocked_inventory: Inventory):
        code = "B2"  # quantity is 0
        assert stocked_inventory.get_item(code).quantity == 0
        stocked_inventory.decrement_item(code)
        assert stocked_inventory.get_item(code).quantity == 0
