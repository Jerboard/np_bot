import sqlite3
import os

from .base_db import begin_conn
from cachetools import cached, TTLCache


cache = TTLCache(maxsize=100, ttl=300)


# Функция для кэширования запросов к базе данных
@cached(cache)
def get_user(chat_id):
    return query_db('SELECT * FROM users WHERE chat_id = ?', (chat_id,), one=True)


# Функция для выполнения запросов к базе данных
def query_db(query, args=(), one=False) -> tuple:
    # меняем '?' на '%s'
    query = query.replace('?', '%s')
    with begin_conn() as conn:
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


# 'INSERT OR REPLACE INTO users (chat_id, agreed, role, fio, inn, title, juridical_type)
# VALUES (%s, %s, %s, %s, %s, %s, %s)',
# Функция для выполнения транзакций
def insert_user_data(chat_id, agreed, role, fio, inn, title, juridical_type):
    with begin_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO users (chat_id, agreed, role, fio, inn, title, juridical_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chat_id) 
                    DO UPDATE SET
                        agreed = EXCLUDED.agreed,
                        role = EXCLUDED.role,
                        fio = EXCLUDED.fio,
                        inn = EXCLUDED.inn,
                        title = EXCLUDED.title,
                        juridical_type = EXCLUDED.juridical_type
                ''',
                (chat_id, agreed, role, fio, inn, title, juridical_type))
            # cursor.execute(
            #     'INSERT OR REPLACE INTO users (chat_id, agreed, role, fio, inn, title, juridical_type) '
            #     'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            #     (chat_id, agreed, role, fio, inn, title, juridical_type))


# Вставляет контрагента
def insert_contractors_data(chat_id, contractor_id, role, juridical_type, ord_id):
    with begin_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO contractors (chat_id, contractor_id, role, juridical_type, ord_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (chat_id) 
                    DO UPDATE SET
                        contractor_id = EXCLUDED.contractor_id,
                        role = EXCLUDED.role,
                        juridical_type = EXCLUDED.juridical_type,
                        ord_id = EXCLUDED.ord_id
                ''',
                (chat_id, contractor_id, role, juridical_type, ord_id)
            )


# 'INSERT OR REPLACE INTO platforms (chat_id, platform_name, platform_url, average_views, ord_id) VALUES (?, ?, ?, ?, ?)'
# Вставляет платформу
def insert_platforms_data(chat_id, platform_name, platform_url, average_views, ord_id):
    with begin_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO platforms (chat_id, platform_name, platform_url, average_views, ord_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (chat_id) 
                    DO UPDATE SET
                        platform_name = EXCLUDED.platform_name,
                        platform_url = EXCLUDED.platform_url,
                        average_views = EXCLUDED.average_views,
                        ord_id = EXCLUDED.ord_id
                ''',
                (chat_id, platform_name, platform_url, average_views, ord_id)
            )


# 'INSERT OR REPLACE INTO selected_contractors (chat_id, contractor_id) VALUES (?, ?)'
# Вставляет контрагента
def insert_selected_contractors_data(chat_id, contractor_id):
    with begin_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO selected_contractors (chat_id, contractor_id)
                    VALUES (%s, %s)
                    ON CONFLICT (chat_id) 
                    DO UPDATE SET
                        contractor_id = EXCLUDED.contractor_id
                ''',
                (chat_id, contractor_id)
            )


# 'INSERT OR REPLACE INTO creative_links (chat_id, ord_id, creative_id, token) VALUES (?, ?, ?, ?)'
# Вставляет платформу
def insert_creative_links_data(chat_id, contract_external_id, creative_id, marker):
    with begin_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO creative_links (chat_id, ord_id, creative_id, token)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (chat_id) 
                    DO UPDATE SET
                        ord_id = EXCLUDED.ord_id,
                        creative_id = EXCLUDED.creative_id,
                        token = EXCLUDED.token
                ''',
                (chat_id, contract_external_id, creative_id, marker)
            )


#  'INSERT OR REPLACE INTO users (chat_id, juridical_type) VALUES (?, ?)', (chat_id, juridical_type)'
# Вставляет Тип пользователя
def insert_users_juridical_type_data(chat_id, juridical_type):
    with begin_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO users (chat_id, juridical_type)
                    VALUES (%s, %s)
                    ON CONFLICT (chat_id) 
                    DO UPDATE SET
                        juridical_type = EXCLUDED.juridical_type
                ''',
                (chat_id, juridical_type)
            )
