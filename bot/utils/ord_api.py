from datetime import datetime

import logging
import typing as t
import httpx
import calendar

import db
import utils
from config import Config
from init import log_error
from enums import MediaType


# Функция для отправки данных в ОРД API
async def send_user_to_ord(
        ord_id: t.Union[str, int],
        name: str,
        role: str,
        j_type: str,
        inn: str
) -> int:
    url = f"{Config.ord_url}/v1/person/{ord_id}"
    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "roles": [role],
        "juridical_details": {
            "type": j_type,
            "inn": inn
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    if response.status_code > 201:
        log_error(f'send_user_to_ord\nrequest:\nord_id: {ord_id}\n{data} \nresponse:\n{response.text}', wt=False)
    return response.status_code

'''
В договоре указываем:
- серийный номер (номер договора): [ИД клиента]
- тип: [оказание услуг]
- заказчик: [Клиент]
- исполнитель: [Мы] (ООО "ЮКЦ "ПАРТНЕР")
- предмет договора: [Иное]
- дата заключения: [дата регистрации клиента]
'''


# Функция для отправки данных о договоре в ОРД API
async def send_contract_to_ord(
        ord_id: str,
        client_external_id: str,
        contractor_external_id: str,
        contract_date: str,
        serial: str = None,
        amount: str = '0'
) -> int:
    url = f"{Config.ord_url}/v1/contract/{ord_id}"
    data = {
        "type": "service",
        "client_external_id": client_external_id,
        "contractor_external_id": contractor_external_id,
        "date": contract_date,
        "subject_type": "org_distribution",
        "amount": amount,
        "flags": [
            "vat_included",
            # "contractor_is_creatives_reporter"
        ],
        # "amount": str(amount)
    }
    if serial:
        data['serial'] = serial

    # for k, v in data.items():
    #     print(f'{k}: {v}')

    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    if response.status_code > 201:
        log_error(f'send_contract_to_ord\nrequest:\nord_id: {ord_id}\n{data} \nresponse:\n{response.text}', wt=False)
    return response.status_code


# Функция для отправки данных о платформе в ОРД API
async def send_platform_to_ord(ord_id: str, platform_name: str, platform_url: str, dist_ord_id: str) -> int:
    url = f"{Config.ord_url}/v1/pad/{ord_id}"

    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }

    data = {
        "person_external_id": dist_ord_id,
        "is_owner": True,
        "type": "web",
        "name": platform_name,
        "url": platform_url
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    if response.status_code > 201:
        log_error(f'send_contract_to_ord\nrequest:\nord_id: {ord_id}\n{data} \nresponse:\n{response.text}', wt=False)
    return response.status_code


# регистрация медиа
async def register_media_file(file_path: str, ord_id: str, description: str) -> int:
    url = f'{Config.ord_url}/v1/media/{ord_id}'
    headers = {
        'Authorization': f'Bearer {Config.bearer}'
    }
    files = {
        'media_file': open(file_path, 'rb'),
    }
    data = {
        'description': 'Мы не храним данные'
    }
    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, data=data, files=files)

    if response.status_code > 201:
        log_error(f'send_media_to_ord\nrequest:\nord_id: {ord_id}\n{data} \nresponse:\n{response.text}', wt=False)
    return response.status_code


async def send_creative_to_ord(
        creative_id,
        brand: str,
        creative_name: str,
        creative_form: str,
        creative_text: list,
        description: str,
        media_ids: list,
        contract_ord_id: str,
        target_urls: list[str],
):

    url = f"{Config.ord_url}/v1/creative/{creative_id}"
    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }
    data = {
        "contract_external_id": contract_ord_id,
        "okveds": ["73.11"],
        "name": creative_name,
        "brand": brand,
        "category": description,
        "description": description,
        "pay_type": "other",
        "form": creative_form,
        "texts": creative_text,
        "media_external_ids": media_ids,
        "target_urls": target_urls
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    if response.status_code <= 201:
        return response.json()

    else:
        log_error(
            f'send_creative_to_ord\nrequest:\nord_id: {creative_id}\n{data} \nresponse:\n{response.text}',
            wt=False
        )
        response


# Функция для отправки статистики в ОРД API
async def send_statistic_to_ord(
        creative_ord_id: str,
        platform_ord_id: str,
        views: int,
        creative_date: datetime,
) -> str:
    end_date = datetime.now()

    # Проверка, отличается ли месяц в creative_date от текущего месяца
    if creative_date.month != end_date.month:
        last_day_of_month = calendar.monthrange(creative_date.year, creative_date.month)[1]
        end_date = creative_date.replace(day=last_day_of_month)

    url = f"{Config.ord_url}/v1/statistics"
    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }

    data = {
        'items': [
                {
                    "creative_external_id": creative_ord_id,
                    "pad_external_id": platform_ord_id,
                    "shows_count": int(views),
                    "date_start_actual": creative_date.strftime(Config.ord_date_form),
                    "date_end_actual": end_date.strftime(Config.ord_date_form)
                }
        ]
    }

    utils.print_dict(data)

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)

    if response.status_code > 201:
        log_error(
            f'send_statistic_to_ord\nrequest:\n{data} \nresponse {response.status_code}:\n{response.text}',
            wt=False
        )
    response_data = response.json()
    external_ids = response_data.get('external_ids')
    return external_ids[0] if external_ids else None


# Функция для отправки актов в ОРД API
async def send_acts_to_ord(
    ord_id: str,
    act_data: dict,
) -> bool:
    url = f"{Config.ord_url}/v1/invoice/{ord_id}"

    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=act_data)

    # if response.status_code > 201:
    log_error(f'send_act_to_ord\nrequest:\n{act_data} \nresponse {response.status_code}:\n{response.text}', wt=False)

    return response.status_code <= 201
