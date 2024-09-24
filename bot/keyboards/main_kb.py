from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

import db
from config import Config
from init import log_error
from enums import CB, Role, JStatus, Platform, Action


def get_agree_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Я согласен', callback_data=CB.AGREE.value)
    return kb.adjust(1).as_markup()


# стартовая клавиатура
def get_start_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Подтвердить', callback_data=CB.CONFIRM_USER.value)
    kb.button(text='Сменить роль', callback_data=CB.CHANGE_ROLE.value)
    kb.adjust(1).as_markup()
    return kb.adjust(1).as_markup()


# кб для  register
def get_register_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='ИП', callback_data=f'{CB.RED_J_TYPE.value}:{JStatus.IP.value}')
    kb.button(text='Юр. лицо', callback_data=f'{CB.RED_J_TYPE.value}:{JStatus.JURIDICAL.value}')
    kb.button(text='Физическое лицо', callback_data=f'{CB.RED_J_TYPE.value}:{JStatus.PHYSICAL.value}')
    return kb.adjust(2).as_markup()


# кб для  inn_collector
def get_select_role_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Рекламодатель', callback_data=f'{CB.USER_SELECT_ROLE.value}:{Role.ADVERTISER.value}')
    kb.button(text='Рекламораспространитель', callback_data=f'{CB.USER_SELECT_ROLE.value}:{Role.PUBLISHER.value}')
    return kb.adjust(1).as_markup()


# кб для  preloader_advertiser_entity
def get_preloader_advertiser_entity_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Да', callback_data=CB.REGISTER_ADVERTISER_ENTITY.value)
    kb.button(text='Нет', callback_data=CB.NO_ADVERTISER.value)
    return kb.adjust(2).as_markup()


# кб для  register_advertiser_entity
def get_register_advertiser_entity_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='ИП', callback_data=f'{CB.ADD_ADVERTISER.value}:{JStatus.IP.value}')
    kb.button(text='Юр. лицо', callback_data=f'{CB.ADD_ADVERTISER.value}:{JStatus.JURIDICAL.value}')
    kb.button(text='Физическое лицо', callback_data=f'{CB.ADD_ADVERTISER.value}:{JStatus.PHYSICAL.value}')
    return kb.adjust(2).as_markup()


# кб для preloader_choose_platform
def get_preloader_choose_platform_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Да', callback_data=CB.PLATFORM_START.value)
    kb.button(text='Нет', callback_data=CB.NO_CHOOSE_PLATFORM.value)
    return kb.adjust(2).as_markup()


# кб для choose_platform
def get_choose_platform_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='ВКонтакте', callback_data=f'{CB.PLATFORM_SELECT.value}:{Platform.VK.value}')
    kb.button(text='Instagram', callback_data=f'{CB.PLATFORM_SELECT.value}:{Platform.INSTAGRAM.value}')
    kb.button(text='YouTube', callback_data=f'{CB.PLATFORM_SELECT.value}:{Platform.YOUTUBE.value}')
    kb.button(text='Telegram-канал', callback_data=f'{CB.PLATFORM_SELECT.value}:{Platform.TG_CHANNEL.value}')
    kb.button(text='Личный Telegram', callback_data=f'{CB.PLATFORM_SELECT.value}:{Platform.TG_PERSONAL.value}')
    kb.button(text='Другое', callback_data=f'{CB.PLATFORM_SELECT.value}:{Platform.OTHER.value}')
    return kb.adjust(2).as_markup()


# кб для platform_url_collector
def get_platform_url_collector_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Да, верно', callback_data=f'{CB.PLATFORM_CORRECT.value}:{Action.YES.value}')
    kb.button(text='Исправить', callback_data=f'{CB.PLATFORM_CORRECT.value}:{Action.NO.value}')
    # kb.button(text='Удалить', callback_data=f'{CB.PLATFORM_CORRECT.value}:0')
    kb.button(text='Удалить', callback_data=f'{CB.CLOSE.value}')
    return kb.adjust(3).as_markup()


# кб для process_average_views
def get_process_average_views_kb(contractors: tuple[db.DistributorRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for contractor in contractors:
        kb.button(text=contractor.name, callback_data=f"{CB.PLATFORM_DIST.value}:{contractor.ord_id}")
    kb.button(text="❌ Отмена", callback_data=CB.CLOSE.value)
    return kb.adjust(1).as_markup()


# кб для finalize_platform_data
def get_finalize_platform_data_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Добавить еще площадку', callback_data=f'{CB.PLATFORM_FIN.value}:{Action.ADD.value}')
    kb.button(text='Продолжить', callback_data=f'{CB.PLATFORM_FIN.value}:{Action.CONT.value}')
    return kb.adjust(2).as_markup()


# кб для confirm_ad_campaign
def get_confirm_ad_campaign_kb(campaign_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да, верно", callback_data=f"confirm_ad_campaign:1"),
    kb.button(text="Изменить", callback_data=f"change_ad_campaign:0"),
    kb.button(text="Удалить", callback_data=f"{CB.CLOSE.value}")
    return kb.adjust(3).as_markup()
    

# кб для ask_for_additional_link
def get_ask_for_additional_link_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data=f"{CB.CAMPAIGN_ADD_ANOTHER_LINK.value}:1"),
    kb.button(text="Нет", callback_data=f"{CB.CAMPAIGN_ADD_ANOTHER_LINK.value}:0"),
    return kb.adjust(2).as_markup()
    

# кб для add_creative
def get_add_creative_kb(campaigns: tuple[db.CampaignRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for campaign in campaigns:
        # Создаем кнопку с текстом из названия бренда и описания услуги
        kb.button(
            text=f"{campaign.brand} - {campaign.service}",
            callback_data=f"{CB.CREATIVE_SELECT_CAMPAIGN.value}_{campaign.id}")
    return kb.adjust(1).as_markup()


# кб для handle_creative_upload
def get_handle_creative_upload_kb(campaign_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить файл или текст", callback_data=f"{CB.CREATIVE_ADD_CREATIVE.value}:1")
    # kb.button(text="Продолжить", callback_data=f"{CB.CREATIVE_ADD_CREATIVE.value}:1")
    # kb.button(text="Добавить файл или текст", callback_data=f"add_more_{campaign_id}")
    kb.button(text="Продолжить", callback_data=f"pay_yk:{campaign_id}")
    return kb.adjust(1).as_markup()


# кб для handle_creative_link
def get_handle_creative_link_kb(ord_id) -> InlineKeyboardMarkup:
    # Предложение добавить еще одну ссылку или закончить
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить ссылку на другую площадку", callback_data=f"add_link_{ord_id}")
    kb.button(text="Готово", callback_data=f"link_done_{ord_id}")
    return kb.adjust(1).as_markup()


# кб для generate_link
def generate_link_markup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить ссылку на другую площадку", callback_data="add_link")
    kb.button(text="Готово", callback_data="link_done")
    return kb.adjust(1).as_markup()


# кб со ссылкой на оплату в юкассе
# def get_yk_pay_kb(pay_id: str, campaign_id: str, save_cards: tuple) -> InlineKeyboardMarkup:
def get_yk_pay_kb(pay_id: str, save_cards: tuple) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Оплатить 400 р.", url=Config.pay_link.format(payment_id=pay_id))
    for card in save_cards:
        kb.button(text=f"Оплатить {card}", callback_data=f"in_dev")

    # markup.add(kb.button(text="Продолжить", callback_data=f"continue_creative_:{pay_id}:{campaign_id}"))
    kb.button(text="Продолжить", callback_data=f"continue_creative_:{pay_id}")
    return kb.adjust(1).as_markup()


def get_nds_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data=f"{CB.CONTRACT_VAT.value}:4")
    kb.button(text="Нет", callback_data=f"{CB.CONTRACT_VAT.value}:1")
    return kb.adjust(2).as_markup()


# запрашивает есть ли часть договора
def get_check_next_step_contract_kb(step: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data=f'add_contract_next_step_check:{step}:1'),
    kb.button(text="Нет", callback_data=f'add_contract_next_step_check:{step}:0')
    return kb.adjust(1).as_markup()


# после добавления контрагента
def get_add_distributor_finish_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Добавить еще контрагента', callback_data=CB.ADD_ANOTHER_DISTRIBUTOR.value)
    kb.button(text='Продолжить', callback_data=CB.CONTINUE.value)
    return kb.adjust(2).as_markup()


# выбор контрагента
def get_select_distributor_kb(contractors: tuple[db.DistributorRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for contractor in contractors:
        kb.button(text=contractor.name, callback_data=f"{CB.CONTRACT_DIST_SELECT.value}:{contractor.id}")

    kb.button(text="❌ Отмена", callback_data=CB.CLOSE.value)
    return kb.adjust(1).as_markup()


# запрашивает есть ли часть договора
def get_close_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data=CB.CLOSE.value)
    return kb.adjust(1).as_markup()
