import json

from init import redis_db
from config import TTL_REDIS


# сохраняем данные
async def save_user_data(chat_id: int, data: dict) -> None:
    key = f"{chat_id}"
    redis_db.setex(key, TTL_REDIS, json.dumps(data))


# возвращаем данные
async def get_user_data(chat_id) -> dict:
    key = f"{chat_id}"
    data = redis_db.get(key)
    return json.loads(data) if data else {}


# добавляет данные
async def update_user_data(chat_id: int, key: str, value: str) -> None:
    data = get_user_data(chat_id)
    data[key] = value
    save_user_data(chat_id, data)
