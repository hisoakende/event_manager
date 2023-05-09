from typing import Annotated

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
async def create_user(user_create: UserCreate) -> UserRead:
    """The view that processes creation the user (registration)"""

    user = User.from_orm(user_create)
    if user_create.government_key and user_create.government_key == config.GOVERNMENT_KEY:
        user.is_government_worker = True

    is_created = await create_model(user)
    if not is_created:
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

    is_updated = await update_models(User, user_changes, User.id == user_id)  # type: ignore
    if not is_updated:
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
