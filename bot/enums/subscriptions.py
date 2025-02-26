from enum import Enum


class Subscription(str, Enum):
    TESTER = 'Пробный'
    BASED = 'Базовый'
    PRO = 'Премиум'
