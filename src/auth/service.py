from fastapi_jwt_auth import AuthJWT
from sqlalchemy import delete, select, update

from src import database
from src.auth import config
from src.auth.models import RefreshToken
from src.service import execute_db_query


@AuthJWT.load_config
def get_config() -> config.AuthSettings:
    """The function that loads AuthJWT settings"""

    return config.AuthSettings()


async def save_refresh_token(token: RefreshToken) -> None:
    """The function that saves the refresh token in the database"""

    async with database.Session() as session, session.begin():
        session.add(token)


async def delete_refresh_token(token: RefreshToken) -> None:
    """The function that deletes the given refresh token from the database"""

    query = delete(RefreshToken).where(RefreshToken.user_id == token.user_id,
                                       RefreshToken.value == token.value)
    await execute_db_query(query)


async def does_refresh_token_exist(token: RefreshToken) -> bool:
    """The function that checks for the existence of the refresh token"""

    query = select(RefreshToken).where(RefreshToken.user_id == token.user_id,
                                       RefreshToken.value == token.value)
    return bool((await execute_db_query(query)).scalar())


async def update_refresh_token(token: RefreshToken, new_token_value: str) -> None:
    """The function that updates the refresh token"""

    query = update(RefreshToken).values(value=new_token_value).where(RefreshToken.user_id == token.user_id,
                                                                     RefreshToken.value == token.value)
    await execute_db_query(query)


def create_tokens_values(Authorize: AuthJWT, user_id: int, is_government_worker: bool) -> tuple[str, str]:
    """The function that creates refresh and access tokens"""

    access_token = Authorize.create_access_token(
        user_id, user_claims={'is_government_worker': is_government_worker}
    )
    refresh_token = Authorize.create_refresh_token(
        user_id, user_claims={'is_government_worker': is_government_worker})
    return access_token, refresh_token
