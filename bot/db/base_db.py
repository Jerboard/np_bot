import os
import psycopg2
from psycopg2 import connect
from psycopg2.extras import DictCursor
from psycopg2.extensions import connection


from config import connect_data


def begin_conn() -> connection:
    return connect(**connect_data)


# try:
#     with begin_conn() as conn:
#         cursor = conn.cursor(DictCursor)
#         # Выполнение запроса на выборку данных
#         cursor.execute("SELECT * FROM your_table;")
#         rows = cursor.fetchall()
#         for row in rows:
#             print(dict(row))  # Преобразование строки в словарь
#
#         # Пример выполнения операции вставки
#         insert_query = """
#         INSERT INTO your_table (column1, column2) VALUES (%s, %s)
#         """
#         cursor.execute(insert_query, ('value1', 'value2'))
#         conn.commit()  # Подтверждение транзакции
#
# except Exception as error:
#     print(f"Ошибка при выполнении запроса: {error}")