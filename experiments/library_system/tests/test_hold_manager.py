import pytest
from src.hold_manager import HoldManager
from unittest.mock import MagicMock

def test_place_hold_success(mock_db):
    mock_db.get_status.return_value = {'fines': 0, 'active_holds': 0, 'book_checked_out': True, 'is_reference': False}
    manager = HoldManager(mock_db)
    result = manager.place_hold('C1', 'B1')
    assert result == 'success'
    mock_db.create_hold_record.assert_called_once_with('C1', 'B1')
    mock_db.increment_hold_count.assert_called_once_with('C1')

def test_place_hold_failure_fines(mock_db):
    mock_db.get_status.return_value = {'fines': 10, 'active_holds': 0, 'book_checked_out': True, 'is_reference': False}
    manager = HoldManager(mock_db)
    result = manager.place_hold('C1', 'B1')
    assert result == 'failure: outstanding fines'

def test_place_hold_failure_max_holds(mock_db):
    mock_db.get_status.return_value = {'fines': 0, 'active_holds': 5, 'book_checked_out': True, 'is_reference': False}
    manager = HoldManager(mock_db)
    result = manager.place_hold('C1', 'B1')
    assert result == 'failure: max holds reached'

def test_place_hold_failure_available(mock_db):
    mock_db.get_status.return_value = {'fines': 0, 'active_holds': 0, 'book_checked_out': False, 'is_reference': False}
    manager = HoldManager(mock_db)
    result = manager.place_hold('C1', 'B1')
    assert result == 'failure: book is available'

def test_place_hold_failure_reference(mock_db):
    mock_db.get_status.return_value = {'fines': 0, 'active_holds': 0, 'book_checked_out': True, 'is_reference': True}
    manager = HoldManager(mock_db)
    result = manager.place_hold('C1', 'B1')
    assert result == 'failure: reference-only status'