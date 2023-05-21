import uuid as uuid_pkg
from typing import Annotated

from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, HTTPException, status, Depends, Body, BackgroundTasks, Request
from pydantic import EmailStr

from src.dependencies import authorize_user
from src.service import update_models, delete_models, create_model, receive_model, receive_unconfirmed_email_data, \
    set_unconfirmed_email_data, send_email, delete_unconfirmed_email_data
from src.users import config
from src.users.email_messages import ConfirmUserEmailEmailMessage, RecoveryPasswordEmailMessage
from src.users.models import UserCreate, User, UserRead, UserUpdate
from src.users.service import add_user_to_blacklist, set_password_recovery_data, receive_password_recovery_data, \
    delete_password_recovery_data

users_router = APIRouter(
    prefix='/users',
    tags=['users']
)

AuthorizeUserDep = Annotated[int, Depends(authorize_user())]


@users_router.post('/', status_code=status.HTTP_204_NO_CONTENT)
async def create_user(user_data: UserCreate, background_task: BackgroundTasks) -> None:
    """
    The view that processes creation the user (registration)

    Sends email message with confirmation uuid to confirm email and to create user
    """

    user = User.from_orm(user_data)
    if user_data.government_key and user_data.government_key == config.GOVERNMENT_KEY:
        user.is_government_worker = True

    user_with_this_email = await receive_model(User, User.email == user_data.email)  # type: ignore
    if user_with_this_email is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'email'],
                                     'msg': 'this email is already in use',
                                     'type': 'value_error'}])

    confirmation_uuid = uuid_pkg.uuid4()
    set_unconfirmed_email_data(confirmation_uuid, user)
    background_task.add_task(send_email, ConfirmUserEmailEmailMessage(user, confirmation_uuid))


@users_router.get('/self/')
async def receive_user(user_id: AuthorizeUserDep) -> UserRead:
    """The view that processes getting the user"""

    user = await receive_model(User, User.id == user_id)  # type: ignore
    return UserRead.from_orm(user)


@users_router.patch('/self/')
async def update_user(user_changes: UserUpdate, user_id: AuthorizeUserDep) -> UserRead:
    """The view that processes updating the user"""

    await update_models(User, user_changes, User.id == user_id)  # type: ignore
    return UserRead.from_orm(await receive_model(User, User.id == user_id))  # type: ignore


@users_router.delete('/self/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: AuthorizeUserDep) -> None:
    """The view that processes deleting the user"""

    await delete_models(User, User.id == user_id)  # type: ignore
    add_user_to_blacklist(user_id)


@users_router.post('/email-confirmation/', status_code=status.HTTP_201_CREATED)
async def confirm_email(confirmation_uuid: Annotated[uuid_pkg.UUID, Body(embed=True)]) -> UserRead:
    """The view that processes email confirmation and, if successful, creates the user"""

    user = receive_unconfirmed_email_data(confirmation_uuid, User)
    if user is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'confirmation_uuid'],
                                     'msg': 'invalid value',
                                     'type': 'value_error'}])
    delete_unconfirmed_email_data(confirmation_uuid, User)

    try:
        await create_model(user)
    except UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'email'],
                                     'msg': 'this email is already in use',
                                     'type': 'value_error'}])
    return UserRead.from_orm(user)


@users_router.post('/password-recovery/', status_code=status.HTTP_204_NO_CONTENT)
async def send_recovery_uuid(email: Annotated[EmailStr, Body(embed=True)],
                             background_task: BackgroundTasks,
                             request: Request) -> None:
    """The view that processes password recovery sends the email message with the recovery link"""

    user = await receive_model(User, User.email == email)  # type: ignore
    if user is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'email'],
                                     'msg': 'user with this email not found',
                                     'type': 'value_error'}])
    recovery_uuid = uuid_pkg.uuid4()
    set_password_recovery_data(recovery_uuid, user.id)  # type: ignore

    recovery_url = str(request.url) + str(recovery_uuid) + '/'
    background_task.add_task(send_email, RecoveryPasswordEmailMessage(user, recovery_url))


@users_router.post('/password-recovery/{recovery_uuid}/', status_code=status.HTTP_204_NO_CONTENT)
async def recover_password(recovery_uuid: uuid_pkg.UUID, password: Annotated[str, Body(embed=True)]) -> None:
    """The view that processes setting the new password"""

    user_id = receive_password_recovery_data(recovery_uuid)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        user_updating_data = UserUpdate(password=password)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[{'loc': ['body', 'password'],
                                     'msg': 'invalid value',
                                     'type': 'value_error'}])

    delete_password_recovery_data(recovery_uuid)
    await update_models(User, user_updating_data, User.id == int(user_id))  # type: ignore
