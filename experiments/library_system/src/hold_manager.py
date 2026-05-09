SYSTEM_MAX_HOLDS = 5
from .interfaces import LibraryDatabasePort

class HoldManager:
    def __init__(self, db: LibraryDatabasePort) -> None:
        self.db = db

    def place_hold(self, customer_id: str, book_id: str) -> str:
        status = self.db.get_status(customer_id, book_id)

        if status.get('fines', 0) > 0:
            return 'failure: outstanding fines'
        
        # Use SYSTEM_MAX_HOLDS constant
        if status.get('active_holds', 0) >= SYSTEM_MAX_HOLDS:
            return 'failure: max holds reached'
        
        if not status.get('book_checked_out', False):
            return 'failure: book is available'
            
        if status.get('is_reference', False):
            return 'failure: reference-only status'
            
        self.db.create_hold_record(customer_id, book_id)
        self.db.increment_hold_count(customer_id)
        
        return 'success'