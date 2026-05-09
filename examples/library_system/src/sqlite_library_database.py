import sqlite3

from src.library_database import Book, Customer, LibraryDatabase


class SQLiteLibraryDatabase(LibraryDatabase):
    def __init__(self, db_path: str = ":memory:"):
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                fines REAL DEFAULT 0.0,
                hold_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'Available'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT,
                book_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(customer_id) REFERENCES customers(id),
                FOREIGN KEY(book_id) REFERENCES books(id)
            )
        """)
        self.connection.commit()

    def get_customer(self, customer_id: str) -> Customer | None:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        if row:
            return Customer(
                id=row["id"], fines=row["fines"], hold_count=row["hold_count"]
            )
        return None

    def get_book(self, book_id: str) -> Book | None:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        if row:
            return Book(id=row["id"], status=row["status"])
        return None

    def add_hold(self, customer_id: str, book_id: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO holds (customer_id, book_id) VALUES (?, ?)",
            (customer_id, book_id),
        )
        self.connection.commit()

    def increment_customer_hold_count(self, customer_id: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE customers SET hold_count = hold_count + 1 WHERE id = ?",
            (customer_id,),
        )
        self.connection.commit()
