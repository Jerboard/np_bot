from enum import Enum


class AddContractStep(str, Enum):
    START_DATE = 'start_date'
    END_DATE = 'end_date'
    NUM = 'num'
    SUM = 'sum'


class Role(str, Enum):
    ADVERTISER = 'advertiser'
    PUBLISHER = 'publisher'
    ORS = 'ors'


class JStatus(str, Enum):
    IP = 'ip'
    JURIDICAL = 'juridical'
    PHYSICAL = 'physical'


class Command(str, Enum):
    START = 'start'
    PRELOADER_ADVERTISER_ENTITY = 'preloader_advertiser_entity'
    PRELOADER_CHOOSE_PLATFORM = 'preloader_choose_platform'
    START_CONTRACT = 'start_contract'
    START_CAMPAIGN = 'start_campaign'
    ADD_CREATIVE = 'add_creative'
    START_STATISTICS = 'start_statistics'
