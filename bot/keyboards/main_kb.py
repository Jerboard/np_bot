from telebot import types

from config import PAY_LINK
from init import log_error


# стартовая клавиатура
def get_start_kb() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    confirm_button = types.InlineKeyboardButton('Подтвердить', callback_data='confirm_user')
    # confirm_button = types.InlineKeyboardButton('Тест', callback_data='pay_yk:12345')
    change_role_button = types.InlineKeyboardButton('Сменить роль', callback_data='change_role')
    return markup.row(confirm_button, change_role_button)


# кб для  get_process_role_change_kb
def get_process_role_change_kb() -> types.InlineKeyboardMarkup:
    markup2 = types.InlineKeyboardMarkup()
    advertiser_button = types.InlineKeyboardButton('Рекламодатель', callback_data='advertiser')
    publisher_button = types.InlineKeyboardButton('Рекламораспространитель', callback_data='publisher')
    return markup2.row(advertiser_button, publisher_button)


# кб для  register
def get_register_kb() -> types.InlineKeyboardMarkup:
    markup1 = types.InlineKeyboardMarkup()
    IP = types.InlineKeyboardButton('ИП', callback_data='ip')
    UR = types.InlineKeyboardButton('Юр. лицо', callback_data='juridical')
    FIZ = types.InlineKeyboardButton('Физическое лицо', callback_data='physical')
    markup1.row(IP, UR)
    return markup1.row(FIZ)


# кб для  inn_collector
def get_inn_collector_kb() -> types.InlineKeyboardMarkup:
    markup2 = types.InlineKeyboardMarkup()
    advertiser_button = types.InlineKeyboardButton('Рекламодатель', callback_data='advertiser')
    publisher_button = types.InlineKeyboardButton('Рекламораспространитель', callback_data='publisher')
    return markup2.row(advertiser_button, publisher_button)


# кб для  preloader_advertiser_entity
def get_preloader_advertiser_entity_kb() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    yes = types.InlineKeyboardButton('Да', callback_data='register_advertiser_entity')
    no = types.InlineKeyboardButton('Нет', callback_data='no_advertiser')
    return markup.row(yes, no)


# кб для  register_advertiser_entity
def get_register_advertiser_entity_kb() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    IP = types.InlineKeyboardButton('ИП', callback_data='ip_advertiser')
    UR = types.InlineKeyboardButton('Юр. лицо', callback_data='ur_advertiser')
    FIZ = types.InlineKeyboardButton('Физическое лицо', callback_data='fiz_advertiser')
    markup.row(IP, UR)
    return markup.row(FIZ)


# кб для preloader_choose_platform
def get_preloader_choose_platform_kb() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    yes = types.InlineKeyboardButton('Да', callback_data='choose_platform')
    no = types.InlineKeyboardButton('Нет', callback_data='no_choose_platform')
    return markup.row(yes, no)


# кб для choose_platform
def get_choose_platform_kb() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    vk_button = types.InlineKeyboardButton('ВКонтакте', callback_data='vk')
    instagram_button = types.InlineKeyboardButton('Instagram', callback_data='instagram')
    youtube_button = types.InlineKeyboardButton('YouTube', callback_data='youtube')
    telegram_channel_button = types.InlineKeyboardButton('Telegram-канал', callback_data='telegram_channel')
    personal_telegram_button = types.InlineKeyboardButton('Личный Telegram', callback_data='personal_telegram')
    # other_button = types.InlineKeyboardButton('Другое', callback_data='other')
    other_button = types.InlineKeyboardButton('Другое', callback_data='in_dev')
    markup.row(vk_button, instagram_button)
    markup.row(telegram_channel_button, youtube_button)
    return markup.row(personal_telegram_button, other_button)


# кб для platform_url_collector
def get_platform_url_collector_kb() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton('Да, верно', callback_data='correct_platform')
    change_button = types.InlineKeyboardButton('Исправить', callback_data='change_platform')
    delete_button = types.InlineKeyboardButton('Удалить', callback_data='delete_platform')
    return markup.row(yes_button, change_button, delete_button)


# кб для process_average_views
def get_process_average_views_kb(contractors: tuple[tuple]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for contractor in contractors:
        contractor_name = contractor[2] if contractor[2] else contractor[1]
        contractor_button = types.InlineKeyboardButton(contractor_name,
                                                       callback_data=f"contractor1_{contractor[0]}")
        markup.add(contractor_button)

    return markup


# кб для finalize_platform_data
def get_finalize_platform_data_kb() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    add_another_button = types.InlineKeyboardButton('Добавить еще площадку',
                                                    callback_data='add_another_platform')
    continue_button = types.InlineKeyboardButton('Продолжить', callback_data='continue_to_entity')
    return markup.row(add_another_button, continue_button)


# кб для confirm_ad_campaign
def get_confirm_ad_campaign_kb(campaign_id) -> types.InlineKeyboardMarkup:
    reply_markup = types.InlineKeyboardMarkup()
    return reply_markup.add(
        types.InlineKeyboardButton("Да, верно", callback_data=f"confirm_ad_campaign:{campaign_id}"),
        types.InlineKeyboardButton("Изменить", callback_data=f"change_ad_campaign:{campaign_id}"),
        types.InlineKeyboardButton("Удалить", callback_data=f"delete_ad_campaign:{campaign_id}")
    )


# кб для ask_for_additional_link
def get_ask_for_additional_link_kb(campaign_id) -> types.InlineKeyboardMarkup:
    reply_markup = types.InlineKeyboardMarkup()
    return reply_markup.add(
        types.InlineKeyboardButton("Да, верно", callback_data=f"confirm_ad_campaign:{campaign_id}"),
        types.InlineKeyboardButton("Изменить", callback_data=f"change_ad_campaign:{campaign_id}"),
        types.InlineKeyboardButton("Удалить", callback_data=f"delete_ad_campaign:{campaign_id}")
    )


# кб для add_creative
def get_add_creative_kb(campaigns) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for idx, campaign in enumerate(campaigns):
        # Создаем кнопку с текстом из названия бренда и описания услуги
        markup.add(types.InlineKeyboardButton(f"{campaign[1]} - {campaign[2]}",
                                              callback_data=f"choose_campaign_{campaign[0]}"))
    return markup


# кб для handle_creative_upload
def get_handle_creative_upload_kb(campaign_id) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Добавить файл или текст", callback_data=f"add_more_{campaign_id}"))
    # markup.add(types.InlineKeyboardButton("Продолжить", callback_data=f"continue_creative_{campaign_id}"))
    markup.add(types.InlineKeyboardButton("Продолжить", callback_data=f"pay_yk:{campaign_id}"))
    return markup


# кб для handle_creative_link
def get_handle_creative_link_kb(ord_id) -> types.InlineKeyboardMarkup:
    # Предложение добавить еще одну ссылку или закончить
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Добавить ссылку на другую площадку", callback_data=f"add_link_{ord_id}"))
    markup.add(types.InlineKeyboardButton("Готово", callback_data=f"link_done_{ord_id}"))
    return markup


# кб для generate_link
def generate_link_markup() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Добавить ссылку на другую площадку", callback_data="add_link"))
    markup.add(types.InlineKeyboardButton("Готово", callback_data="link_done"))
    return markup


# кб со ссылкой на оплату в юкассе
# def get_yk_pay_kb(pay_id: str, campaign_id: str, save_cards: tuple) -> types.InlineKeyboardMarkup:
def get_yk_pay_kb(pay_id: str,save_cards: tuple) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Оплатить 400 р.", url=PAY_LINK.format(payment_id=pay_id)))
    for card in save_cards:
        markup.add(types.InlineKeyboardButton(f"Оплатить {card[0]}", callback_data=f"in_dev"))

    # markup.add(types.InlineKeyboardButton("Продолжить", callback_data=f"continue_creative_:{pay_id}:{campaign_id}"))
    markup.add(types.InlineKeyboardButton("Продолжить", callback_data=f"continue_creative_:{pay_id}"))
    return markup
