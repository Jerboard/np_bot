from enum import Enum


class CB(str, Enum):
    CONFIRM_USER = 'confirm_user'
    CHANGE_ROLE = 'change_role'
    USER_SELECT_ROLE = 'user_select_role'
    AGREE = 'agree'
    REGISTER_ADVERTISER_ENTITY = 'register_advertiser_entity'
    ADD_ADVERTISER = 'add_advertiser'
    ADD_ANOTHER_DISTRIBUTOR = 'add_another_distributor'
    CONTINUE = 'continue'
    CONTRACT_DIST_SELECT = 'contract_dist_select'
    CONTRACT_VAT = 'contract_vat'

    IP = 'ip'
    JURIDICAL = 'juridical'
    PHYSICAL = 'physical'
    ADVERTISER = 'advertiser'
    PUBLISHER = 'publisher'
    NO_ADVERTISER = 'no_advertiser'
    IP_ADVERTISER = 'ip_advertiser'
    UR_ADVERTISER = 'ur_advertiser'
    FIZ_ADVERTISER = 'fiz_advertiser'
    CHOOSE_PLATFORM = 'choose_platform'
    NO_CHOOSE_PLATFORM = 'no_choose_platform'
    CLOSE = 'close'
