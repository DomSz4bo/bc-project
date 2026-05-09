import pytest
from unittest.mock import MagicMock
from src.vending_machine import VendingMachine
from src.inventory import Item, InventoryException


@pytest.fixture
def vm():
    vending_machine = VendingMachine()
    vending_machine.inventory.set_item("A1", Item("Soda", 150, 5))
    vending_machine.inventory.set_item("A2", Item("Chips", 100, 0))
    vending_machine.bank.set_wallet({50: 10, 20: 10, 10: 10})
    return vending_machine


class TestVendingMachine:
    def test_select_item_success(self, vm: VendingMachine):
        response = vm.select_item("A1")
        assert response == "Insert 1.50€"
        assert vm.selected_code == "A1"

    def test_select_item_invalid_code(self, vm: VendingMachine):
        response = vm.select_item("Z9")
        assert response == "Choose a valid item code."
        assert vm.selected_code is None

    def test_select_item_out_of_stock(self, vm: VendingMachine):
        response = vm.select_item("A2")
        assert response == "Selected item is out of stock."
        assert vm.selected_code is None

    def test_insert_coin_without_selection(self, vm: VendingMachine):
        response = vm.inserted_coin(100)
        assert response == "Please select a product."
        assert vm.bank.get_balance_sum() == 0

    def test_insert_coin_insufficient_funds(self, vm: VendingMachine):
        vm.select_item("A1")
        response = vm.inserted_coin(100)
        assert response == "Remaining balance required: 0.50€"

    def test_purchase_success(self, vm: VendingMachine):
        vm.select_item("A1")
        initial_stock = vm.inventory.get_item("A1").quantity
        
        vm.bank.add_coin_to_balance(100)
        response = vm.inserted_coin(200) 
        
        assert response == "Please take your product. Change: 0.50€"
        assert vm.inventory.get_item("A1").quantity == initial_stock - 1
        assert vm.bank.get_balance_sum() == 0
        assert len(vm.transactions) == 1
        assert vm.transactions[0]["item"] == "Soda"
        assert vm.selected_code is None

    def test_exact_change_required(self, vm: VendingMachine):
        vm.bank.set_wallet({100: 10}) 
        vm.select_item("A1")
        
        vm.bank.add_coin_to_balance(100)
        response = vm.inserted_coin(200)
        
        assert response == "Exact change required. Insert 1.50€"
        assert vm.bank.get_balance_sum() == 0
        assert vm.inventory.get_item("A1").quantity == 5

    def test_cancel(self, vm: VendingMachine):
        vm.select_item("A1")
        vm.bank.add_coin_to_balance(100)
        
        vm.cancel()
        assert vm.selected_code is None
        assert vm.bank.get_balance_sum() == 0

    def test_inventory_exception_during_dispense(self, vm: VendingMachine):
        vm.select_item("A1")
        vm.bank.add_coin_to_balance(100)
        
        vm.inventory.dispense_product = MagicMock(side_effect=InventoryException("Error"))
        
        response = vm.inserted_coin(150)
        
        assert "Transaction cancelled" in response
        assert vm.bank.get_balance_sum() == 0
        assert vm.selected_code is None
