from fastapi import APIRouter, HTTPException

from src.auth import config
from src.auth.models import UserCreate, User, UserRead
from src.auth.service import save_user

users_router = APIRouter(
    prefix='/users',
    tags=['users']
)


@users_router.post('/', status_code=201)
async def create_user(user_create: UserCreate) -> UserRead:
    """The view that processes user creation (registration)"""

    user = User.from_orm(user_create)
    if user_create.government_key and user_create.government_key == config.government_key:
        user.is_government_worker = True

    user_id = await save_user(user)
    if user_id is None:
        raise HTTPException(status_code=422, detail=[{'loc': ['body', 'email'],
                                                      'msg': 'this email is already in use',
                                                      'type': 'value_error'}])

    return UserRead.from_orm(user)
