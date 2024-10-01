from aiogram.types import Message
from aiogram.enums.content_type import ContentType
from datetime import datetime
from random import randint

import typing as t
import os

import db
from init import bot, log_error
from config import Config
from .ord_api import register_media_file, send_mediation_to_ord
from .media_utils import compress_video
from enums import JStatus, Delimiter


# выводит данные словаря
def print_dict(data: dict, title: str = None) -> None:
    print('>>>')
    if title:
        print(title)

    for k, v in data.items():
        print(f'{k}: {v}')


# Функция для получения ord_id
def get_ord_id(user_id: int, delimiter: str = Delimiter.BASE.value) -> str:
    return f"{user_id}{delimiter}{randint(100000000, 9999999999)}"


def convert_date(date_str: str) -> str:
    # Определяем два возможных формата
    formats = [Config.date_form, Config.ord_date_form]

    for date_format in formats:
        try:
            # Пробуем распарсить строку как дату
            date_obj = datetime.strptime(date_str, date_format)

            # Если формат "%Y.%m.%d", просто возвращаем строку
            if date_format == Config.ord_date_form:
                return date_str

            # Если формат "%d.%m.%Y", конвертируем в "%Y.%m.%d"
            return date_obj.strftime(Config.ord_date_form)

        except ValueError:
            # Если ошибка - продолжаем проверку с другим форматом
            continue

    # Если строка не является датой в нужных форматах, возвращаем пустую строку
    return ""


def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, Config.date_form)
        return True
    except ValueError:
        return False


def is_float(text: str) -> bool:
    try:
        float(text)
        return True
    except Exception as ex:
        return False


# Валидатор ИНН
def validate_inn(inn: str, j_type: str):
    # Проверяем длину ИНН (он должен быть 10 или 12 символов)
    if len(inn) not in (10, 12):
        return False

    # Функция для вычисления контрольной цифры
    def calculate_checksum(inn_digits, coefficients):
        return sum(int(digit) * coef for digit, coef in zip(inn_digits, coefficients)) % 11 % 10

    # Если ИНН 10-значный
    if len(inn) == 10:
        if j_type != JStatus.JURIDICAL:
            return False

        coefficients_10 = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum_10 = calculate_checksum(inn[:9], coefficients_10)
        return checksum_10 == int(inn[9])

    # Если ИНН 12-значный
    elif len(inn) == 12:
        coefficients_11_1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        coefficients_11_2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]

        checksum_11_1 = calculate_checksum(inn[:10], coefficients_11_1)
        checksum_11_2 = calculate_checksum(inn[:11], coefficients_11_2)

        return checksum_11_1 == int(inn[10]) and checksum_11_2 == int(inn[11])


#  возвращает id файла
def get_file_id(msg: Message) -> t.Union[str, None]:
    if msg.content_type == ContentType.PHOTO:
        file_id = msg.photo[-1].file_id

    elif msg.content_type == ContentType.VIDEO:
        file_id = msg.video.file_id

    elif msg.content_type == ContentType.AUDIO:
        file_id = msg.audio.file_id

    elif msg.content_type == ContentType.DOCUMENT:
        file_id = msg.document.file_id

    else:
        file_id = None
    return file_id


# тут медиа регистрируются в ОРД
async def save_media_ord(creatives: list[dict], creative_ord_id: str, user_id: int, descriptions: str) -> list[str]:
    media_ord_ids = []
    for creative in creatives:
        # {'content_type': msg.content_type, 'file_id': ut.get_file_id(msg), 'text': msg.text}

        file_id = creative.get('file_id')
        if file_id:
            media_ord_id = get_ord_id(user_id, delimiter=Delimiter.M.value)

            # скачиваем файл
            file_info = await bot.get_file(file_id)
            tg_file = await bot.download_file(file_info.file_path)

            if creative['content_type'] == ContentType.VIDEO:
                file_path = os.path.join(Config.storage_path, creative['video_name'])
            else:
                file_path = os.path.join(Config.storage_path, f'{file_info.file_unique_id}')

            with open(file_path, 'wb') as new_file:
                new_file.write(tg_file.read())

            # тут нужно видео сжимать

            status_code = await register_media_file(file_path=str(file_path), ord_id=media_ord_id, description=descriptions)
            if status_code <= 201:
                media_ord_ids.append(media_ord_id)

            await db.add_media(
                user_id=user_id,
                creative_ord_id=creative_ord_id,
                content_type=creative['content_type'],
                file_id=file_id,
                ord_id=media_ord_id
            )

            # Удаление файла после обработки
            # if os.path.exists(file_path):
            #     os.remove(file_path)
    #
    return media_ord_ids
