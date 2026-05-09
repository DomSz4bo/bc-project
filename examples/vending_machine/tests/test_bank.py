from unittest.mock import MagicMock

import pytest

from src.bank import (
    Bank,
    ChangeAvailabilityError,
    InvalidCoinValueError,
    NegativeCoinAmountError,
)


@pytest.fixture
def bank() -> Bank:
    bank = Bank(MagicMock())
    return bank


@pytest.fixture
def full_bank() -> Bank:
    bank = Bank(MagicMock())
    bank._wallet = {10: 5, 20: 3, 50: 3, 100: 4, 200: 1}
    bank._balance = {10: 3, 20: 1, 50: 2}
    return bank


class TestBank:
    def test_add_to_balance(self, bank: Bank):
        bank.add_coin_to_balance(100)
        bank._on_balance_change.assert_called_once_with(100)
        assert bank.get_balance_sum() == 100

    def test_invalid_coin_value(self, bank: Bank):
        with pytest.raises(InvalidCoinValueError):
            bank.add_coin_to_balance(25)

    def test_balance_sum(self, bank: Bank):
        bank.add_coin_to_balance(200)
        bank.add_coin_to_balance(200)
        bank.add_coin_to_balance(100)
        bank.add_coin_to_balance(50)
        bank.add_coin_to_balance(20)
        bank.add_coin_to_balance(20)
        bank.add_coin_to_balance(10)
        bank.add_coin_to_balance(10)
        bank.add_coin_to_balance(10)

        sum = bank.get_balance_sum()
        assert sum == (200 + 200 + 100 + 50 + 20 + 20 + 10 + 10 + 10)

    def test_can_give_change(self, full_bank: Bank):
        can_give_change = full_bank.can_give_change(70)
        assert can_give_change
    
    def test_can_give_change_none(self, bank: Bank):
        can_give_zero = bank.can_give_change(0)
        assert can_give_zero

    def test_can_not_give_change(self, bank: Bank):
        can_give_change = bank.can_give_change(30)
        assert can_give_change is False

    def test_return_balance(self, full_bank: Bank):
        full_bank.return_balance()
        assert full_bank._balance == {}
        assert full_bank.get_balance_sum() == 0
        assert full_bank._wallet == {10: 2, 20: 2, 50: 1, 100: 4, 200: 1}

    def test_set_wallet(self, bank: Bank):
        new_wallet = {10: 10, 20: 5}
        bank.set_wallet(new_wallet)
        assert bank._wallet == new_wallet

    def test_dispense_change(self, full_bank: Bank):
        full_bank.dispense_change(30)
        expected_wallet = {10: 4, 20: 2, 50: 3, 100: 4, 200: 1}
        assert full_bank._wallet == expected_wallet
        assert full_bank._balance == {}
        assert full_bank.get_balance_sum() == 0

    def test_dispense_change_fail(self, bank: Bank):
        with pytest.raises(ChangeAvailabilityError):
            bank.dispense_change(100)

    def test_change_calculation(self, bank: Bank):
        bank._wallet = {10: 3, 20: 5, 50: 2, 100: 2, 200: 1}

        change1 = bank._calculate_change(20)
        assert change1 == {20: 1}

        change2 = bank._calculate_change(80)
        assert change2 == {10: 1, 20: 1, 50: 1}

        change3 = bank._calculate_change(560)
        assert change3 == {20: 3, 50: 2, 100: 2, 200: 1}

        change4 = bank._calculate_change(-20)
        assert change4 == {}

    def test_subtract_from_wallet(self, bank: Bank):
        bank._wallet = {10: 3, 20: 5, 50: 2, 100: 2, 200: 1}
        subtract = {10: 2, 20: 5, 50: 1, 100: 1, 200: 1}
        bank._subtract_from_wallet(subtract)

        expected_wallet = {10: 1, 20: 0, 50: 1, 100: 1, 200: 0}
        assert bank._wallet == expected_wallet

    def test_subtract_from_wallet_nothing(self, bank: Bank):
        original_wallet = bank._wallet
        bank._subtract_from_wallet({})
        assert bank._wallet == original_wallet

    def test_subtract_from_wallet_invalid_coin(self, full_bank: Bank):
        original_wallet = full_bank._wallet.copy()
        with pytest.raises(InvalidCoinValueError):
            full_bank._subtract_from_wallet({10: 3, 20: 1, 100: 0, 55: 1})
        assert original_wallet == full_bank._wallet

    def test_subtract_from_wallet_negative_amount(self, full_bank: Bank):
        original_wallet = full_bank._wallet.copy()
        with pytest.raises(NegativeCoinAmountError, match="Negative amount"):
            full_bank._subtract_from_wallet({10: 3, 20: 0, 100: -2})
        assert original_wallet == full_bank._wallet

    def test_subtract_from_wallet_not_enough(self, full_bank: Bank):
        original_wallet = full_bank._wallet.copy()
        with pytest.raises(NegativeCoinAmountError, match="not enough"):
            full_bank._subtract_from_wallet({10: 3, 20: 0, 100: 15})
        assert original_wallet == full_bank._wallet
