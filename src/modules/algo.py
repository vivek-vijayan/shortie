import os
import time
import random
#rom random import random
import string
import mmh3
import dotenv
import logging
import hashlib
from typing import Optional
from bitarray import bitarray

class Environ:
    """
    A class to manage environment variables from .env file or OS environment.
    """

    def __init__(self) -> None:
        """Initializes the environment object."""
        self.env_loaded: bool = False

    def load_from_dotenv(self, env_path: Optional[str] = None) -> bool:
        """
        Loads environment variables from a .env file.

        Args:
            env_path (str, optional): Path to .env file. Defaults to None.

        Returns:
            bool: True if loading succeeds.
        """
        try:
            dotenv.load_dotenv(dotenv_path=env_path)
            self.env_loaded = True
            logging.info("[ENVIRON] Dotenv file loaded successfully.")
            return True
        except Exception as e:
            logging.error(f"[ENVIRON] Failed to load dotenv: {e}")
            return False

    def get(self, key: str) -> str:
        """
        Retrieves an environment variable by key.

        Args:
            key (str): Environment variable key.

        Returns:
            str: Value of the environment variable or empty string if not found.
        """
        value = os.getenv(key)
        if value:
            return value
        logging.warning(f"[ENVIRON] Environment variable '{key}' not found.")
        return ""


class BloomFilter:
    """
    A simple Bloom Filter implementation using bitarray and MurmurHash (mmh3).
    
    A Bloom filter is a space-efficient probabilistic data structure used to test
    whether an element is a member of a set. False positives are possible, but false
    negatives are not.
    """

    def __init__(self, size: int, hash_size: int) -> None:
        """
        Initialize the Bloom filter.

        Args:
            size (int): The size of the bit array.
            hash_size (int): The number of hash functions to use.
        """
        self.size = size
        self.hash_size = hash_size
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)  # Initialize all bits to 0

    def add(self, value: str) -> bool:
        """
        Add a value to the Bloom filter.

        Args:
            value (str): The value object to be added.

        Returns:
            bool: True if added successfully.
        """
        for seed in range(self.hash_size):
            # Generate a hash for the value with a given seed
            index = mmh3.hash(value, seed) % self.size
            self.bit_array[index] = 1  # Set the bit at the calculated index

        return True

    def check(self, value: str) -> bool:
        """
        Check if a value is possibly in the Bloom filter.

        Args:
            value (str): The value object to check.

        Returns:
            bool: False if definitely not present, True if possibly present.
        """
        for seed in range(self.hash_size):
            index = mmh3.hash(value, seed) % self.size
            if self.bit_array[index] == 0:
                return False  # At least one bit is not set → definitely not in the set

        return True  # All bits are set → possibly in the set


class EncryptHash:
    """
    A utility class to generate short, Base62-encoded hash-based identifiers
    for given input strings (e.g., URLs). Useful for applications like 
    URL shorteners.
    """

    def __init__(self, size: int) -> None:
        """
        Initialize the EncryptHash class.

        Args:
            size (int): Desired length of the generated short ID.
        """
        self.hash_size: int = size
        self.BASE62 = string.ascii_letters + string.digits  # Base62 charset: a-zA-Z0-9

    def base62_encode(self, num: int) -> str:
        """
        Encode an integer into a Base62 string.

        Args:
            num (int): Integer to encode.

        Returns:
            str: Base62-encoded string.
        """
        if num == 0:
            return self.BASE62[0]
        
        encoded = ''
        while num > 0:
            num, rem = divmod(num, 62)
            encoded = self.BASE62[rem] + encoded
        
        return encoded

    

    def generate_short_id(self, original_url: str) -> str:
        """
        Generate a short, deterministic ID from the input string (e.g., URL).

        Args:
            original_url (str): The input string to hash.

        Returns:
            str: A Base62-encoded short ID of specified length.
        """
        salt = f"{time.time()}{random.randint(1000, 9999)}" # type: ignore
        combined = original_url + salt
        sha256_hash = hashlib.sha256(combined.encode()).digest()
        partial_hash = int.from_bytes(sha256_hash[:self.hash_size], 'big')
        short_id: str = self.base62_encode(partial_hash)
        return short_id[:self.hash_size]