import sys
import logging
import asyncio
import os

from init import log_error, set_main_menu, bot
from config import Config
from handlers import dp
from db.base_db import init_models
# from handlers.common import auto_submit_statistics
# from db.create_db import create_tables


async def main() -> None:
    # await db_command()
    if not os.path.exists(Config.storage_path):
        os.mkdir(Config.storage_path)
    await init_models()
    await set_main_menu()
    await bot.delete_webhook (drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    if Config.debug:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    else:
        log_error('start_bot', wt=False)
    asyncio.run(main())