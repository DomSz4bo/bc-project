from unittest.mock import MagicMock

import pytest

from src.library_database import Book, Customer, LibraryDatabase
from src.library_system import LibrarySystem


@pytest.fixture
def mock_db():
    return MagicMock(spec=LibraryDatabase)


@pytest.fixture
def system(mock_db):
    return LibrarySystem(mock_db)


class TestLibrarySystem:
    def test_place_hold_success(self, system: LibrarySystem, mock_db: LibraryDatabase):
        mock_db.get_customer.return_value = Customer(id="C1", fines=0.0, hold_count=0)
        mock_db.get_book.return_value = Book(id="B1", status="Checked Out")

        result = system.place_hold("C1", "B1")

        assert result == "Confirmation: Hold placed successfully."
        mock_db.add_hold.assert_called_once_with("C1", "B1")
        mock_db.increment_customer_hold_count.assert_called_once_with("C1")

    def test_place_hold_customer_not_found(
        self, system: LibrarySystem, mock_db: LibraryDatabase
    ):
        mock_db.get_customer.return_value = None
        result = system.place_hold("C1", "B1")
        assert result == "Error: Customer not found."
        mock_db.add_hold.assert_not_called()
        mock_db.increment_customer_hold_count.assert_not_called()

    def test_place_hold_unpaid_fines(
        self, system: LibrarySystem, mock_db: LibraryDatabase
    ):
        mock_db.get_customer.return_value = Customer(id="C1", fines=10.0, hold_count=0)
        result = system.place_hold("C1", "B1")
        assert result == "Error: Customer cannot place holds until fines are paid."
        mock_db.add_hold.assert_not_called()
        mock_db.increment_customer_hold_count.assert_not_called()

    def test_place_hold_max_limit_reached(
        self, system: LibrarySystem, mock_db: LibraryDatabase
    ):
        mock_db.get_customer.return_value = Customer(id="C1", fines=0.0, hold_count=5)
        result = system.place_hold("C1", "B1")
        assert result == "Error: Customer has reached the maximum hold limit."
        mock_db.add_hold.assert_not_called()
        mock_db.increment_customer_hold_count.assert_not_called()

    def test_place_hold_book_not_found(
        self, system: LibrarySystem, mock_db: LibraryDatabase
    ):
        mock_db.get_customer.return_value = Customer(id="C1", fines=0.0, hold_count=0)
        mock_db.get_book.return_value = None
        result = system.place_hold("C1", "B1")
        assert result == "Error: Book not found."
        mock_db.add_hold.assert_not_called()
        mock_db.increment_customer_hold_count.assert_not_called()

    def test_place_hold_book_available(
        self, system: LibrarySystem, mock_db: LibraryDatabase
    ):
        mock_db.get_customer.return_value = Customer(id="C1", fines=0.0, hold_count=0)
        mock_db.get_book.return_value = Book(id="B1", status="Available")
        result = system.place_hold("C1", "B1")
        assert (
            result
            == "Message: Book is currently on the shelf and cannot be put on hold."
        )
        mock_db.add_hold.assert_not_called()
        mock_db.increment_customer_hold_count.assert_not_called()

    def test_place_hold_book_not_eligible(
        self, system: LibrarySystem, mock_db: LibraryDatabase
    ):
        mock_db.get_customer.return_value = Customer(id="C1", fines=0.0, hold_count=0)
        mock_db.get_book.return_value = Book(id="B1", status="Reference")
        result = system.place_hold("C1", "B1")
        assert result == "Error: Book is not eligible for holds."
        mock_db.add_hold.assert_not_called()
        mock_db.increment_customer_hold_count.assert_not_called()
