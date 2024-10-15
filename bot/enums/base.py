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
    FIN = 'fin'


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


class MediaType(Enum):
    BANNER = "banner"  # баннер
    TEXT_BLOCK = "text_block"  # текстовый блок
    TEXT_GRAPHIC_BLOCK = "text_graphic_block"  # текстово-графический блок
    AUDIO = "audio"  # аудиозапись
    VIDEO = "video"  # видеоролик
    LIVE_AUDIO = "live_audio"  # аудиотрансляция в прямом эфире
    LIVE_VIDEO = "live_video"  # видеотрансляция в прямом эфире
    TEXT_VIDEO_BLOCK = "text_video_block"  # текстовый блок с видео
    TEXT_GRAPHIC_VIDEO_BLOCK = "text_graphic_video_block"  # текстово-графический блок с видео
    TEXT_AUDIO_BLOCK = "text_audio_block"  # текстовый блок с аудио
    TEXT_GRAPHIC_AUDIO_BLOCK = "text_graphic_audio_block"  # текстово-графический блок с аудио
    TEXT_AUDIO_VIDEO_BLOCK = "text_audio_video_block"  # текстовый блок с аудио и видео
    TEXT_GRAPHIC_AUDIO_VIDEO_BLOCK = "text_graphic_audio_video_block"  # текстово-графический блок с аудио и видео
