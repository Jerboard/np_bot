from enum import Enum


class Step(str, Enum):
    START_DATE = 'start_date'
    END_DATE = 'end_date'
    NUM = 'num'
    SUM = 'sum'
    INN = 'inn'
    PHONE = 'phone'
    EMAIL = 'email'
    NAME = 'name'
    FIO = 'fio'


class Role(str, Enum):
    ADVERTISER = 'advertiser'
    PUBLISHER = 'publisher'
    # ORS = 'ors'
    # MEDIATION = 'mediation'


class Status(str, Enum):
    NEW = 'new'
    ACTIVE = 'active'
    UNACTIVE = 'unactive'


class JStatus(str, Enum):
    IP = 'ip'
    JURIDICAL = 'juridical'
    PHYSICAL = 'physical'


class Action(str, Enum):
    ADD = 'add'
    DEL = 'del'
    EDIT = 'edit'
    YES = 'yes'
    NO = 'no'
    CONT = 'continue'


class Command(str, Enum):
    START = 'start'
    COUNTERAGENT = 'counteragent'
    PLATFORM = 'platform'
    CONTRACT = 'contract'
    CAMPAIGN = 'campaign'
    TOKEN = 'token'
    STATS = 'stats'
    ACTS = 'acts'
    HELP = 'help'


class Platform(str, Enum):
    VK = 'vk'
    INSTAGRAM = 'instagram'
    YOUTUBE = 'youtube'
    TG_CHANNEL = 'telegram_channel'
    TG_PERSONAL = 'personal_telegram'
    OTHER = 'other'


platform_dict = {
    Platform.VK.value: 'ВКонтакте',
    Platform.INSTAGRAM.value: 'Instagram',
    Platform.YOUTUBE.value: 'YouTube',
    Platform.TG_CHANNEL.value: 'Telegram-канал',
    Platform.TG_PERSONAL.value: 'Личный Telegram',
    Platform.OTHER.value: 'Другое',
}


class Delimiter(str, Enum):
    BASE = '.'
    U = '-u-'
    P = '-p-'
    C = '-c-'
    M = '-m-'
    CR = '-cr-'
