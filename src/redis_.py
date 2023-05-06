import redis

from src import config

redis_engine = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
