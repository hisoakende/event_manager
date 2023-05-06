from src import config
from src.redis_ import redis_engine


def add_user_to_blacklist(user_id: int) -> None:
    """
    The function that adds user to the blacklist

    This is necessary so that in the interval between the removal of the user
    and the expiration of the last access token, he could not make requests
    """

    redis_engine.sadd(config.USERS_BLACKLIST_NAME, user_id)
