from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends

from src.dependencies import authorize_user
from src.service import update_model
from src.users import config
from src.users.models import UserCreate, User, UserRead, UserChange
from src.users.service import save_user, get_user_by_id, delete_user_from_db, add_user_to_blacklist

users_router = APIRouter(
    prefix='/users',
    tags=['users']
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


@users_router.get('/self')
async def get_user(user_id: Annotated[int, Depends(authorize_user())]) -> UserRead:
    """The view that processes user getting"""

    user = await get_user_by_id(user_id)
    return UserRead.from_orm(user)


@users_router.patch('/self')
async def change_user(user_changes: UserChange, user_id: Annotated[int, Depends(authorize_user())]) -> UserRead:
    """The view that processes user changing"""

    is_updated = await update_model(User, user_changes, User.id == user_id)
    if not is_updated:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'email'],
                                     'msg': 'this email is already in use',
                                     'type': 'value_error'}])

    return UserRead.from_orm(await get_user_by_id(user_id))


@users_router.delete('/self', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: Annotated[int, Depends(authorize_user())]) -> None:
    """The view that processes user deleting"""

    await delete_user_from_db(user_id)
    add_user_to_blacklist(user_id)
