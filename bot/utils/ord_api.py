import inspect
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


KKTUS = {
    '1.1.1', '1.1.2', '1.1.3', '1.1.4', '1.2.1',
    '2.1.1', '2.1.2', '2.1.3', '2.1.4',
    '3.1.1', '3.1.2', '3.1.3', '3.2.1',
    '4.1.1', '4.1.2', '4.1.3', '4.1.4', '4.2.1', '4.3.1', '4.3.2', '4.3.3',
    '5.1.1', '5.1.2', '5.2.1', '5.2.2', '5.2.3', '5.2.4', '5.2.5', '5.2.6', '5.2.7', '5.2.8', '5.2.9', '5.2.10', '5.2.11', '5.3.1',
    '6.1.1',
    '7.1.1', '7.1.2',
    '8.1.1',
    '9.1.1', '9.1.2', '9.1.3', '9.1.4', '9.1.5', '9.1.6', '9.1.7', '9.1.8', '9.2.1',

    '10.1.1', '10.2.1', '10.2.2', '10.3.1', '10.4.1', '10.4.2', '10.5.1', '10.6.1', '10.6.2', '10.6.3', '10.7.1', '10.8.1', '10.9.1', '10.9.2', '10.9.3',
    '10.9.4', '10.9.5', '10.9.6', '10.9.7', '10.9.8', '10.9.9', '10.9.10',

    '11.1.1', '11.1.2', '11.1.3',
    '12.1.1', '12.1.2', '12.1.3', '12.2.1', '12.2.2', '12.2.3', '12.2.4', '12.2.5',
    '13.1.1', '13.1.2', '13.1.3', '13.1.4', '13.1.5',
    '14.1.1', '14.1.2', '14.1.3', '14.1.4', '14.1.5', '14.1.6', '14.1.7', '14.1.8', '14.1.9', '14.1.10', '14.1.11', '14.1.12',
    '15.1.1', '15.1.2', '15.1.3', '15.1.4', '15.2.1', '15.2.2', '15.2.3', '15.2.4', '15.2.5', '15.2.6', '15.3.1', '15.3.2', '15.3.3', '15.3.4', '15.3.5',
    '16.1.1', '16.1.2',
    '17.1.1', '17.1.2', '17.1.3', '17.2.1', '17.2.2', '17.2.3', '17.3.1', '17.3.2', '17.3.3', '17.3.4', '17.4.1', '17.4.2', '17.4.3', '17.5.1', '17.5.2',
    '17.5.3', '17.5.4', '17.5.5', '17.5.6', '17.5.7', '17.5.8', '17.5.9', '17.5.10', '17.5.11',

    '18.1.1', '18.1.2', '18.1.3', '18.2.1', '18.3.1', '18.3.2', '18.3.3',
    '19.1.1', '19.1.2', '19.1.3', '19.1.4', '19.1.5', '19.2.1',
    '20.1.1', '20.1.2', '20.1.3', '20.1.4', '20.1.5',
    '21.1.1', '21.1.2', '21.1.3', '21.1.4', '21.1.5', '21.1.6', '21.2.1', '21.2.2', '21.3.1', '21.3.2', '21.3.3', '21.4.1', '21.4.2', '21.4.3', '21.4.4',
    '21.4.5', '21.4.6', '21.4.7', '21.4.8', '21.4.9', '21.4.10', '21.4.11', '21.4.12', '21.4.13',

    '22.1.1', '22.2.1', '22.2.2', '22.2.3', '22.2.4', '22.2.5', '22.3.1', '22.3.2', '22.3.3', '22.3.4',
    '23.1.1', '23.1.2', '23.2.1',
    '24.1.1', '24.1.2', '24.1.3', '24.1.4', '24.1.5', '24.1.6', '24.1.7', '24.1.8', '24.1.9', '24.1.10', '24.2.1',
    '25.1.1', '25.1.2', '25.1.3', '25.1.4', '25.1.5', '25.2.1',
    '26.1.1', '26.2.1', '26.2.2', '26.3.1', '26.4.1', '26.4.2', '26.4.3', '26.4.4', '26.4.5',
    '27.1.1', '27.1.2', '27.2.1',
    '28.1.1', '28.1.2', '28.1.3', '28.1.4', '28.1.5', '28.1.6', '28.1.7', '28.1.8', '28.1.9', '28.1.10', '28.1.11', '28.1.12', '28.1.13', '28.1.14', '28.1.15',
    '29.1.1', '29.1.2', '29.1.3', '29.1.4', '29.2.1', '29.2.2', '29.2.3', '29.2.4', '29.2.5', '29.2.6', '29.2.7', '29.2.8', '29.2.9',

    '30.1.1', '30.1.2', '30.1.3', '30.2.1', '30.2.2', '30.2.3', '30.2.4', '30.2.5', '30.2.6', '30.2.7', '30.2.8', '30.2.9', '30.2.10', '30.2.11', '30.3.1',
    '30.3.2', '30.3.3', '30.3.4', '30.3.5', '30.4.1', '30.4.2', '30.5.1', '30.5.2', '30.6.1', '30.6.2', '30.6.3', '30.7.1', '30.8.1', '30.8.2', '30.8.3',
    '30.8.4', '30.9.1', '30.10.1', '30.10.2', '30.10.3', '30.11.1', '30.11.2', '30.12.1', '30.13.1', '30.13.2', '30.14.1', '30.15.1'
}


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
        print(f"[{inspect.stack()[0][3]}] PUT {url} json={data}")
        response = await client.put(url, headers=headers, json=data)

    if response.status_code > 201:
        log_error(f'send_user_to_ord\nrequest:\nord_id: {ord_id}\n{data} \nresponse:\n{response.text}', wt=False)
    return response.status_code

'''
В договоре между нами и пользователем указываем:
- серийный номер (номер договора): [ИД клиента]
- тип: [оказание услуг]
- заказчик: [Клиент]
- исполнитель: [Мы] (ООО "ЮКЦ "ПАРТНЕР")
- предмет договора: [Иное]  # правильно определется предмет договора
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
        "amount": str(amount),
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
        print(f"[{inspect.stack()[0][3]}] PUT {url} json={data}")
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
        print(f"[{inspect.stack()[0][3]}] PUT {url} json={data}")
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
        print(f"[{inspect.stack()[0][3]}] PUT {url} json={data}")
        response = await client.put(url, headers=headers, data=data, files=files)

    if response.status_code > 201:
        log_error(f'send_media_to_ord\nrequest:\nord_id: {ord_id}\n{data} \nresponse:\n{response.text}', wt=False)
    return response.status_code


async def send_creative_to_ord(
        creative_id,
        brand: str,
        kktu: str,
        creative_name: str,
        creative_form: str,
        creative_text: list,
        description: str,
        media_ids: list,
        contract_ord_id: str,
        target_urls: list[str],
):

    url = f"{Config.ord_url}/v2/creative/{creative_id}"
    headers = {
        "Authorization": f"Bearer {Config.bearer}",
        "Content-Type": "application/json"
    }
    data = {
        "contract_external_id": contract_ord_id,
        "okveds": ["73.11"],
        "name": creative_name,
        "brand": brand,
        "kktus": [kktu],
        "category": description,
        "description": description,
        "pay_type": "other",
        "form": creative_form,
        "texts": creative_text,
        "media_external_ids": media_ids,
        "target_urls": target_urls,
    }

    async with httpx.AsyncClient() as client:
        print(f"[{inspect.stack()[0][3]}] PUT {url} json={data}")
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
        print(f"[{inspect.stack()[0][3]}] POST {url} json={data}")
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
        print(f"[{inspect.stack()[0][3]}] PUT {url} json={act_data}")
        response = await client.put(url, headers=headers, json=act_data)

    # if response.status_code > 201:
    log_error(f'send_act_to_ord\nrequest:\n{act_data} \nresponse {response.status_code}:\n{response.text}', wt=False)

    return response.status_code <= 201
