import logging
import os.path
import typing as t
import httpx
import uuid

import db
from config import Config
from init import log_error
from enums import JStatus


# Функция для отправки данных в ОРД API
async def send_user_to_ord(
        ord_id: t.Union[str, int],
        name: str,
        role: str,
        j_type: str,
        inn: str,
        phone: str = None,
        rs_url=None
) -> int:
    url = f"https://api-sandbox.ord.vk.com/v1/person/{ord_id}"
    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "roles": [role],
        "juridical_details": {
            "type": j_type,
            "inn": inn,
            "phone": phone or "+7(495)709-56-39"  # Используем заглушку, если номер телефона пуст
        }
    }

    # if rs_url:
    #     data["rs_url"] = rs_url

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    log_error(f'send_user_to_ord response:\n{response.text}', wt=False)
    return response.status_code


# Функция для отправки данных о контрагенте в ОРД API
# async def send_contractor_to_ord(ord_id: str, name: str, role: str, j_type: str, inn: str, phone: str):
#     url = f"https://api-sandbox.ord.vk.com/v1/person/{ord_id}"
#     headers = {
#         "Authorization": f"Bearer {Config.bearer}",
#         "Content-Type": "application/json"
#     }
#     data = {
#         "name": name,
#         "roles": [role],
#         "juridical_details": {
#             "type": j_type,
#             "inn": inn,
#             "phone": phone  # Используем номер телефона, переданный в функцию
#         }
#     }
#
#     async with httpx.AsyncClient() as client:
#         response = await client.put(url, headers=headers, json=data)
#
#     return response


# Функция для отправки данных о договоре в ОРД API
async def send_contract_to_ord(
        ord_id: str,
        client_external_id: str,
        contractor_external_id: str,
        contract_date: str,
        serial: str,
        # vat_flag: list,
        amount: str
) -> int:
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
        "amount": str(amount)
    }
    if serial:
        data['serial'] = serial

    url = f"https://api-sandbox.ord.vk.com/v1/contract/{ord_id}"

    # for k, v in data.items():
    #     print(f'{k}: {v}')

    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    log_error(f'send_contract_to_ord code: {response.status_code}\nresponse:\n{response.text}', wt=False)
    return response.status_code


# Функция для отправки данных о платформе в ОРД API
# async def send_platform_to_ord(ord_id: str, platform_name: str, platform_url: str, person_external_id: str):
async def send_platform_to_ord(ord_id: str, platform_name: str, platform_url: str, dist_ord_id: str) -> int:
    url = f"https://api-sandbox.ord.vk.com/v1/pad/{ord_id}"

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

    log_error(f'send_contract_to_ord response:\n{response.text}', wt=False)
    return response.status_code


# регистрация медиа
async def register_media_file(file_path: str, ord_id: str, description: str) -> int:
    print(f'file_path: {os.path.exists(file_path)} {file_path}')
    print(f'description: {description}')

    url = f'https://api-sandbox.ord.vk.com/v1/media/{ord_id}'
    headers = {
        'Authorization': f'Bearer {Config.bearer}'
    }
    files = {
        'media_file': open(file_path, 'rb'),
    }
    data = {
        'description': 'Мы не храним данные о картах и пользователя все данные хранит сервис Юкасса'
    }
    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data, files=files)

    log_error(f'send_media_to_ord code:{response.status_code}\nresponse: {response.text}', wt=False)
    return response.status_code


async def send_creative_to_ord(
        creative_id,
        brand: str,
        creative_name: str,
        creative_text: str,
        description: str,
        media_ids: list,
        # media_ids: str,
        contract_ord_id: str,
):

    url = f"https://api-sandbox.ord.vk.com/v1/creative/{creative_id}"
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
        "pay_type": "cpc",
        "form": "text_graphic_block",
        # "targeting": "Школьники",
        # "url": "https://www.msu.ru",
        "texts": [creative_text],
        "media_external_ids": media_ids,
        "flags": [
            "social"
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    log_error(f'send_creative_to_ord code:{response.status_code}\nresponse: {response.text}', wt=False)
    if response.status_code <= 201:
        return response.json()

    else:
        response