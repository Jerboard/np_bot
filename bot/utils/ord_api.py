import logging
import requests
import httpx
import uuid

import db
from config import Config
from init import log_error
from enums import JStatus


# Функция для отправки данных в ОРД API
async def send_to_ord(user_id: int, name: str, role: str, j_type: str, inn: int, phone: str = None, rs_url=None) -> int:
    url = f"https://api-sandbox.ord.vk.com/v1/person/{user_id}"
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

    if rs_url:
        data["rs_url"] = rs_url

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    log_error(f'>>> {response.text}', wt=False)
    return response.status_code


# Функция для отправки данных о контрагенте в ОРД API
async def send_contractor_to_ord(ord_id: str, name: str, role: str, j_type: str, inn: str, phone: str, rs_url: str):
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
            "phone": phone  # Используем номер телефона, переданный в функцию
        }
    }
    if rs_url is not None:
        data["rs_url"] = rs_url

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    return response


# Функция для отправки данных о договоре в ОРД API
async def send_contract_to_ord(
        ord_id: str,
        client_external_id: str,
        contractor_external_id: str,
        contract_date: str,
        serial: str,
        vat_flag: list,
        amount: int
) -> bool:
    data = {
        "type": "service",
        "client_external_id": client_external_id,
        "contractor_external_id": contractor_external_id,
        "date": contract_date,
        "serial": serial,
        "subject_type": "org_distribution",
        "flags": vat_flag,
        "amount": str(amount)
    }

    url = f"https://api-sandbox.ord.vk.com/v1/contract/{ord_id}"

    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        return True
    else:
        return False


# Функция для отправки данных о платформе в ОРД API
async def send_platform_to_ord(ord_id: str, platform_name: str, platform_url: str, person_external_id: str):
    url = f"https://api-sandbox.ord.vk.com/v1/pad/{ord_id}"

    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }

    data = {
        "person_external_id": person_external_id,
        "is_owner": True,
        "type": "web",
        "name": platform_name,
        "url": platform_url
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        return True
    else:
        return False


# регистрация медиа
async def register_media_file(file_path: str, campaign_id: int, description: str) -> str:
    media_id = f"{campaign_id}_media_{uuid.uuid4()}"
    url = f'https://api-sandbox.ord.vk.com/v1/media/{media_id}'
    headers = {
        'Authorization': f'Bearer {Config.bearer}'
    }
    files = {
        'media_file': open(file_path, 'rb')
    }
    # description = db.query_db('SELECT service FROM ad_campaigns WHERE campaign_id = ?', (campaign_id,), one=True)[0]
    data = {
        'description': description
    }
    async with httpx.AsyncClient() as client:
        await client.put(url, headers=headers, json=data, files=files)
    return media_id


async def send_creative_to_ord(
        creative_id,
        brand: str,
        creative_name: str,
        creative_text: str,
        description,
        # media_ids: list,
        media_ids: str,
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
        "targeting": "Школьники",
        "url": "https://www.msu.ru",
        "texts": creative_text,
        "media_external_ids": media_ids
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=data)

    return response.json()