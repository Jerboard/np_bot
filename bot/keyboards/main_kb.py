from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

import db
from config import Config
from enums.subscriptions import Subscription
from init import log_error
from enums import CB, Role, JStatus, Platform, Action


# написать в поддержку
def get_help_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Написать в поддержку', url='https://t.me/Andrey_Tatarnik')
    return kb.adjust(1).as_markup()


def get_agree_button() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Я согласен', callback_data=CB.AGREE.value)
    return kb.adjust(1).as_markup()


# стартовая клавиатура
def get_start_kb(with_card: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Подтвердить', callback_data=CB.CONFIRM_USER.value)
    kb.button(text='Сменить роль', callback_data=CB.CHANGE_ROLE.value)
    if with_card:
        kb.button(text='💳 Сохранённые карты', callback_data=CB.SAVE_CARD_VIEW.value)
    kb.adjust(1).as_markup()
    return kb.adjust(1).as_markup()


# стартовая клавиатура
def get_view_card_kb(cards: list[db.SaveCardRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for card in cards:
        kb.button(text=f'🗑 {card.card_info}', callback_data=f'{CB.SAVE_CARD_DEL.value}:{card.id}')

    kb.button(text=f'🔙 Назад', callback_data=f'{CB.SAVE_CARD_DEL.value}:{Action.BACK.value}')
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
def get_process_average_views_kb(contractors: list[db.DistributorRow]) -> InlineKeyboardMarkup:
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
    kb.button(text="🖍 Изменить", callback_data=f"{CB.CAMPAIGN_ADD_CONFIRM.value}:{Action.EDIT.value}"),
    kb.button(text="❌ Удалить", callback_data=f"{CB.CAMPAIGN_ADD_CONFIRM.value}:0"),
    # kb.button(text="❌ Удалить", callback_data=f"{CB.CLOSE.value}")
    return kb.adjust(3).as_markup()


# Подтвердить замену промо
def get_select_page_kb(
        end_page: bool,
        select_id: int,
        page: int,
        cb: str = CB.CONTRACT_PAGE.value,
        with_select_btn: bool = True
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    btn_count = 0
    if page > 0:
        btn_count += 1
        kb.button(text=f'⬅️ Пред стр.', callback_data=f'{cb}:{page - 1}:{Action.CONT.value}')
    if not end_page:
        btn_count += 1
        kb.button(text=f'След стр. ➡️ ', callback_data=f'{cb}:{page + 1}:{Action.CONT.value}')

    if with_select_btn:
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
        text="Продолжить",
        callback_data=f"{CB.CREATIVE_SELECT_CAMPAIGN.value}:0:{ Action.CONT.value}"
    )
    return kb.adjust(1).as_markup()


# кб для add_creative
# def get_add_creative_kb(campaigns: list[db.CampaignRow]) -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     for campaign in campaigns:
#         # Создаем кнопку с текстом из названия бренда и описания услуги
#         kb.button(
#             text=f"{campaign.brand} - {campaign.service}",
#             callback_data=f"{CB.CREATIVE_SELECT_CAMPAIGN.value}:{campaign.id}")
#     return kb.adjust(1).as_markup()


# кб для generate_link
def get_end_creative_kb(creative_id: int, with_add: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if with_add:
        kb.button(text="Добавить ссылку на опубликованный пост", callback_data=f'{CB.CREATIVE_ADD_LINK.value}:{creative_id}')
    kb.button(text="Готово", callback_data=f'{CB.CREATIVE_DONE.value}:{creative_id}')
    return kb.adjust(1).as_markup()


# выбор карты
def get_select_card_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Оплатить картой", callback_data=f"{CB.PAY_YK_NEW.value}:{1}")
    return kb.adjust(1).as_markup()


# кб со ссылкой на оплату в юкассе
# def get_yk_pay_kb(pay_id: str, campaign_id: str, save_cards: tuple) -> InlineKeyboardMarkup:
def get_yk_pay_kb(pay_id: str, amount_rub: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f"Оплатить {amount_rub} р.", url=Config.pay_link.format(payment_id=pay_id))
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
    kb.button(text="Да", callback_data=f'{CB.CONTRACT_NEXT_STEP_CHECK.value}:{step}:1'),
    kb.button(text="Нет", callback_data=f'{CB.CONTRACT_NEXT_STEP_CHECK.value}:{step}:0')
    return kb.adjust(1).as_markup()


# после добавления контрагента
def get_add_distributor_finish_kb(contractor_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Добавить еще контрагента', callback_data=CB.ADD_ANOTHER_DISTRIBUTOR.value)
    kb.button(text='Продолжить', callback_data=f'{CB.CONTINUE.value}:{contractor_id}')
    return kb.adjust(2).as_markup()


# выбор контрагента
def get_select_distributor_kb(contractors: list[db.DistributorRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for contractor in contractors:
        kb.button(text=contractor.name, callback_data=f"{CB.CONTRACT_DIST_SELECT.value}:{contractor.id}")

    kb.button(text="❌ Отмена", callback_data=CB.CLOSE.value)
    return kb.adjust(1).as_markup()


# выбор контрагента
def get_select_creative_platform_kb(platforms: list[db.PlatformRow]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for platform in platforms:
        kb.button(text=platform.url, callback_data=f"{CB.CREATIVE_SELECT_PLATFORM.value}:{platform.id}")

    return kb.adjust(1).as_markup()


# запрашивает есть ли часть договора
def get_close_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data=CB.CLOSE.value)
    return kb.adjust(1).as_markup()


# следующий шаг при создании акта
def get_check_next_step_act_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data=f'{CB.ACT_NEXT_STEP_CHECK.value}:{Action.YES.value}'),
    kb.button(text="Нет", callback_data=f'{CB.ACT_NEXT_STEP_CHECK.value}:{Action.NO.value}')
    return kb.adjust(2).as_markup()


# завершает создание акта
def get_end_act_kb(contract_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да, отправить в ОРД", callback_data=f'{CB.ACT_SEND.value}'),
    kb.button(text=f'Нет, изменить', callback_data=f'{CB.ACTS_SELECT_PAGE.value}:{contract_id}:{Action.YES.value}')

    return kb.adjust(1).as_markup()


# завершает создание акта
def get_send_monthly_statistic_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Отправить статистику в ОРД", callback_data=f'{CB.STATISTIC_MONTHLY.value}:{user_id}'),
    return kb.adjust(1).as_markup()


def get_subscription_main_kb(current_subscription: str | None, was_subscribed_at_least_once: bool) -> InlineKeyboardMarkup:
    if current_subscription:
        assert hasattr(Subscription, current_subscription), f"[get_subscription_main_kb] Invalid current_subscription: {current_subscription}"
    kb = InlineKeyboardBuilder()

    for subscription in Subscription:
        if subscription == Subscription.TESTER and was_subscribed_at_least_once:
            continue
        if current_subscription != subscription:
            kb.button(text=f"+ {subscription.value}", callback_data=f"{CB.SUBSCRIPTION_BUY_PLAN.value}:{subscription.name}")
    if current_subscription:
        kb.button(text='+ Приобрести больше токенов', callback_data=f"{CB.SUBSCRIPTION_BUY_TOKENS.value}")
        kb.button(text='❌ Отменить подписку', callback_data=f"{CB.SUBSCRIPTION_CANCEL.value}")
    return kb.adjust(1).as_markup()


def get_subscription_buy_plan_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text='Перейти к оплате', callback_data=f"{CB.PAY_YK_NEW.value}")
    kb.button(text='Назад', callback_data=f"{CB.SUBSCRIPTION_BUY_BACK.value}")
    return kb.adjust(1).as_markup()


def get_subscription_buy_tokens_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text='Перейти к оплате', callback_data=f"{CB.PAY_YK_NEW.value}")
    kb.button(text='Назад', callback_data=f"{CB.SUBSCRIPTION_BUY_BACK.value}")
    return kb.adjust(1).as_markup()


def get_subscription_cancel_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text='Отменить подписку', callback_data=f"{CB.SUBSCRIPTION_CANCEL_CONFIRMED.value}")
    kb.button(text='Назад', callback_data=f"{CB.SUBSCRIPTION_BUY_BACK.value}")
    return kb.adjust(1).as_markup()
