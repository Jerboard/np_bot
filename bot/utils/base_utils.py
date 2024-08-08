from datetime import datetime


# Функция для получения ord_id
def get_ord_id(chat_id, campaign_id):
    return f"{chat_id}.{campaign_id}"


def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, "%d.%m.%Y")
        return True
    except ValueError:
        return False
