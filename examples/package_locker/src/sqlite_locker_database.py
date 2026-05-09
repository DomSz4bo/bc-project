import sqlite3
from datetime import datetime

from src.interfaces.database import LockerDatabase, PackageDetails


class SQLiteLockerDatabase(LockerDatabase):
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS packages (
                    pickup_code TEXT,
                    door_code TEXT,
                    status TEXT,
                    delivery_date TIMESTAMP
                )
            """)

    def add_package(self, pickup_code: str, door_code: str, delivery_date: datetime):
        with self.conn:
            self.conn.execute(
                "INSERT INTO packages (pickup_code, door_code, status, delivery_date) VALUES (?, ?, ?, ?)",
                (pickup_code, door_code, "pending", delivery_date.isoformat()),
            )

    def get_package_details(self, pickup_code: str) -> PackageDetails | None:
        cursor = self.conn.execute(
            "SELECT rowid, pickup_code, door_code, delivery_date FROM packages WHERE pickup_code = ? AND status = 'pending'",
            (pickup_code,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        delivery_time = datetime.fromisoformat(row["delivery_date"])
        return PackageDetails(
            package_id=row["rowid"],
            pickup_code=row["pickup_code"],
            door_code=row["door_code"],
            delivery_time=delivery_time,
        )

    def mark_as_picked_up(self, pickup_code: str):
        with self.conn:
            self.conn.execute(
                "UPDATE packages SET status = 'picked_up' WHERE pickup_code = ?",
                (pickup_code,),
            )

    def close(self):
        self.conn.close()
