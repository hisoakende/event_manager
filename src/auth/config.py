import os

from pydantic import BaseModel


class AuthSettings(BaseModel):
    authjwt_secret_key: str = os.getenv('AUTHJWT_KEY')  # type: ignore
    authjwt_access_token_expires: int = 1800  # 30 minutes
    authjwt_refresh_token_expires: int = 5_184_000  # 60 days
