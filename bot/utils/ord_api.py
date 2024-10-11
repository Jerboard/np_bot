from datetime import datetime

import logging
import typing as t
import httpx

import db
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

    # if rs_url:
    #     data["rs_url"] = rs_url

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    if response.status_code > 201:
        log_error(f'send_user_to_ord\nrequest:\nord_id: {ord_id}\n{data} \nresponse:\n{response.text}', wt=False)
    return response.status_code


# Функция для отправки посреднического договора при регистрации ОРД API
# async def send_mediation_to_ord(ord_id: str, client_ord_id: str):
#     today = datetime.now().date()
#
#     url = f"{Config.ord_url}/v1/contract/{ord_id}"
#     headers = {
#         "Authorization": f"Bearer {Config.bearer}",
#         "Content-Type": "application/json"
#     }
#     data = {
#           "type": "mediation",
#           "client_external_id": client_ord_id,
#           "contractor_external_id": Config.partner_data['ord_id'],
#           "date": today.strftime(Config.ord_date_form),
#           "action_type": "commercial",
#           "subject_type": "mediation",
#           "flags": [
#             "vat_included",
#             "agent_acting_for_publisher"
#           ],
#     }
#     async with httpx.AsyncClient() as client:
#         response = await client.put(url, headers=headers, json=data)
#
#     return response

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
        # vat_flag: list,
        amount: str = None
) -> int:
    url = f"{Config.ord_url}/v1/contract/{ord_id}"
    data = {
        "type": "service",
        "client_external_id": client_external_id,
        "contractor_external_id": contractor_external_id,
        "date": contract_date,
        "subject_type": "org_distribution",
        "flags": [
            "vat_included",
            "contractor_is_creatives_reporter"
        ],
        # "amount": str(amount)
    }
    if serial:
        data['serial'] = serial

    if amount:
        data['amount'] = str(amount)

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
# async def send_platform_to_ord(ord_id: str, platform_name: str, platform_url: str, person_external_id: str):
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
        'Authorization': f'Bearer {Config.bearer}',
        # "Content-Type": "multipart/form-data"
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

'''
{'description': 'Мы не храним данные о картах и пользователя все данные хранит сервис Юкасса'} 
 'description'
response:
{"error":"Image file requires non-empty field 'description'"}
'''


async def send_creative_to_ord(
        creative_id,
        brand: str,
        creative_name: str,
        # creative_text: str,
        creative_text: list,
        description: str,
        media_ids: list,
        # media_ids: str,
        contract_ord_id: str,
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
        # "pay_type": "cpc",
        "pay_type": "other",
        "form": MediaType.BANNER.value,
        "texts": creative_text,
        "media_external_ids": media_ids,
        # "flags": [
        #     "native"
        # ]
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
        views: str,
        creative_date: datetime,

) -> str:
    now = datetime.now()

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
                    "date_end_actual": now.strftime(Config.ord_date_form)
                }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)

    # if response.status_code > 201:
    log_error(f'send_statistic_to_ord\nrequest:\n{data} \nresponse {response.status_code}:\n{response.text}', wt=False)

    response_data = response.json()
    external_ids = response_data.get('external_ids')
    return external_ids[0] if external_ids else None

'''
request:
{'items': [{'creative_external_id': '524275902-cr-7513269220', 'pad_external_id': '7181274585-p-6809174294', 'shows_count': 0, 'date_start_actual': '2024-10-11', 'date_end_actual': '2024-10-11'}]} 
response 200:
{"external_ids":["524275902-cr-7513269220__7181274585-p-6809174294__2024-10-01"]}


---------------------------------
request:
{'items': [{'creative_external_id': '524275902-cr-2463806352', 'pad_external_id': '7181274585-p-6809174294', 'shows_count': 0, 'date_start_actual': '2024-10-11', 'date_end_actual': '2024-10-11'}]} 
response 200:
{"external_ids":["524275902-cr-2463806352__7181274585-p-6809174294__2024-10-01"]}

---------------------------------
request:
{'items': [{'creative_external_id': '524275902-cr-2463806352', 'pad_external_id': '7181274585-p-6809174294', 'shows_count': 0, 'date_start_actual': '2024-10-11', 'date_end_actual': '2024-10-11'}]} 
response 200:
{"external_ids":["524275902-cr-2463806352__7181274585-p-6809174294__2024-10-01"]}

---------------------------------
request:
{'items': [{'creative_external_id': '524275902-cr-2463806352', 'pad_external_id': '7181274585-p-6809174294', 'shows_count': 0, 'date_start_actual': '2024-10-11', 'date_end_actual': '2024-10-11'}]} 
response 200:
{"external_ids":["524275902-cr-2463806352__7181274585-p-6809174294__2024-10-01"]}

---------------------------------
request:
{'items': [{'creative_external_id': '524275902-cr-7475978899', 'pad_external_id': '7181274585-p-6809174294', 'shows_count': 0, 'date_start_actual': '2024-10-11', 'date_end_actual': '2024-10-11'}]} 
response 200:
{"external_ids":["524275902-cr-7475978899__7181274585-p-6809174294__2024-10-01"]}
'''

