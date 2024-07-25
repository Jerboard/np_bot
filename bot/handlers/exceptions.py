from init import bot, log_error


@bot.exception_handler()
def log_exception(ex):
    print(type(ex))
    print(ex)
    log_error(ex)



    # from aiogram.types import ErrorEvent
    # from aiogram.exceptions import TelegramBadRequest
    #
    # import db
    # from init import dp, bot, log_error
    #
    # @dp.errors()
    # async def errors_handler(ex: ErrorEvent):
    #     msg = log_error(ex)
    #
    #     user_id = ex.update.message.chat.id if ex.update.message else 0
    #     await db.save_error(user_id, msg)
    #
    #     if user_id and not ex != TelegramBadRequest:
    #         await bot.send_message(
    #             chat_id=user_id,
    #             text='‼️ Что-то сломалось! Сообщите разработчикам, чтоб мы могли это исправить\n\n'
    #                  'В сообщении расскажите о ваших последних действиях')