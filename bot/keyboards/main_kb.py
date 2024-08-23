from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from config import Config
from init import log_error
from enums import CB, Role


def get_agree_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Я согласен', callback_data=CB.AGREE.value)
    return kb.adjust(1).as_markup()


# стартовая клавиатура
def get_start_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Подтвердить', callback_data='confirm_user')
    kb.button(text='Сменить роль', callback_data='change_role')
    kb.adjust(1).as_markup()
    return kb.adjust(1).as_markup()


# кб для  get_process_role_change_kb
def get_process_role_change_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Рекламодатель', callback_data='advertiser')
    kb.button(text='Рекламораспространитель', callback_data='publisher')
    return kb.adjust(1).as_markup()


# кб для  register
def get_register_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='ИП', callback_data='ip')
    kb.button(text='Юр. лицо', callback_data='juridical')
    kb.button(text='Физическое лицо', callback_data='physical')
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
    kb.button(text='Да', callback_data='register_advertiser_entity')
    kb.button(text='Нет', callback_data='no_advertiser')
    return kb.adjust(1).as_markup()


# кб для  register_advertiser_entity
def get_register_advertiser_entity_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='ИП', callback_data='ip_advertiser')
    kb.button(text='Юр. лицо', callback_data='ur_advertiser')
    kb.button(text='Физическое лицо', callback_data='fiz_advertiser')
    return kb.adjust(2).as_markup()


# кб для preloader_choose_platform
def get_preloader_choose_platform_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Да', callback_data='choose_platform')
    kb.button(text='Нет', callback_data='no_choose_platform')
    return kb.adjust(2).as_markup()


# кб для choose_platform
def get_choose_platform_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='ВКонтакте', callback_data='vk')
    kb.button(text='Instagram', callback_data='instagram')
    kb.button(text='YouTube', callback_data='youtube')
    kb.button(text='Telegram-канал', callback_data='telegram_channel')
    kb.button(text='Личный Telegram', callback_data='personal_telegram')
    # kb.button(text='Другое', callback_data='other')
    kb.button(text='Другое', callback_data='in_dev')
    return kb.adjust(2).as_markup()


# кб для platform_url_collector
def get_platform_url_collector_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Да, верно', callback_data='correct_platform')
    kb.button(text='Исправить', callback_data='change_platform')
    kb.button(text='Удалить', callback_data='delete_platform')
    return kb.adjust(3).as_markup()


# кб для process_average_views
def get_process_average_views_kb(contractors: tuple[tuple]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for contractor in contractors:
        contractor_name = contractor[2] if contractor[2] else contractor[1]
        kb.button(text=contractor_name, callback_data=f"contractor1_{contractor[0]}")

    return kb.adjust(1).as_markup()


# кб для finalize_platform_data
def get_finalize_platform_data_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Добавить еще площадку', callback_data='add_another_platform')
    kb.button(text='Продолжить', callback_data='continue_to_entity')
    return kb.adjust(2).as_markup()


# кб для confirm_ad_campaign
def get_confirm_ad_campaign_kb(campaign_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да, верно", callback_data=f"confirm_ad_campaign:{campaign_id}"),
    kb.button(text="Изменить", callback_data=f"change_ad_campaign:{campaign_id}"),
    kb.button(text="Удалить", callback_data=f"delete_ad_campaign:{campaign_id}")
    return kb.adjust(3).as_markup()
    

# кб для ask_for_additional_link
def get_ask_for_additional_link_kb(campaign_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да, верно", callback_data=f"confirm_ad_campaign:{campaign_id}"),
    kb.button(text="Изменить", callback_data=f"change_ad_campaign:{campaign_id}"),
    kb.button(text="Удалить", callback_data=f"delete_ad_campaign:{campaign_id}")
    return kb.adjust(3).as_markup()
    

# кб для add_creative
def get_add_creative_kb(campaigns) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for idx, campaign in enumerate(campaigns):
        # Создаем кнопку с текстом из названия бренда и описания услуги
        kb.button(text=f"{campaign[1]} - {campaign[2]}", callback_data=f"choose_campaign_{campaign[0]}")
    return kb.adjust(1).as_markup()


# кб для handle_creative_upload
def get_handle_creative_upload_kb(campaign_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить файл или текст", callback_data=f"add_more_{campaign_id}")
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
def get_yk_pay_kb(pay_id: str,save_cards: tuple) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Оплатить 400 р.", url=Config.pay_link.format(payment_id=pay_id))
    for card in save_cards:
        kb.button(text=f"Оплатить {card[0]}", callback_data=f"in_dev")

    # markup.add(kb.button(text="Продолжить", callback_data=f"continue_creative_:{pay_id}:{campaign_id}"))
    kb.button(text="Продолжить", callback_data=f"continue_creative_:{pay_id}")
    return kb.adjust(1).as_markup()


def get_nds_kb(contractor_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data=f"vat_yes_{contractor_id}")
    kb.button(text="Нет", callback_data=f"vat_no_{contractor_id}")
    return kb.adjust(2).as_markup()


# запрашивает есть ли часть договора
def get_check_next_step_contract_kb(step: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data=f'add_contract_next_step_check:{step}:1'),
    kb.button(text="Нет", callback_data=f'add_contract_next_step_check:{step}:0')
    return kb.adjust(1).as_markup()
