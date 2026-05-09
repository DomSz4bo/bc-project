import pytest
from unittest.mock import MagicMock
from src.ports import DatabasePort, PaymentGatewayPort, LockerControllerPort
from src.locker_manager import LockerManager

@pytest.fixture
def mock_db():
    return MagicMock(spec=DatabasePort)

@pytest.fixture
def mock_payment():
    return MagicMock(spec=PaymentGatewayPort)

@pytest.fixture
def mock_controller():
    return MagicMock(spec=LockerControllerPort)

@pytest.fixture
def manager(mock_db, mock_payment, mock_controller):
    return LockerManager(mock_db, mock_payment, mock_controller)