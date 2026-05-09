from typing import Callable, Any

ALLOWED_COINS = [200, 100, 50, 20, 10]


class Bank:
    def __init__(self, on_balance_change: Callable[[int], Any]):
        self._wallet: dict[int, int] = {}
        self._balance: dict[int, int] = {}
        self._on_balance_change = on_balance_change

    def set_wallet(self, wallet: dict[int, int]):
        self._wallet = wallet

    def return_balance(self):
        self._subtract_from_wallet(self._balance)
        self._reset_balance()

    def add_coin_to_balance(self, value):
        if value not in ALLOWED_COINS:
            raise InvalidCoinValueError(f"Received coin of disallowed value: {value}")

        self._balance[value] = self._balance.get(value, 0) + 1
        self._wallet[value] = self._wallet.get(value, 0) + 1
        if self._on_balance_change:
            self._on_balance_change(self.get_balance_sum())

    def get_balance_sum(self) -> int:
        balance_sum = 0
        for coin_value, number in self._balance.items():
            balance_sum += number * coin_value

        return balance_sum

    def can_give_change(self, amount: int) -> bool:
        if amount == 0:
            return True

        change = self._calculate_change(amount)
        return bool(change)

    def dispense_change(self, amount: int):
        change = self._calculate_change(amount)
        if not change and amount != 0:
            raise ChangeAvailabilityError(
                f"Can not provide change in required amount ({amount})."
            )
        self._subtract_from_wallet(change)
        self._reset_balance()

    def _reset_balance(self):
        self._balance = {}

    def _calculate_change(self, amount: int) -> dict[int, int]:
        if amount <= 0:
            return {}

        remaining = amount
        change = {}

        for coin_value, number in sorted(
            self._wallet.items(), key=lambda x: x[0], reverse=True
        ):
            use = min(remaining // coin_value, number)

            if use > 0:
                change[coin_value] = use
                remaining -= use * coin_value

            if not remaining:
                return change

        return {}

    def _subtract_from_wallet(self, amounts: dict[int, int]):
        if not amounts:
            return

        result_wallet = self._wallet.copy()

        for coin_value, amount in amounts.items():
            if coin_value not in ALLOWED_COINS:
                raise InvalidCoinValueError(f"Disallowed coin value: {coin_value}.")
            if amount < 0:
                raise NegativeCoinAmountError(
                    f"Negative amount for coin of value {coin_value}."
                )

            new_amount = result_wallet.get(coin_value, 0) - amount
            if new_amount < 0:
                raise NegativeCoinAmountError(
                    f"There is not enough coins of value {coin_value}."
                )

            result_wallet[coin_value] = new_amount

        self._wallet = result_wallet


class BankException(Exception):
    pass


class InvalidCoinValueError(BankException):
    pass


class NegativeCoinAmountError(BankException):
    pass


class ChangeAvailabilityError(BankException):
    pass
