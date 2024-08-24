from enum import Enum


class UserState(str, Enum):
    USER_ADD_NAME = 'user_add_name'
    USER_ADD_INN = 'user_add_inn'
    ADD_ADVERTISER_NAME = 'add_advertiser_name'
    ADD_ADVERTISER_INN = 'add_advertiser_inn'
    ADD_CONTRACT = 'add_contract'
    ADD_PLATFORM_NAME = 'add_platform_name'
    ADD_PLATFORM_VIEW = 'add_platform_view'

    ADD_CONTRACT_START_DATE = 'add_contract_start_date'
    ADD_CONTRACT_END_DATE = 'add_contract_end_date'
    ADD_CONTRACT_SERIAL = 'add_contract_serial'
    ADD_CONTRACT_AMOUNT = 'add_contract_amount'
