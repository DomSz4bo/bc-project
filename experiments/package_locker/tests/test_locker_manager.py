def test_locker_jammed_no_refund_if_no_fee(manager, mock_db, mock_payment, mock_controller):
    # Setup: No fee (<= 3 days), but door jams
    package = PackageRecord(package_id="pkg5", locker_id="L5", pickup_code="3333", storage_days=2)
    mock_db.query_package_by_code.return_value = package
    mock_controller.open_door.return_value = "Jammed"

    result = manager.pickup_package("3333")

    assert "Technical Error" in result
    mock_payment.trigger_refund.assert_not_called()
    mock_db.flag_locker_error.assert_called_once_with("L5")
import pytest
from unittest.mock import MagicMock
from src.models import PackageRecord

def test_pickup_success_no_fee(manager, mock_db, mock_controller):
    # Setup: Package within 3 days
    package = PackageRecord(package_id="pkg1", locker_id="L1", pickup_code="1234", storage_days=2)
    mock_db.query_package_by_code.return_value = package
    mock_controller.open_door.return_value = "Success"

    result = manager.pickup_package("1234")

    assert result == "Success"
    mock_controller.open_door.assert_called_once_with("L1")
    mock_db.update_package_status.assert_called_once_with("pkg1", "Picked Up")

def test_pickup_success_with_fee(manager, mock_db, mock_payment, mock_controller):
    # Setup: Package > 3 days
    package = PackageRecord(package_id="pkg2", locker_id="L2", pickup_code="5678", storage_days=5)
    mock_db.query_package_by_code.return_value = package
    mock_payment.request_payment.return_value = "TXN_001"
    mock_controller.open_door.return_value = "Success"

    result = manager.pickup_package("5678")

    assert result == "Success"
    mock_payment.request_payment.assert_called_once()
    mock_db.update_package_status.assert_called_once_with("pkg2", "Picked Up")

def test_invalid_pickup_code(manager, mock_db):
    mock_db.query_package_by_code.return_value = None

    result = manager.pickup_package("9999")

    assert "invalid" in result.lower()

def test_payment_failure(manager, mock_db, mock_payment):
    package = PackageRecord(package_id="pkg3", locker_id="L3", pickup_code="1111", storage_days=10)
    mock_db.query_package_by_code.return_value = package
    mock_payment.request_payment.return_value = None # Payment failed

    result = manager.pickup_package("1111")

    assert "payment" in result.lower()
    # Should terminate without opening door
    manager.locker_controller.open_door.assert_not_called()

def test_locker_jammed_triggers_refund_and_flag(manager, mock_db, mock_payment, mock_controller):
    # Setup: Fee paid, but door jams
    package = PackageRecord(package_id="pkg4", locker_id="L4", pickup_code="2222", storage_days=4)
    mock_db.query_package_by_code.return_value = package
    mock_payment.request_payment.return_value = "TXN_REFUND_ME"
    mock_controller.open_door.return_value = "Jammed"

    result = manager.pickup_package("2222")

    assert "Technical Error" in result
    mock_payment.trigger_refund.assert_called_once_with("TXN_REFUND_ME")
    mock_db.flag_locker_error.assert_called_once_with("L4")