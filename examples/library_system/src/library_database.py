from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

BookStatus = Literal["Available", "Checked Out", "Reference", "Lost"]


@dataclass
class Customer:
    id: str
    fines: float = 0.0
    hold_count: int = 0


@dataclass
class Book:
    id: str
    status: BookStatus = "Available"

    @property
    def is_eligible(self) -> bool:
        """A book is eligible for holds if it is not a Reference book or Lost."""
        return self.status not in ("Reference", "Lost")


class LibraryDatabase(ABC):
    @abstractmethod
    def get_customer(self, customer_id: str) -> Customer | None:
        """Returns customer details or None."""
        pass

    @abstractmethod
    def get_book(self, book_id: str) -> Book | None:
        """Returns book details or None."""
        pass

    @abstractmethod
    def add_hold(self, customer_id: str, book_id: str) -> None:
        """Adds a hold for the book for the customer."""
        pass

    @abstractmethod
    def increment_customer_hold_count(self, customer_id: str) -> None:
        """Increments the customer's active hold count by 1."""
        pass
