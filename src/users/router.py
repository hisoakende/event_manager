from typing import Annotated

from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, HTTPException, status, Depends

from src.dependencies import authorize_user
from src.service import update_models, delete_models, create_model, receive_model
from src.users import config
from src.users.models import UserCreate, User, UserRead, UserUpdate
from src.users.service import add_user_to_blacklist

users_router = APIRouter(
    prefix='/users',
    tags=['users']
)

AuthorizeUserDep = Annotated[int, Depends(authorize_user())]


@users_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate) -> UserRead:
    """The view that processes creation the user (registration)"""

    user = User.from_orm(user_data)
    if user_data.government_key and user_data.government_key == config.GOVERNMENT_KEY:
        user.is_government_worker = True

    try:
        await create_model(user)
    except UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'email'],
                                     'msg': 'this email is already in use',
                                     'type': 'value_error'}])
    return UserRead.from_orm(user)


@users_router.get('/self/')
async def receive_user(user_id: AuthorizeUserDep) -> UserRead:
    """The view that processes getting the user"""

    user = await receive_model(User, User.id == user_id)  # type: ignore
    return UserRead.from_orm(user)


@users_router.patch('/self/')
async def update_user(user_changes: UserUpdate, user_id: AuthorizeUserDep) -> UserRead:
    """The view that processes updating the user"""

    try:
        await update_models(User, user_changes, User.id == user_id)  # type: ignore
    except UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'email'],
                                     'msg': 'this email is already in use',
                                     'type': 'value_error'}])

    return UserRead.from_orm(await receive_model(User, User.id == user_id))  # type: ignore


@users_router.delete('/self/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: AuthorizeUserDep) -> None:
    """The view that processes deleting the user"""

    await delete_models(User, User.id == user_id)  # type: ignore
    add_user_to_blacklist(user_id)
