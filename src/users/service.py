import uuid as uuid_pkg

from src import config
from src.redis_ import redis_engine


def add_user_to_blacklist(user_id: int) -> None:
    """
    The function that adds user to the blacklist in redis

    This is necessary so that in the interval between the removal of the user
    and the expiration of the last access token, he could not make requests
    """

    redis_engine.sadd(config.USERS_BLACKLIST_NAME, user_id)


def set_password_recovery_data(recovery_uuid: uuid_pkg.UUID, user_id: int) -> None:
    """The function that saves the user id for password recovery in redis"""

    redis_engine.set(str(recovery_uuid), user_id, ex=1800)


def receive_password_recovery_data(recovery_uuid: uuid_pkg.UUID) -> str | None:
    """The function that returns the user id for password recovery from redis"""

    return redis_engine.get(str(recovery_uuid))


def delete_password_recovery_data(recovery_uuid: uuid_pkg.UUID) -> None:
    """The function that deletes the user id for password recovery from redis"""

    redis_engine.delete(str(recovery_uuid))
