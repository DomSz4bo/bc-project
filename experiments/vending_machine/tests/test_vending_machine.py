import pytest
from unittest.mock import MagicMock

def test_successful_purchase_exact_amount(controller, mock_inventory, mock_coin_handler):
    mock_inventory.validate_availability.return_value = 1.50
    mock_inventory.dispense_product.return_value = True
    mock_coin_handler.check_change_capacity.return_value = True
    
    controller.select_product("item1")
    controller.insert_coins(1.50)
    controller.process_transaction()
    
    mock_inventory.dispense_product.assert_called_with("item1")
    # Verify return_coins was NOT called (no change due)
    mock_coin_handler.return_coins.assert_not_called()

def test_successful_purchase_with_change(controller, mock_inventory, mock_coin_handler):
    mock_inventory.validate_availability.return_value = 1.50
    mock_inventory.dispense_product.return_value = True
    mock_coin_handler.check_change_capacity.return_value = True
    
    controller.select_product("item1")
    controller.insert_coins(2.00)
    controller.process_transaction()
    
    mock_inventory.dispense_product.assert_called_with("item1")
    # Verify return_coins was called with 0.50
    mock_coin_handler.return_coins.assert_called_with(0.50)

def test_select_nonexistent_product(controller, mock_inventory):
    mock_inventory.validate_availability.return_value = None
    
    controller.select_product("nonexistent")
    assert controller.selected_product_id is None

def test_cancel_transaction(controller, mock_coin_handler):
    controller.insert_coins(1.0)
    controller.request_cancel()
    mock_coin_handler.return_coins.assert_called()

def test_insufficient_change_scenario(controller, mock_inventory, mock_coin_handler):
    mock_inventory.validate_availability.return_value = 1.0
    mock_coin_handler.check_change_capacity.return_value = False
    
    controller.select_product("item1")
    controller.insert_coins(1.0)
    controller.process_transaction()
    
    mock_coin_handler.return_coins.assert_called()
