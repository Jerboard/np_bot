import os
import pytz


DEBUG = bool(int(os.getenv('DEBUG')))


class Config:
    debug = DEBUG
    # Параметры магазина
    mrh_login = os.getenv('MRH_LOGIN')
    mrh_pass1 = os.getenv('MRH_PASS1')
    mrh_pass2 = os.getenv('MRH_PASS2')

    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = os.getenv('REDIS_PORT', 6379)
    redis_db = os.getenv('REDIS_DB', 0)

    if DEBUG:
        token = os.getenv('TEST_TOKEN')  # test (test)
        bearer = os.getenv('VK_TEST_API_KEY')
    else:
        token = os.getenv('TOKEN')
        bearer = os.getenv('VK_TEST_API_KEY')
        # bearer = os.getenv('VK_API_KEY')

    default_email = 'dgushch@gmail.com'
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('POSTGRES_DB')
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    db_url = f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

    ttl_redis = 3600
    service_price = 400
    bot_link = os.getenv('BOT_LINK')
    pay_link = os.getenv('PAY_LINK')

    # YOO_ACCOUNT_ID = int(os.getenv('YOO_ACCOUNT_ID'))
    # YOO_SECRET_KEY = os.getenv('YOO_SECRET_KEY')
    # yoo_account_id = int(os.getenv('YOO_ACCOUNT_ID_TEST'))
    # yoo_secret_key = os.getenv('YOO_SECRET_KEY_TEST')
    yoo_account_id = '891569'
    yoo_secret_key = 'test_AtpTCVjudZJgiE8bVPHfO_4DLuURvqcTl65ZmbpSf7U'

    date_form = "%d.%m.%Y"
    ord_date_form = "%Y-%m-%d"
    storage_path = 'temp'

