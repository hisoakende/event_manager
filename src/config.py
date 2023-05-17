import os

DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = 5432
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_URL = f'postgresql+asyncpg://{DATABASE_USER}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
DATABASE_CURSOR_SIZE = 10000

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = 6379
USERS_BLACKLIST_NAME = 'users_black_list'

EMAIL_PASSWORD = 'aoubnsgsddrgsnnt'
EMAIL_LOCAL_ADDRESS = 'event.manager.notifications@gmail.com'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587

TIMEZONE = 'Europe/Moscow'
