import os


DEBUG = bool(int(os.getenv('DEBUG')))

# Параметры магазина
mrh_login = "markirovkaNP"
mrh_pass1 = "shNcJ5nQpyx9821eemKM"
mrh_pass2 = "LGb9k7QMZ5c3lzuqM2pI"


redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = os.getenv('REDIS_PORT', 6379)
redis_db = os.getenv('REDIS_DB', 0)

# Замените 'YOUR_TOKEN' на ваш токен, полученный при создании бота в Telegram
TOKEN2 = '7494012774:AAHGtlNLIF-L4hJ3Sn3GuA2IBJWXC2zISas'
if DEBUG:
    # TOKEN = os.getenv('TEST_TOKEN')  # test (test)
    TOKEN = '7181274585:AAEPJ_CXjhKFR3CiLhV8W9AS_8KmHej7JmI' # test (test)

else:
    TOKEN = os.getenv('TOKEN')

VK_API_KEY = 'f29beaf7aef0465d90e03d8ba17d3bde'
VK_TEST_API_KEY = '633962f71ade453f997d179af22e2532'
connect_data = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'dbname': os.getenv('POSTGRES_DB'),
}

TTL_REDIS = 3600
SERVICE_PRICE = 400
BOT_LINK = 'https://t.me/markirovkaNP_bot'
PAY_LINK = 'https://yoomoney.ru/api-pages/v2/payment-confirm/epl?orderId={payment_id}'

# YOO_ACCOUNT_ID = int(os.getenv('YOO_ACCOUNT_ID'))
# YOO_SECRET_KEY = os.getenv('YOO_SECRET_KEY')
YOO_ACCOUNT_ID = 423024
YOO_SECRET_KEY = 'test_YmWKvH-Dure8bnEhkRLboWwvp6yoiRzD4nzE3_xPIVs'



# ilia
