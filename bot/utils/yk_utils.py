from yookassa import Payment, Refund

import json
import uuid

from config import Config


def create_simple_pay_link(email: str = None, amount_rub: int = 500, metadata: dict = None) -> str:
    if not email:
        email = Config.default_email

    payment_body = {
        "amount": {
            "value": str(amount_rub),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": Config.bot_link,
        },
        "capture": True,
        "description": "Оплата услуг маркировки рекламы",
        "receipt": {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": f"Оплата услуг маркировки рекламы",
                        "quantity": "1.00",
                        "amount": {
                            "value": str(amount_rub),
                            "currency": "RUB"
                        },
                        "vat_code": 0,
                        "payment_mode": "full_payment",
                        "payment_subject": "service"
                    }
                ]
            },
    }

    if metadata:
        payment_body['metadata'] = metadata

    return Payment.create(payment_body, uuid.uuid4()).id


def create_recurrent_pay_link(email: str = Config.default_email) -> str:
    raise NotImplementedError('[create_recurrent_pay_link] Function is not implemented.')
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


# вернуть деньги
def refund_payment(pay_id: str):
    raise NotImplementedError('[create_recurrent_pay_link] Function is not implemented.')
    Refund.create({
        "amount": {
            "value": Config.token_price,
            "currency": "RUB"
        },
        "payment_id": pay_id
    })


# быстрая оплата рекурент
def fast_pay(last_pay_id: str, email: str = None) -> Payment:
    raise NotImplementedError('[fast_pay] Function is not implemented.')
    if not email:
        email = Config.default_email
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


# проверка оплаты по ю кассе
def get_payment_card_info(payment: Payment) -> str:
    raise NotImplementedError('[get_payment_card_info] Function is not implemented.')
    pay_data = json.loads(payment.payment_method.json())
    return f'{pay_data["card"]["card_type"]} **{pay_data["card"]["last4"]}'

'''
{"card": {"card_product": {"code": "E"}, "card_type": "MasterCard", "expiry_month": "12", "expiry_year": "2024", 
"first6": "555555", "issuer_country": "US", "last4": "4444"}, "id": "2e35daf1-000f-5000-a000-1e7f1fb0116d", 
"saved": true, "title": "Bank card *4444", "type": "bank_card"}
'''