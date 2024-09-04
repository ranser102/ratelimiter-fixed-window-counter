""" test_ratelimit_memcached.py """
import os
import sys
import unittest.mock
import pytest

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)
from ratelimit_memcached import rate_limit, get_balance

@pytest.fixture
def mock_cache_rate_limit():
    """ Mock the cache_rate_limit function """
    with unittest.mock.patch('ratelimit_memcached.cache_rate_limit') as mock_client:
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        yield mock_client

def test_rate_limit(mock_cache_rate_limit):
    """ Test rate_limit function """
    result = rate_limit('key1', 10, 100)
    assert result is False
    mock_cache_rate_limit.get.assert_called_once_with('key1')

def test_get_balance(mock_cache_rate_limit):
    """ Test get_balance function """
    result = get_balance('key1')
    assert result == 0
    mock_cache_rate_limit.get.assert_called_once_with('key1')
