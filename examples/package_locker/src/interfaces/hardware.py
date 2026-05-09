from abc import ABC, abstractmethod


class HardwareController(ABC):
    @abstractmethod
    def open_door(self, door_code: str) -> bool:
        pass
