import logging
import requests
import httpx

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

    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()

    if response.status_code in [200, 201]:
        return True
    else:
        return False



