import re

from pydantic import validator, EmailStr
from sqlmodel import SQLModel, Field

from src.users.utils import get_random_string, hash_password
from src.utils import ChangesAreNotEmptyMixin


class UserBase(SQLModel):
    """The model that represents basic user structure fields"""

    first_name: str
    last_name: str
    patronymic: str


class UserBaseWithPassword(UserBase):
    """The model that represents basic user structure fields and the password field"""

    password: str


class UserBaseWithEmail(UserBase):
    """The model that represents basic user structure fields and the email field"""

    email: EmailStr = Field(unique=True)


class UserValidator(SQLModel):

    @validator('first_name', 'last_name', 'patronymic', check_fields=False)
    def validate_full_name(cls, value: str) -> str:
        if re.fullmatch(r'[а-яА-ЯёЁ]{1,35}', value) is None:
            raise ValueError('invalid value')

        return value.lower().capitalize()

    @validator('password', check_fields=False)
    def validate_password(cls, value: str) -> str:
        if re.fullmatch(r'(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{6,}', value) is None:
            raise ValueError('invalid value')

        salt = get_random_string()
        hashed_password = hash_password(value, salt)
        return f'{salt}${hashed_password}'


class User(UserBaseWithEmail, UserBaseWithPassword, table=True):
    """The model that represents an ordinary citizen or a government worker in the database"""

    id: int | None = Field(default=None, primary_key=True)
    is_government_worker: bool = False
    email: EmailStr = Field(unique=True)


class UserCreate(UserBaseWithEmail, UserBaseWithPassword, UserValidator):
    """
    The model that represents the fields needed to create the user and processes its

    The 'government_key' field needed to create a government worker
    """

    government_key: str | None = None


class UserRead(UserBaseWithEmail):
    """The model that represents the fields which will be returned by API"""

    is_government_worker: bool


class UserUpdate(UserBaseWithPassword, UserValidator, ChangesAreNotEmptyMixin):
    """The model that represents the fields needed to change the user"""

    __annotations__ = {k: v | None for k, v in
                       (UserBase.__annotations__ | UserBaseWithPassword.__annotations__).items()}
