from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class PackageDetails:
    package_id: int
    pickup_code: str
    door_code: str
    delivery_time: datetime

class LockerDatabase(ABC):
    @abstractmethod
    def get_package_details(self, pickup_code: str) -> Optional[PackageDetails]:
        pass

    @abstractmethod
    def mark_as_picked_up(self, pickup_code: str):
        pass
