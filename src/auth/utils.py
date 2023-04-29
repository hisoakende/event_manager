import hashlib
import random
import string


def get_random_string(length: int = 10) -> str:
    """The function that generates a random string of a given length"""

    return ''.join(random.choices(string.ascii_letters, k=length))


def hash_password(password: str, salt: str) -> str:
    """The function that hashes password with the given salt"""

    hashed_password = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return hashed_password.hex()
