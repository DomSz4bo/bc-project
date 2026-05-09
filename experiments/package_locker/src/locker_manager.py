from typing import Optional
from src.ports import DatabasePort, PaymentGatewayPort, LockerControllerPort

class LockerManager:
    def __init__(self, db: DatabasePort, payment_gateway: PaymentGatewayPort, locker_controller: LockerControllerPort):
        self.db = db
        self.payment_gateway = payment_gateway
        self.locker_controller = locker_controller

    def pickup_package(self, code: str) -> str:
        """
        Main entry point for picking up a package.
        Returns a status message to be displayed to the customer.
        """
        package = self.db.query_package_by_code(code)
        if not package:
            return "Invalid pickup code."

        transaction_id = None
        if package.storage_days > 3:
            # Assume a fixed rate for late fee, e.g., 5.0
            transaction_id = self.payment_gateway.request_payment(5.0)
            if not transaction_id:
                return "Payment could not be processed."

        door_result = self.locker_controller.open_door(package.locker_id)

        if door_result == "Jammed":
            if transaction_id:
                self.payment_gateway.trigger_refund(transaction_id)
            self.db.flag_locker_error(package.locker_id)
            return "Technical Error - Please contact building management"
        
        # Assume anything other than Jammed means success (per test expectations)
        self.db.update_package_status(package.package_id, "Picked Up")
        return "Success"