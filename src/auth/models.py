import re
from typing import Optional

from pydantic import validator
from sqlmodel import SQLModel, Field

from src.auth.utils import get_random_string, hash_password


class UserBase(SQLModel):
    """The model that represents basic user structure fields"""

    first_name: str
    last_name: str
    patronymic: str
    email: str = Field(unique=True)


class User(UserBase, table=True):
    """The model that represents an ordinary citizen or a government worker in the database"""

    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    is_government_worker: bool = False


class UserRead(UserBase):
    """That model that represents the fields which will be returned by API"""

    id: int
    is_government_worker: bool


class UserCreate(UserBase):
    """
    The model that represents the fields needed to create the user from a post request and processes its

    The 'government_key' field needed to create a government worker
    """

    password: str
    government_key: str | None = None

    @validator('first_name', 'last_name', 'patronymic')
    def validate_full_name(cls, value: str) -> str:
        if re.fullmatch(r'[а-яА-ЯёЁ]{1,35}', value) is None:
            raise ValueError('incorrect value')
        return value.lower().capitalize()

    @validator('email')
    def validate_email(cls, value: str) -> str:
        if re.fullmatch(r'[_A-Za-z0-9-\+]+(\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+'
                        r'(\.[A-Za-z0-9]+)*(\.[A-Za-z]{2,})', value) is None:
            raise ValueError('incorrect value')
        return value

    @validator('password')
    def validate_password(cls, value: str) -> str:
        if re.fullmatch(r'(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{6,}', value) is None:
            raise ValueError('incorrect value')

        salt = get_random_string()
        hashed_password = hash_password(value, salt)
        return f'{salt}${hashed_password}'
