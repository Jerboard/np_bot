from enum import Enum


class CB(str, Enum):
    CONFIRM_USER = 'confirm_user'
    USER_CONTINUE = 'user_continue'
    CHANGE_ROLE = 'change_role'
    USER_SELECT_ROLE = 'user_select_role'
    AGREE = 'agree'
    REGISTER_ADVERTISER_ENTITY = 'register_advertiser_entity'
    ADD_ADVERTISER = 'add_advertiser'
    ADD_ANOTHER_DISTRIBUTOR = 'add_another_distributor'
    CONTINUE = 'continue'
    CONTRACT_DIST_SELECT = 'contract_dist_select'
    CONTRACT_END = 'contract_end'
    CONTRACT_BACK = 'contract_back'
    CONTRACT_PAGE = 'contract_page'
    CONTRACT_NEXT_STEP_CHECK = 'add_contract_next_step_check'
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
    CREATIVE_TOKEN = 'creative_token'
    CREATIVE_ADD_LINK = 'creative_add_link'
    CREATIVE_SELECT_PLATFORM = 'creative_select_platform'
    CREATIVE_DONE = 'creative_done'
    RED_J_TYPE = 'red_j_type'
    NO = 'answer_no'
    PAY_YK_NEW = 'pay_yk_new'
    PAY_YK_FAST = 'pay_yk_fast'
    PAY_YK_CHECK = 'pay_yk_check'
    STATISTIC_SELECT_PAGE = 'statistic_select_page'
    STATISTIC_MONTHLY = 'statistic_monthly'
    ACTS_SELECT_PAGE = 'acts_select_page'
    ACT_NEXT_STEP_CHECK = 'act_next_step_check'
    ACT_SEND = 'act_send'
    SAVE_CARD_VIEW = 'save_card_view'
    SAVE_CARD_DEL = 'save_card_del'

    NO_ADVERTISER = 'no_advertiser'
    CLOSE = 'close'


