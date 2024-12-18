import sys
import logging
import asyncio
import os

from init import log_error, set_main_menu, bot, scheduler
from config import Config
from handlers import dp
from db.base_db import init_models
import utils as ut


async def main() -> None:
    # await ut.send_statistic()
    if not os.path.exists(Config.storage_path):
        os.mkdir(Config.storage_path)

    await init_models()
    await set_main_menu()
    if not Config.debug:
        await ut.start_schedulers()
    # await ut.request_monthly_statistic()
    await bot.delete_webhook (drop_pending_updates=True)
    await dp.start_polling(bot)
    # scheduler.shutdown()


if __name__ == "__main__":
    if Config.debug:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    else:
        log_error('start_bot', wt=False)
    asyncio.run(main())
