"""Rate limiting using Memcached"""
import time
import sys
import os
import logging
import pickle
from pymemcache.client import Client
from pymemcache.exceptions import MemcacheError


class RateLimiterEntry:
    """RateLimiterEntry class to store the rate limit entry in Memcached"""
    def __init__(self, scale_seconds, number_of_requests):
        self.scale_seconds = scale_seconds
        self.number_of_requests = number_of_requests # counter for the number of requests processed.

    def reset_requests(self):
        """Reset the number of requests to zero."""
        self.number_of_requests = 0

    def increment_requests(self):
        """Increment the number of requests by one."""
        self.number_of_requests += 1

# Retrieve Memcached server address and port from environment variables
memcached_host = os.getenv('MEMCACHED_HOST', 'localhost')
memcached_port = int(os.getenv('MEMCACHED_PORT', '11211'))


######
def get_logging_level():
    """Get the logging level from the LOG_LEVEL environment variable."""
    level_str = os.getenv("LOG_LEVEL", "INFO")
    try:
        return getattr(logging, level_str.upper())
    except AttributeError:
        print(f"Invalid logging level: {level_str}. Using INFO")
        return logging.INFO
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',level=get_logging_level())
######

# Initialize the Memcached client

try:
    cache_rate_limit = Client((memcached_host, memcached_port))
except MemcacheError as e:
    logging.error(f"Failed to connect to Memcached with host <{memcached_host}> and port <{memcached_port}>: {e}")
    sys.exit(1)

def rate_limit(key :str, interval_in_secs :int, max_limit :int) -> bool:
    """Rate limit the requests based on the key, interval_in_secs, and max_limit."""
    if not isinstance(interval_in_secs, int):
        logging.error("Second argument interval_in_secs is not an integer")
        sys.exit(2)
    if not isinstance(max_limit, int):
        logging.error("Third argument max_limit is not an integer")
        sys.exit(3)

    # In order to know if a request fall into a current fixed window or in a new window
    # I'm dividing the current time (in seconds) by the rate limit window interval, rounded down.
    # The result is than compared to the cached result for the given key.
    # If the new calculated result is equal to the cached result - that means we are WITHIN the current fixed window.
    # If the new calculated result is NOT eqaul to the cached result - that means we are in a NEW fixed window

    curr_time_secs = int(time.time())
    scale_seconds = curr_time_secs // interval_in_secs
    logging.debug(f"Calculated scale_seconds: {scale_seconds}")

    try:
        # Retrieve the current rate limit entry from Memcached
        current_rate_limit = cache_rate_limit.get(key)
        if current_rate_limit:
            current_entry = pickle.loads(current_rate_limit)  # Deserialize using pickle
            logging.debug(f"current_entry.scale_seconds: {current_entry.scale_seconds}")
            if current_entry.scale_seconds == scale_seconds:
                logging.debug(f"Request is WITHIN the current fixed window. Comparing the # of processed requests within the current window {current_entry.number_of_requests} vs max-limit {max_limit}")
                if current_entry.number_of_requests >= max_limit:
                    return True
                current_entry.number_of_requests += 1
            else:
                logging.debug(f"Request is in a new fixed window - resetting the rate counter for {key}")
                reset_entry = RateLimiterEntry(scale_seconds, 1)
                current_entry = reset_entry
        else:
            logging.debug(f"API key not found - creating new RateLimiterEntry for {key}")
            new_entry = RateLimiterEntry(scale_seconds, 1)
            current_entry = new_entry

        cache_rate_limit.set(key, pickle.dumps(current_entry),expire=interval_in_secs)
        return False

    except MemcacheError as memerr:
        logging.error(f"Memcached error: {memerr}")
        return True  # Fail-safe: deny the request if there's an error with Memcached
    except pickle.PickleError as pickleerr:
        logging.error(f"Pickle error: {pickleerr}")
        return True  # Fail-safe: deny the request if there's an error with serialization
    except (TypeError, ValueError) as specificerror:
        logging.error("Type or Value error: %s", specificerror)
        return True  # Fail-safe: deny the request if there's a type or value error
    except Exception as genericerror:
        logging.error(f"Unexpected error: {genericerror}")
        return True  # Fail-safe: deny the request if there's an unexpected error


def get_balance(key: str) -> int:
    """Get the number of requests processed for the given key."""
    try:
        # Retrieve the current rate limit entry from Memcached
        current_rate_limit = cache_rate_limit.get(key)
        if current_rate_limit:
            current_entry = pickle.loads(current_rate_limit)  # Deserialize using pickle
            return int(current_entry.number_of_requests)
        # else - If no entry, assume no requests have been made:
        return 0
    except MemcacheError as memerr:
        logging.error(f"Memcached error: {memerr}")
        return 0  # Fail-safe: return 0 if there's an error with Memcached
    except pickle.PickleError as pickleerr:
        logging.error(f"Pickle error: {pickleerr}")
        return 0  # Fail-safe: return 0 if there's an error with serialization
    except (TypeError, ValueError) as specificerror:
        logging.error("Type or Value error: %s", specificerror)
        return 0  # Fail-safe: return 0 if there's a type or value error
    except Exception as genericerror:
        logging.error(f"Unexpected error: {genericerror}")
        return 0  # Fail-safe: return 0 if there's an unexpected error
