
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramBadRequest

import db
from init import dp, bot, log_error


@dp.errors()
async def errors(ex: ErrorEvent):
    msg = log_error(ex)
    user_id = ex.update.message.chat.id if ex.update.message else 0

    if user_id and ex != TelegramBadRequest:
        await bot.send_message(
            chat_id=user_id,
            text='‼️ Что-то сломалось! Сообщите разработчикам, чтоб мы могли это исправить\n\n'
                 'В сообщении расскажите о ваших последних действиях')