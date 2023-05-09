from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from starlette import status

from src.auth.models import TokensResponseModel, RefreshToken
from src.auth.service import create_tokens_values
from src.dependencies import authorize_user
from src.service import delete_models, update_models, create_model, receive_model
from src.users.models import User
from src.users.utils import verify_password

auth_router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

AuthorizeUserRefreshDep = Annotated[int, Depends(authorize_user(refresh_token=True))]


@auth_router.post('/login/')
async def login(email: Annotated[str, Body()],
                password: Annotated[str, Body()],
                Authorize: Annotated[AuthJWT, Depends()]) -> TokensResponseModel:
    """The view that processes login and returns access and refresh token"""

    user = await receive_model(User, User.email == email)  # type: ignore
    if user is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'email'],
                                     'msg': 'user with this email does not exist',
                                     'type': 'value_error'}])
    if not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'password'],
                                     'msg': 'invalid password',
                                     'type': 'value_error'}])

    access_token, refresh_token = create_tokens_values(Authorize, user.id, user.is_government_worker)  # type: ignore
    await create_model(RefreshToken(user_id=user.id, value=refresh_token))

    return TokensResponseModel.parse_obj({'access_token': access_token, 'refresh_token': refresh_token})


@auth_router.post('/logout/', status_code=status.HTTP_204_NO_CONTENT)
async def logout(user_id: AuthorizeUserRefreshDep,
                 Authorize: Annotated[AuthJWT, Depends()]) -> None:
    """The view that processes logout user"""

    await delete_models(RefreshToken, RefreshToken.user_id == user_id,  # type: ignore
                        RefreshToken.value == Authorize._token)


@auth_router.post('/refresh/')
async def update_access_token(user_id: AuthorizeUserRefreshDep,
                              Authorize: Annotated[AuthJWT, Depends()]) -> TokensResponseModel:
    """The view that processes updating expired access token"""

    user_is_government_worker = Authorize.get_raw_jwt()['is_government_worker']
    new_access_token, new_refresh_token = create_tokens_values(Authorize, user_id, user_is_government_worker)
    token = RefreshToken(user_id=user_id, value=new_refresh_token)
    await update_models(RefreshToken, token, RefreshToken.user_id == user_id,  # type: ignore
                        RefreshToken.value == Authorize._token)

    return TokensResponseModel.parse_obj({'access_token': new_access_token, 'refresh_token': new_refresh_token})
