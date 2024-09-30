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


# кнопка пропустить при добавлении данных
def get_continue_btn_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Пропустить', callback_data=f'{CB.USER_CONTINUE.value}')
    return kb.adjust(1).as_markup()


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
def get_confirm_ad_campaign_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, верно", callback_data=f"{CB.CAMPAIGN_ADD_CONFIRM.value}:{Action.ADD.value}"),
    kb.button(text="🖍 Изменить", callback_data=f"{CB.CAMPAIGN_ADD_CONFIRM.value}:{Action.NO.value}"),
    kb.button(text="❌ Удалить", callback_data=f"{CB.CAMPAIGN_ADD_CONFIRM.value}:0"),
    # kb.button(text="❌ Удалить", callback_data=f"{CB.CLOSE.value}")
    return kb.adjust(3).as_markup()


# Подтвердить замену промо
def get_select_page_kb(end_page: bool, select_id: int, page: int, cb: str = CB.CONTRACT_PAGE.value) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    btn_count = 0
    if page > 0:
        btn_count += 1
        kb.button(text=f'⬅️ Пред стр.', callback_data=f'{cb}:{page - 1}:{Action.CONT.value}')
    if not end_page:
        btn_count += 1
        kb.button(text=f'След стр. ➡️ ', callback_data=f'{cb}:{page + 1}:{Action.CONT.value}')

    kb.button(text=f'✔️ Выбрать', callback_data=f'{cb}:{select_id}:{Action.YES.value}')
    kb.adjust(2, 1) if btn_count == 2 else kb.adjust(1)
    return kb.as_markup()


# кнопка пропустить добавление ссылки
def get_continue_add_link_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Пропустить", callback_data=f"{CB.CAMPAIGN_ADD_ANOTHER_LINK.value}:0")
    return kb.adjust(1).as_markup()


# кб для ask_for_additional_link
def get_ask_for_additional_link_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data=f"{CB.CAMPAIGN_ADD_ANOTHER_LINK.value}:1")
    kb.button(text="Нет", callback_data=f"{CB.CAMPAIGN_ADD_ANOTHER_LINK.value}:0")
    return kb.adjust(2).as_markup()


# кб переход к выбору рекламной компании
def get_select_campaigns_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Перейти к выбору рекламной компании",
        callback_data=f"{CB.CREATIVE_SELECT_CAMPAIGN.value}:0:{ Action.CONT.value}"
    )
    return kb.adjust(1).as_markup()


# кб для add_creative
# def get_add_creative_kb(campaigns: tuple[db.CampaignRow]) -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     for campaign in campaigns:
#         # Создаем кнопку с текстом из названия бренда и описания услуги
#         kb.button(
#             text=f"{campaign.brand} - {campaign.service}",
#             callback_data=f"{CB.CREATIVE_SELECT_CAMPAIGN.value}:{campaign.id}")
#     return kb.adjust(1).as_markup()


# кб для generate_link
def get_end_creative_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить ссылку на другую площадку", callback_data=CB.CREATIVE_ADD_LINK.value)
    kb.button(text="Готово", callback_data=CB.CREATIVE_DONE.value)
    return kb.adjust(1).as_markup()


# выбор карты
def get_select_card_kb(save_cards: tuple[db.SaveCardRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Оплатить новой картой", callback_data=f"{CB.PAY_YK_NEW.value}:{1}")
    for card in save_cards:
        kb.button(text=f"Оплатить {card.card_info}", callback_data=f"{CB.PAY_YK_FAST.value}:{card.id}")

    # markup.add(kb.button(text="Продолжить", callback_data=f"continue_creative_:{pay_id}:{campaign_id}"))
    return kb.adjust(1).as_markup()


# кб со ссылкой на оплату в юкассе
# def get_yk_pay_kb(pay_id: str, campaign_id: str, save_cards: tuple) -> InlineKeyboardMarkup:
def get_yk_pay_kb(pay_id: str, save_card: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    checkbox = '✔️ ' if save_card else ''
    edit_save_card = 0 if save_card else 1
    kb.button(text=f"{checkbox} Сохранить карту", callback_data=f"{CB.PAY_YK_NEW.value}:{int(not save_card)}")
    kb.button(text=f"Оплатить 400 р.", url=Config.pay_link.format(payment_id=pay_id))
    kb.button(text="Продолжить", callback_data=f"{CB.PAY_YK_CHECK.value}:{pay_id}")
    return kb.adjust(1).as_markup()


def get_contract_end_kb(dist_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, верно", callback_data=f"{CB.CONTRACT_END.value}")
    kb.button(text="🖍 Изменить", callback_data=f"{CB.CONTRACT_DIST_SELECT.value}:{dist_id}")
    kb.button(text="❌ Удалить", callback_data=f"{CB.CONTRACT_BACK.value}")
    return kb.adjust(3).as_markup()


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
