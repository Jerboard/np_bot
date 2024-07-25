import sys
import logging

from init import log_error, set_main_menu
from config import DEBUG
from handlers import bot
from handlers.common import auto_submit_statistics
from db.create_db import create_tables
from utils import app


if __name__ == '__main__':
    if DEBUG:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    else:
        log_error('start_bot', with_traceback=False)
    set_main_menu()
    create_tables()
    # Вызов функции для автоматической подачи статистики
    auto_submit_statistics()
    print('start_bot')
    bot.polling(none_stop=True, logger_level=logging.INFO)
    # app.run()
