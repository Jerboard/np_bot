import os


DEBUG = bool(int(os.getenv('DEBUG')))

# Параметры магазина
mrh_login = "markirovkaNP"
mrh_pass1 = "shNcJ5nQpyx9821eemKM"
mrh_pass2 = "LGb9k7QMZ5c3lzuqM2pI"

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
