from fastapi_jwt_auth import AuthJWT

from src.auth import config
from src.auth.models import RefreshToken
from src.service import receive_model


@AuthJWT.load_config
def get_config() -> config.AuthSettings:
    """The function that loads AuthJWT settings"""

    return config.AuthSettings()


async def does_refresh_token_exist(token: RefreshToken) -> bool:
    """The function that checks for the existence of the refresh token"""

    token = await receive_model(RefreshToken, RefreshToken.user_id == token.user_id,  # type: ignore
                                RefreshToken.value == token.value)  # type: ignore
    return bool(token)


def create_tokens_values(Authorize: AuthJWT, user_id: int, is_government_worker: bool) -> tuple[str, str]:
    """The function that creates refresh and access tokens"""

    access_token = Authorize.create_access_token(
        user_id, user_claims={'is_government_worker': is_government_worker}
    )
    refresh_token = Authorize.create_refresh_token(
        user_id, user_claims={'is_government_worker': is_government_worker})
    return access_token, refresh_token
