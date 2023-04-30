from typing import Annotated

from fastapi import APIRouter, HTTPException, Body, Depends, status
from fastapi_jwt_auth import AuthJWT

from src.users import config
from src.users.models import UserCreate, User, UserRead, RefreshToken
from src.users.service import save_user, get_user_by_email, save_refresh_token
from src.users.utils import verify_password

users_router = APIRouter(
    prefix='/users',
    tags=['users']
)

auth_router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


@users_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate) -> UserRead:
    """The view that processes user creation (registration)"""

    user = User.from_orm(user_create)
    if user_create.government_key and user_create.government_key == config.GOVERNMENT_KEY:
        user.is_government_worker = True

    user_id = await save_user(user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'email'],
                                     'msg': 'this email is already in use',
                                     'type': 'value_error'}])
    return UserRead.from_orm(user)


@auth_router.post('/login')
async def login(email: Annotated[str, Body()],
                password: Annotated[str, Body()],
                Authorize: Annotated[AuthJWT, Depends()]) -> dict[str, str]:
    """The view that processes login and returns access and refresh token"""

    user = await get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'email'],
                                     'msg': 'user with this email does not exist',
                                     'type': 'value_error'}])
    if not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'password'],
                                     'msg': 'incorrect password',
                                     'type': 'value_error'}])
    access_token = Authorize.create_access_token(
        user.id, user_claims={'is_government_worker': user.is_government_worker}
    )
    refresh_token = Authorize.create_refresh_token(user.id)
    await save_refresh_token(RefreshToken(user_id=user.id, token=refresh_token))

    return {'access_token': access_token, 'refresh_token': refresh_token}
