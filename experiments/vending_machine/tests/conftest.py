import pytest
from unittest.mock import MagicMock
from src.ports import InventoryPort, CoinHandlerPort
from src.vending_machine_controller import VendingMachineController

@pytest.fixture
def mock_inventory():
    return MagicMock(spec=InventoryPort)

@pytest.fixture
def mock_coin_handler():
    return MagicMock(spec=CoinHandlerPort)

@pytest.fixture
def controller(mock_inventory, mock_coin_handler):
    return VendingMachineController(mock_inventory, mock_coin_handler)