from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.interfaces.database import LockerDatabase, PackageDetails
from src.interfaces.hardware import HardwareController
from src.interfaces.payment import PaymentTerminal
from src.package_locker import PackageLocker


@pytest.fixture
def mock_db():
    return MagicMock(spec=LockerDatabase)


@pytest.fixture
def mock_payment():
    return MagicMock(spec=PaymentTerminal)


@pytest.fixture
def mock_hardware():
    return MagicMock(spec=HardwareController)


@pytest.fixture
def locker(mock_db, mock_payment, mock_hardware):
    return PackageLocker(mock_db, mock_payment, mock_hardware)


class TestPackageLocker:
    def test_success_no_fee(
        self,
        locker: PackageLocker,
        mock_db: LockerDatabase,
        mock_hardware: HardwareController,
    ):
        delivery_time = datetime.now(tz=timezone.utc)
        pickup_code = "123456"
        details = PackageDetails(12, pickup_code, "55", delivery_time)
        mock_db.get_package_details.return_value = details
        mock_hardware.open_door.return_value = True

        result = locker.process_pickup(pickup_code)

        assert "Success" in result
        mock_db.get_package_details.assert_called_with(pickup_code)
        mock_hardware.open_door.assert_called_with("55")
        mock_db.mark_as_picked_up.assert_called_with(pickup_code)

    def test_success_with_fee(
        self,
        locker: PackageLocker,
        mock_db: LockerDatabase,
        mock_payment: PaymentTerminal,
        mock_hardware: HardwareController,
    ):
        pickup_code = "654321"
        delivery_time = datetime(2025, 5, 9, 12, 30, tzinfo=timezone.utc)
        details = PackageDetails(12, pickup_code, "123", delivery_time)
        mock_db.get_package_details.return_value = details
        mock_payment.process_payment.return_value = True
        mock_hardware.open_door.return_value = True

        result = locker.process_pickup(pickup_code)

        assert "Success" in result
        mock_payment.process_payment.assert_called_once()
        mock_hardware.open_door.assert_called_with("123")
        mock_db.mark_as_picked_up.assert_called_with(pickup_code)

    def test_invalid_code(
        self, locker: PackageLocker, mock_db: LockerDatabase, mock_hardware
    ):
        pickup_code = "000000"
        mock_db.get_package_details.return_value = None

        result = locker.process_pickup(pickup_code)

        assert "Invalid Code" in result
        mock_hardware.open_door.assert_not_called()
        mock_db.mark_as_picked_up.assert_not_called()

    def test_payment_declined(
        self,
        locker: PackageLocker,
        mock_db: LockerDatabase,
        mock_payment: PaymentTerminal,
        mock_hardware: HardwareController,
    ):
        pickup_code = "111222"
        delivery_time = datetime(2025, 5, 9, 12, 30, tzinfo=timezone.utc)
        details = PackageDetails(666, pickup_code, "939", delivery_time)
        mock_db.get_package_details.return_value = details
        mock_payment.process_payment.return_value = False

        result = locker.process_pickup(pickup_code)

        assert "Payment Failed" in result
        mock_hardware.open_door.assert_not_called()
        mock_db.mark_as_picked_up.assert_not_called()

    def test_hardware_jam_no_fee(
        self,
        locker: PackageLocker,
        mock_db: LockerDatabase,
        mock_hardware: HardwareController,
        mock_payment: PaymentTerminal,
    ):
        pickup_code = "333444"
        delivery_time = datetime.now(tz=timezone.utc)
        details = PackageDetails(4545, pickup_code, "404040", delivery_time)
        mock_db.get_package_details.return_value = details
        mock_hardware.open_door.return_value = False

        result = locker.process_pickup(pickup_code)

        assert "Hardware Error" in result
        mock_payment.void_transaction.assert_not_called()
        mock_db.mark_as_picked_up.assert_not_called()

    def test_hardware_jam_with_fee_void(
        self,
        locker: PackageLocker,
        mock_db: LockerDatabase,
        mock_hardware: HardwareController,
        mock_payment: PaymentTerminal,
    ):
        pickup_code = "5A56B6"
        delivery_time = datetime(2026, 1, 20, 11, 39, tzinfo=timezone.utc)
        details = PackageDetails(3344, pickup_code, "0022AB", delivery_time)
        mock_db.get_package_details.return_value = details
        mock_payment.process_payment.return_value = True
        mock_hardware.open_door.return_value = False

        result = locker.process_pickup(pickup_code)

        assert "Hardware Error" in result
        mock_payment.void_transaction.assert_called_once()
        mock_db.mark_as_picked_up.assert_not_called()
