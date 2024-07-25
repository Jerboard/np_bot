
# Функция для отправки данных о контрагенте в ОРД API
def send_contractor_to_ord(ord_id, name, role, juridical_type, inn, phone, rs_url):
    try:
        assert juridical_type in ['physical', 'juridical', 'ip'], f"Invalid juridical_type: {juridical_type}"

        url = f"https://api-sandbox.ord.vk.com/v1/person/{ord_id}"
        headers = {
            "Authorization": f"Bearer 633962f71ade453f997d179af22e2532",
            "Content-Type": "application/json"
        }
        data = {
            "name": name,
            "roles": [role],
            "juridical_details": {
                "type": juridical_type,
                "inn": inn,
                "phone": phone  # Используем номер телефона, переданный в функцию
            }
        }

        if rs_url is not None:
            data["rs_url"] = rs_url

        # Логирование данных запроса
        logging.debug(f"Sending data to ORD API: {data}")

        response = requests.put(url, headers=headers, json=data)
        # Логирование данных ответа
        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response content: {response.content}")

        response.raise_for_status()  # Принудительно вызовет исключение для кода состояния HTTP 4xx или 5xx
        return response
    except AssertionError as e:
        logging.error(f"AssertionError: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"RequestException: {e}")
        logging.error(f"Response content: {e.response.content if e.response else 'No response content'}")


