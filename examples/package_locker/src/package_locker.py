from src.interfaces.database import LockerDatabase
from src.interfaces.hardware import HardwareController
from src.interfaces.payment import PaymentTerminal
from datetime import datetime, timezone

FEE_TIME_LIMIT = 3
PER_DAY_CENT_FEE = 100

class PackageLocker:
    def __init__(
        self, db: LockerDatabase, payment: PaymentTerminal, hardware: HardwareController
    ):
        self.db = db
        self.payment = payment
        self.hardware = hardware

    def process_pickup(self, pickup_code: str) -> str:
        package_details = self.db.get_package_details(pickup_code)

        if not package_details:
            return "Invalid Code. Try again."

        outstanding_fee = self.calculate_fee(package_details.delivery_time)
        fee_paid = False
        
        if outstanding_fee > 0:
            if not self.payment.process_payment(outstanding_fee):
                return "Payment Failed. Try again."
            fee_paid = True

        if not self.hardware.open_door(package_details.door_code):
            message = "Hardware Error."
            if fee_paid:
                self.payment.void_transaction()
                message += "Payment refunded."
            return message

        self.db.mark_as_picked_up(pickup_code)

        return "Success. Please take your package."

    def calculate_fee(self, delivery_time: datetime):
        now = datetime.now(tz=timezone.utc)
        difference = now - delivery_time

        if difference.days < FEE_TIME_LIMIT:
            return 0
        
        return PER_DAY_CENT_FEE * (difference.days - FEE_TIME_LIMIT + 1)
    