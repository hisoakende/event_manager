import hashlib
import random
import string

from src.users import config


def get_random_string(length: int = 10) -> str:
    """The function that generates a random string of the given length"""

    return ''.join(random.choices(string.ascii_letters, k=length))


def hash_password(password: str, salt: str) -> str:
    """The function that hashes password with the given salt"""

    hashed_password = hashlib.pbkdf2_hmac(config.HASH_ALGORITHM, password.encode(),
                                          salt.encode(), config.HASH_ITERATIONS_COUNT)
    return hashed_password.hex()


def verify_password(password: str, hashed_password: str) -> bool:
    """
    The function that verifies password

    It compares the hash from database with the hash of the given password
    """

    salt, hash_ = hashed_password.split('$')
    return hash_password(password, salt) == hash_
