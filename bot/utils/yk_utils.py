from yookassa import Payment

import json

from init import log_error
from config import SERVICE_PRICE, BOT_LINK


def create_pay_link(campaign_id: str) -> str:
    payment = Payment.create({
        "amount": {
            "value": SERVICE_PRICE,
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "bank_card"
        },
        'save_payment_method': True,
        "capture": True,
        "description": campaign_id,
        "confirmation": {
            "type": "redirect",
            "return_url": BOT_LINK
        },
        "receipt": {
            "customer": {
                "email": "gdruk@gmail.com"
            },
            "items": [
                {
                    "description": f"Оплата 400 рубликов",
                    "quantity": "1.00",
                    "amount": {
                        "value": SERVICE_PRICE,
                        "currency": "RUB"
                    },
                    "vat_code": "1",
                    "payment_mode": "full_payment",
                    "payment_subject": "service"
                }
            ]
        },
    })

    return payment.id


# проверка оплаты по ю кассе
def check_pay_yoo(pay_id: str) -> tuple:
    payment = Payment.find_one(pay_id)
    if payment.paid:
        pay_data = json.loads(payment.payment_method.json())

        log_error(f'{pay_data}', wt=False)
        log_error(f'{pay_data["card"]["card_type"]} *{pay_data["card"]["last4"]}', wt=False)
        return f'{pay_data["card"]["card_type"]} **{pay_data["card"]["last4"]}', payment.description


'''
{"card": {"card_product": {"code": "E"}, "card_type": "MasterCard", "expiry_month": "12", "expiry_year": "2024", 
"first6": "555555", "issuer_country": "US", "last4": "4444"}, "id": "2e35daf1-000f-5000-a000-1e7f1fb0116d", 
"saved": true, "title": "Bank card *4444", "type": "bank_card"}
'''