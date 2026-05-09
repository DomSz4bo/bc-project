import pytest

from src.sqlite_library_database import SQLiteLibraryDatabase


@pytest.fixture
def sqlite_db():
    return SQLiteLibraryDatabase(":memory:")


class TestSQLiteLibraryDatabase:
    def test_create_schema(self, sqlite_db: SQLiteLibraryDatabase):
        cursor = sqlite_db.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row["name"] for row in cursor.fetchall()}
        assert "customers" in tables
        assert "books" in tables
        assert "holds" in tables

    def test_get_customer_not_found(self, sqlite_db: SQLiteLibraryDatabase):
        assert sqlite_db.get_customer("C1") is None

    def test_get_customer_found(self, sqlite_db: SQLiteLibraryDatabase):
        cursor = sqlite_db.connection.cursor()
        cursor.execute(
            "INSERT INTO customers (id, fines, hold_count) VALUES (?, ?, ?)",
            ("C1", 0.0, 2),
        )
        customer = sqlite_db.get_customer("C1")
        assert customer.id == "C1"
        assert customer.fines == 0.0
        assert customer.hold_count == 2

    def test_get_book_not_found(self, sqlite_db: SQLiteLibraryDatabase):
        assert sqlite_db.get_book("B1") is None

    def test_get_book_found(self, sqlite_db: SQLiteLibraryDatabase):
        cursor = sqlite_db.connection.cursor()
        cursor.execute(
            "INSERT INTO books (id, status) VALUES (?, ?)", ("B1", "Checked Out")
        )
        book = sqlite_db.get_book("B1")
        assert book.id == "B1"
        assert book.status == "Checked Out"
        assert book.is_eligible is True

    def test_add_hold(self, sqlite_db: SQLiteLibraryDatabase):
        sqlite_db.add_hold("C1", "B1")
        cursor = sqlite_db.connection.cursor()
        cursor.execute("SELECT * FROM holds")
        hold = cursor.fetchone()
        assert hold["customer_id"] == "C1"
        assert hold["book_id"] == "B1"

    def test_hold_queue_order(self, sqlite_db: SQLiteLibraryDatabase):
        """Verify that multiple holds on the same book maintain their insertion order."""
        sqlite_db.add_hold("C1", "B1")
        sqlite_db.add_hold("C2", "B1")
        sqlite_db.add_hold("C3", "B1")

        cursor = sqlite_db.connection.cursor()
        cursor.execute("SELECT customer_id FROM holds WHERE book_id = ? ORDER BY created_at ASC, id ASC", ("B1",))
        holds = [row["customer_id"] for row in cursor.fetchall()]

        assert holds == ["C1", "C2", "C3"]

    def test_increment_customer_hold_count(self, sqlite_db: SQLiteLibraryDatabase):
        cursor = sqlite_db.connection.cursor()
        cursor.execute(
            "INSERT INTO customers (id, hold_count) VALUES (?, ?)", ("C1", 0)
        )
        sqlite_db.increment_customer_hold_count("C1")
        customer = sqlite_db.get_customer("C1")
        assert customer.hold_count == 1
