from fastapi import APIRouter, HTTPException, status

from src.users import config
from src.users.models import UserCreate, User, UserRead
from src.users.service import save_user

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
