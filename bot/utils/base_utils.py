from aiogram.types import Message
from aiogram.enums.content_type import ContentType
from datetime import datetime
from random import randint

import typing as t
import os

import db
from init import bot, log_error
from config import Config
from enums import JStatus, Delimiter


# Функция для получения ord_id
def get_ord_id(user_id: int, delimiter: str = Delimiter.BASE.value) -> str:
    return f"{user_id}{delimiter}{randint(100000000, 9999999999)}"


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
def is_valid_inn(inn: str, juridical_type: str) -> bool:
    if Config.debug:
        return True

    if not inn.isdigit():
        return False

    if juridical_type == JStatus.JURIDICAL:
        if len(inn) != 10:
            return False

    else:
        if len(inn) != 12:
            return False
        

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


async def save_media(file_id: str, user_id: int) -> str:
    file_info = await bot.get_file(file_id)
    log_error(f'{file_info.file_path}')
    photo_file = await bot.download_file(file_info.file_path)

    path = os.path.join(Config.storage_path, str(user_id), file_info.file_unique_id)
    with open(path, 'wb') as new_file:
        new_file.write(photo_file.read())

    return path


# переименовал inn в inn_check и coefficients в coefficients_check, чтоб не дублировалось название переменной
# async def check_control_digit(inn_check, coefficients_check):
#     n = sum([int(a) * b for a, b in zip(inn_check, coefficients_check)]) % 11
#     return n if n < 10 else n % 10
#
# if len(inn) == 10:
#     coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
#     return check_control_digit(inn[:-1], coefficients) == int(inn[-1])
# elif len(inn) == 12:
#     coefficients1 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
#     coefficients2 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
#     return (check_control_digit(inn[:-1], coefficients1) == int(inn[-1]) and
#             check_control_digit(inn[:-2], coefficients2) == int(inn[-2]))
#
# return False