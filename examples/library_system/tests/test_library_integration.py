import pytest

from src.library_system import LibrarySystem
from src.sqlite_library_database import SQLiteLibraryDatabase


@pytest.fixture
def db():
    return SQLiteLibraryDatabase(":memory:")


@pytest.fixture
def system(db: SQLiteLibraryDatabase):
    cursor = db.connection.cursor()
    cursor.execute(
        "INSERT INTO customers (id, fines, hold_count) VALUES (?, ?, ?)", ("C1", 0.0, 0)
    )
    cursor.execute(
        "INSERT INTO books (id, status) VALUES (?, ?)", ("B1", "Checked Out")
    )
    db.connection.commit()
    return LibrarySystem(db)


class TestLibrarySqliteIntegration:
    def test_integration_place_hold_success(
        self, system: LibrarySystem, db: SQLiteLibraryDatabase
    ):
        result = system.place_hold("C1", "B1")

        assert result == "Confirmation: Hold placed successfully."

        customer = db.get_customer("C1")
        assert customer.hold_count == 1

        cursor = db.connection.cursor()
        cursor.execute(
            "SELECT * FROM holds WHERE customer_id = ? AND book_id = ?", ("C1", "B1")
        )
        assert cursor.fetchone() is not None

    def test_integration_place_hold_failure_fines(
        self, system: LibrarySystem, db: SQLiteLibraryDatabase
    ):
        cursor = db.connection.cursor()
        cursor.execute("UPDATE customers SET fines = 10.0 WHERE id = 'C1'")
        db.connection.commit()

        result = system.place_hold("C1", "B1")

        assert "Error" in result

        customer = db.get_customer("C1")
        assert customer.hold_count == 0

        cursor = db.connection.cursor()
        cursor.execute(
            "SELECT * FROM holds WHERE customer_id = ? AND book_id = ?", ("C1", "B1")
        )
        assert cursor.fetchone() is None
