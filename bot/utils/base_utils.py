from datetime import datetime
from random import randint

import db
from config import Config
from enums import JStatus


# Функция для получения ord_id
def get_ord_id(user_id: int, delimiter: str = '.') -> str:
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


# переименовал inn в inn_check и coefficients в coefficients_check, чтоб не дублировалось название переменной
async def check_control_digit(inn_check, coefficients_check):
    n = sum([int(a) * b for a, b in zip(inn_check, coefficients_check)]) % 11
    return n if n < 10 else n % 10

if len(inn) == 10:
    coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
    return check_control_digit(inn[:-1], coefficients) == int(inn[-1])
elif len(inn) == 12:
    coefficients1 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    coefficients2 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    return (check_control_digit(inn[:-1], coefficients1) == int(inn[-1]) and
            check_control_digit(inn[:-2], coefficients2) == int(inn[-2]))

return False