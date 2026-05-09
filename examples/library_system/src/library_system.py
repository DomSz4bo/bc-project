from src.library_database import LibraryDatabase


class LibrarySystem:
    MAX_HOLDS: int = 5

    def __init__(self, db: LibraryDatabase) -> None:
        self.db = db

    def place_hold(self, customer_id: str, book_id: str) -> str:
        customer = self.db.get_customer(customer_id)
        if not customer:
            return "Error: Customer not found."

        if customer.fines > 0:
            return "Error: Customer cannot place holds until fines are paid."

        if customer.hold_count >= self.MAX_HOLDS:
            return "Error: Customer has reached the maximum hold limit."

        book = self.db.get_book(book_id)
        if not book:
            return "Error: Book not found."

        if book.status == "Available":
            return "Message: Book is currently on the shelf and cannot be put on hold."

        if not book.is_eligible:
            return "Error: Book is not eligible for holds."

        self.db.add_hold(customer_id, book_id)
        self.db.increment_customer_hold_count(customer_id)

        return "Confirmation: Hold placed successfully."
