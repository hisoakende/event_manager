from src.config import REDIS_HOST

BROKER = 'redis'
BROKER_HOST = REDIS_HOST
BROKER_URL = f'{BROKER}://{BROKER_HOST}//'
