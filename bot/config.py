import os


DEBUG = bool(int(os.getenv('DEBUG')))

# Параметры магазина
mrh_login = os.getenv('MRH_LOGIN')
mrh_pass1 = os.getenv('MRH_PASS1')
mrh_pass2 = os.getenv('MRH_PASS2')


redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = os.getenv('REDIS_PORT', 6379)
redis_db = os.getenv('REDIS_DB', 0)

if DEBUG:
    TOKEN = os.getenv('TEST_TOKEN')  # test (test)
else:
    TOKEN = os.getenv('TEST_TOKEN')
    # TOKEN = os.getenv('TOKEN')

VK_API_KEY = os.getenv('VK_API_KEY')
VK_TEST_API_KEY = os.getenv('VK_TEST_API_KEY')
connect_data = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'dbname': os.getenv('POSTGRES_DB'),
}

TTL_REDIS = 3600
SERVICE_PRICE = 400
BOT_LINK = os.getenv('BOT_LINK')
PAY_LINK = os.getenv('PAY_LINK')


# YOO_ACCOUNT_ID = int(os.getenv('YOO_ACCOUNT_ID'))
# YOO_SECRET_KEY = os.getenv('YOO_SECRET_KEY')
YOO_ACCOUNT_ID = int(os.getenv('YOO_ACCOUNT_ID_TEST'))
YOO_SECRET_KEY = os.getenv('YOO_SECRET_KEY_TEST')




# ilia
