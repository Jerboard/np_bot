from enum import Enum


class UserState(str, Enum):
    USER_ADD_NAME = 'user_add_name'
    USER_ADD_INN = 'user_add_inn'
