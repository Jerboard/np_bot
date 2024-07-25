import sqlite3
import os

from .base_db import conn
from cachetools import cached, TTLCache


cache = TTLCache(maxsize=100, ttl=300)


# Функция для кэширования запросов к базе данных
@cached(cache)
def get_user(chat_id):
    return query_db('SELECT * FROM users WHERE chat_id = ?', (chat_id,), one=True)


# Функция для выполнения запросов к базе данных
def query_db(query, args=(), one=False) -> tuple:
    with sqlite3.connect('bot_database2.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        r = cursor.fetchall()
        cursor.close()
        return (r[0] if r else None) if one else r


# Функция для создания директории, если она не существует
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


# Функция для выполнения пакетных вставок данных
def batch_insert_users(users):
    with conn:
        cursor = conn.cursor()
        cursor.executemany(
            'INSERT OR REPLACE INTO users (chat_id, agreed, role, fio, inn, title, juridical_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
            users)


# Функция для выполнения транзакций
def insert_user_data(chat_id, agreed, role, fio, inn, title, juridical_type):
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO users (chat_id, agreed, role, fio, inn, title, juridical_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (chat_id, agreed, role, fio, inn, title, juridical_type))

