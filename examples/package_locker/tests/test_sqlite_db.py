from datetime import datetime, timedelta

import pytest

from src.sqlite_locker_database import SQLiteLockerDatabase


@pytest.fixture
def db():
    database = SQLiteLockerDatabase(":memory:")
    yield database
    database.close()


class TestSQLiteLockerDatabase:
    def test_add_and_get_package(self, db: SQLiteLockerDatabase):
        pickup_code = "TEST1"
        door = "1"
        delivery_date = datetime.now()
        db.add_package(pickup_code, door, delivery_date)

        details = db.get_package_details(pickup_code)
        assert details is not None
        assert details.door_code == door
        assert details.delivery_time == delivery_date

    def test_mark_as_picked_up(self, db: SQLiteLockerDatabase):
        pickup_code = "PICKUP"
        db.add_package(pickup_code, 3, datetime.now())

        db.mark_as_picked_up(pickup_code)
        details = db.get_package_details(pickup_code)

        assert details is None

    def test_invalid_code(self, db: SQLiteLockerDatabase):
        assert db.get_package_details("NONEXISTENT") is None
