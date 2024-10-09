import os

from enums import JStatus, Role

DEBUG = bool(int(os.getenv('DEBUG')))


class Config:
    debug = DEBUG

    if DEBUG:
        token = os.getenv('TEST_TOKEN')  # test (test)
        bearer = os.getenv('VK_TEST_API_KEY')
        ord_url = 'https://api-sandbox.ord.vk.com'
        service_price = 10
        default_email = 'dgushch@gmail.com'
        db_name = os.getenv('POSTGRES_DB')
        yoo_account_id = '891569'
        yoo_secret_key = 'test_AtpTCVjudZJgiE8bVPHfO_4DLuURvqcTl65ZmbpSf7U'

    else:
        token = os.getenv('TOKEN')
        bearer = os.getenv('VK_API_KEY')
        ord_url = 'https://api.ord.vk.com'
        db_name = os.getenv('POSTGRES_WORK_DB')
        service_price = 1
        default_email = 'mark.check@np61.ru'
        yoo_account_id = os.getenv('YOO_ACCOUNT_ID')
        yoo_secret_key = os.getenv('YOO_SECRET_KEY')

    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    db_url = f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

    bot_link = os.getenv('BOT_LINK')
    pay_link = os.getenv('PAY_LINK')

    # YOO_ACCOUNT_ID = int(os.getenv('YOO_ACCOUNT_ID'))
    # YOO_SECRET_KEY = os.getenv('YOO_SECRET_KEY')
    # yoo_account_id = int(os.getenv('YOO_ACCOUNT_ID_TEST'))
    # yoo_secret_key = os.getenv('YOO_SECRET_KEY_TEST')


    date_form = "%d.%m.%Y"
    ord_date_form = "%Y-%m-%d"
    storage_path = 'temp'

    partner_data = {
        'ord_id': os.getenv('OWN_ORD_ID'),
        'name': os.getenv('OWN_NAME'),
        'inn': os.getenv('OWN_INN'),
        'role': Role.PUBLISHER.value,
        # 'role': 'org_distribution',
        'j_type': JStatus.JURIDICAL.value
    }
