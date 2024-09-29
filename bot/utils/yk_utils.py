from yookassa import Payment

import json

from init import log_error
from config import Config


def create_pay_link(email: str = Config.default_email) -> str:
    print(f'email: {email}')
    payment = Payment.create({
        "amount": {
            "value": Config.service_price,
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "bank_card"
        },
        'save_payment_method': True,
        "capture": True,
        "description": 'Оплата услуг маркировки рекламы',
        "confirmation": {
            "type": "redirect",
            "return_url": Config.bot_link
        },
        "receipt": {
            "customer": {
                "email": 'dgushch@gmail.com'
            },
            "items": [
                {
                    "description": f"Оплата 400 рубликов",
                    "quantity": "1.00",
                    "amount": {
                        "value": Config.service_price,
                        "currency": "RUB"
                    },
                    "vat_code": 0,
                    "payment_mode": "full_payment",
                    "payment_subject": "service"
                }
            ]
        },
    })

    return payment.id


# быстрая оплата рекурент
def fast_pay(last_pay_id: str, email: str = Config.default_email) -> Payment:
    payment = Payment.create({
        "amount": {
            "value": Config.service_price,
            "currency": "RUB"
        },
        'save_payment_method': True,
        "capture": True,
        "payment_method_id": last_pay_id,
        "description": 'Оплата маркировки рекламы',
        "confirmation": {
            "type": "redirect",
            "return_url": Config.bot_link
        },
        "receipt": {
            "customer": {
                "email": email
            },
            "items": [
                {
                    "description": 'Оплата маркировки рекламы',
                    "quantity": "1.00",
                    "amount": {
                        "value": Config.service_price,
                        "currency": "RUB"
                    },
                    "vat_code": "1",
                    "payment_mode": "full_payment",
                    "pament_subject": "service"
                }
            ]
        },
    })

    return payment



'''
{"card": {"card_product": {"code": "E"}, "card_type": "MasterCard", "expiry_month": "12", "expiry_year": "2024", 
"first6": "555555", "issuer_country": "US", "last4": "4444"}, "id": "2e35daf1-000f-5000-a000-1e7f1fb0116d", 
"saved": true, "title": "Bank card *4444", "type": "bank_card"}
'''