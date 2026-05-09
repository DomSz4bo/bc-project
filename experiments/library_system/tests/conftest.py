import pytest
from unittest.mock import MagicMock
from src.interfaces import LibraryDatabasePort

@pytest.fixture
def mock_db():
    return MagicMock(spec=LibraryDatabasePort)