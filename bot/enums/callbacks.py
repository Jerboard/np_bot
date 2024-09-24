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
    PLATFORM_START = 'platform_start'
    PLATFORM_SELECT = 'platform_select'
    PLATFORM_CORRECT = 'platform_correct'
    PLATFORM_DIST = 'platform_dist'
    PLATFORM_FIN = 'platform_fin'
    NO_CHOOSE_PLATFORM = 'no_choose_platform'
    CAMPAIGN_ADD_ANOTHER_LINK = 'campaign_add_another_link'
    CAMPAIGN_ADD_CONFIRM = 'campaign_add_confirm'
    CREATIVE_SELECT_CAMPAIGN = 'creative_select_campaign'
    CREATIVE_ADD_CREATIVE = 'creative_add_creative'
    RED_J_TYPE = 'red_j_type'
    NO = 'answer_no'

    IP = 'ip'
    JURIDICAL = 'juridical'
    PHYSICAL = 'physical'
    ADVERTISER = 'advertiser'
    PUBLISHER = 'publisher'
    NO_ADVERTISER = 'no_advertiser'
    IP_ADVERTISER = 'ip_advertiser'
    UR_ADVERTISER = 'ur_advertiser'
    FIZ_ADVERTISER = 'fiz_advertiser'
    CLOSE = 'close'


