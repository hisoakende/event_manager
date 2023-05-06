from typing import Annotated
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT

from src.auth.models import RefreshToken
from src.auth.service import does_refresh_token_exist
from src.service import is_user_in_black_list


def authorize_user(is_government_worker: bool = False,
                   refresh_token: bool = False) -> Callable:
    """The dependence that authorizes the user"""

    async def wrapper(Authorize: Annotated[AuthJWT, Depends()]) -> int:
        user_id = Authorize.get_jwt_subject()
        if refresh_token:
            Authorize.jwt_refresh_token_required()

            token = RefreshToken(user_id=user_id, value=Authorize._token)
            if not (await does_refresh_token_exist(token)):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail=[{'loc': ['headers', 'token'],
                                             'msg': 'invalid token',
                                             'type': 'value_error'}])
        else:
            Authorize.jwt_required()

        if is_user_in_black_list(user_id):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=[{'loc': ['headers', 'token'],
                                         'msg': 'invalid token',
                                         'type': 'value_error'}])

        user_is_government_worker = Authorize.get_raw_jwt()['is_government_worker']
        if is_government_worker and not user_is_government_worker:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=[{'loc': ['headers', 'token'],
                                         'msg': 'you do not have rights to this resource',
                                         'type': 'value_error'}])
        return user_id

    return wrapper
