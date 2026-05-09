from abc import ABC, abstractmethod


class PaymentTerminal(ABC):
    @abstractmethod
    def process_payment(self, amount: float) -> bool:
        pass

    @abstractmethod
    def void_transaction(self) -> bool:
        pass
