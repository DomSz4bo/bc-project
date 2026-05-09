from dataclasses import dataclass
from typing import Optional

@dataclass
class PackageRecord:
    package_id: str
    locker_id: str
    pickup_code: str
    storage_days: int
    last_transaction_id: Optional[str] = None