import requests
import json
import csv
from time import sleep
from datetime import datetime, timedelta
from io import StringIO

def refresh_token_ads_vk(refresh_token, client_secret, client_id):
    """
    Refreshes access token
    """
    url = "https://ads.vk.com/api/v2/oauth2/token.json"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_secret": client_secret,
        "client_id": client_id
    }

    response = requests.post(url, headers=headers, data=data)
    token = response.json()['access_token']
    return token


def get_balance_vk_accs(access_token, client_ids):
    """
    Returns balance VK accounts
    client_ids - string with client ids with comma separated
    """
    url = "https://ads.vk.com/api/v2/agency/clients.json"
    headers = {
         "Authorization": f"Bearer {access_token}"
    }

    params = {
        "_user__id__in": client_ids
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()

    balance_list = []
    for item in json_data['items']:
        client_info_dict = {
            'client_name': item['user']['additional_info']['client_name'],
            'balance': item['user']['account']['balance'],
            'id': item['user']['id']
        }
        balance_list.append(client_info_dict)

    return balance_list



def get_spent_vk_client(accaunt_ids, access_token, date_from, date_to):
    """
    Returns stat VK campaigns
    accaunt_ids - string with campaigns ids with comma separated
    """

    url = "https://ads.vk.com/api/v2/statistics/users/day.json"
    headers = {
         "Authorization": f"Bearer {access_token}"
    }
    params = {
        "id": accaunt_ids,
        "date_from": date_from,
        "date_to": date_to,
        "metrics": "base"
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()


def old_vk_get_stat_campaigns(access_token, 
                        account_id, 
                        campaign_ids, 
                        date_from, 
                        date_to):
    """
    Returns stat of campaigns from old VK account
    campaign_ids - string with campaigns ids with comma separated
    """
    url_ads = 'https://api.vk.com/method/ads.getStatistics'
    params = {
    'account_id': account_id,
    'ids_type': 'campaign',
    'ids': campaign_ids,
    'period': 'day',
    'date_from': date_from,
    'date_to': date_to,
    'v': '5.199'
}
    headers = {
    "Authorization": f"Bearer {access_token}"
}
    response = requests.get(url_ads, headers=headers, params=params)
    return response.json()



# Define telegram bot
class TelegramBot:
    def __init__(self, token, chat_id):
        """
        Initializes a new instance of the telegram bot with the provided 
        token and chat ID.

        Parameters:
            token (str): The token for the Telegram bot.
            chat_id (int): The ID of the chat.
        """
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.chat_id = chat_id

    def send_message(self, text):
        url = self.base_url + "sendMessage"
        params = {"chat_id": self.chat_id, "text": text}
        response = requests.post(url, params=params)
        return response.json()
    

## Yandex
class YandexDirect:
    def __init__(self, token):
        """
         Initializes a new instance of the yandex direct exporter 
         with the provided token.

        Parameters:
            token (str): The token for Yandex Direct API.
        """
        self.token = token
        self.url_accounts = 'https://api.direct.yandex.ru/live/v4/json/'
        self.url_reports = 'https://api.direct.yandex.com/json/v5/reports'

# Создание HTTP-заголовков запроса
    def accounts_budget(self, logins):
        """
        Returns accounts budget
        """
        token = self.token
        AgencyClientsBody = {
            "method": "AccountManagement",
            "token": token,
            "param": {
                "Action": "Get",
                "SelectionCriteria": {
                "Logins": logins  
                }
            }
        }
        response = requests.post(self.url_accounts, json=AgencyClientsBody)
    
        if response.status_code == 200:
            print("Request was successful")
            print(response.json())
            json_data = response.json()
            accounts_budget = [{'Login': account['Login'], 
              'Amount': round(float(account['Amount']), 2)} for account in json_data['data']['Accounts']]
            return accounts_budget
        else:
            print("Request failed with status code:", response.status_code)
            print(response.text)

    def get_account_spent(self, logins, date_range="LAST_3_DAYS"):
        """
        Returns accounts spent
        """
        main_url = self.url_reports
        token = self.token
        headers = {
            "Authorization": "Bearer " + token,
            "Accept-Language": "ru",
            'skipReportHeader': "true",
            'skipColumnHeader': "true",
            'skipReportSummary': "true",
            'returnMoneyInMicros': "false"
        }
        body = {
            "params": {
                "SelectionCriteria": {},
                "FieldNames": ["Cost"],
                "ReportName": "ACCOUNT_PERFORMANCE",
                "ReportType": "ACCOUNT_PERFORMANCE_REPORT",
                "DateRangeType": date_range,
                "Format": "TSV",
                "IncludeVAT": "YES",
                "IncludeDiscount": "NO"
            }
        }
        resultcsv = "Login,Costs\n"
        for Client in logins:
            # Добавление HTTP-заголовка "Client-Login"
            headers['Client-Login'] = Client
            # Кодирование тела запроса в JSON
            requestBody = json.dumps(body, indent=4)
            # Запуск цикла для выполнения запросов
            # Если получен HTTP-код 200, то содержание отчета добавляется к результирующим данным
            # Если получен HTTP-код 201 или 202, выполняются повторные запросы
            while True:
                try:
                    req = requests.post(main_url, requestBody, headers=headers)
                    req.encoding = 'utf-8'  # Принудительная обработка ответа в кодировке UTF-8
                    if req.status_code == 400:
                        print("Параметры запроса указаны неверно или достугнут лимит отчетов в очереди")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        print(f"JSON-код запроса: {body}")
                        print(f"JSON-код ответа сервера: \n{req.json()}")
                        break
                    elif req.status_code == 200:
                        print(f"Отчет для аккаунта {str(Client)} создан успешно")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        if req.text != "":
                            tempresult = req.text.split('\t')
                            resultcsv += "{},{}\n".format(Client, tempresult[0])
                        else:
                            resultcsv += "{},0\n".format(Client)
                        break
                    elif req.status_code == 201:
                        print(f"Отчет для аккаунта {str(Client)} успешно поставлен в очередь в режиме offline")
                        retryIn = int(req.headers.get("retryIn", 60))
                        print(f"Повторная отправка запроса через {retryIn} секунд")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        sleep(retryIn)
                    elif req.status_code == 202:
                        print("Отчет формируется в режиме офлайн")
                        retryIn = int(req.headers.get("retryIn", 60))
                        print(f"Повторная отправка запроса через {retryIn} секунд")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        sleep(retryIn)
                    elif req.status_code == 500:
                        print("При формировании отчета произошла ошибка. Пожалуйста, попробуйте повторить запрос позднее.")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        print(f"JSON-код ответа сервера: \n{req.json()}")
                        break
                    elif req.status_code == 502:
                        print("Время формирования отчета превысило серверное ограничение.")
                        print(
                            "Пожалуйста, попробуйте изменить параметры запроса - уменьшить период и количество запрашиваемых данных.")
                        print(f"JSON-код запроса: {body}")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        print(f"JSON-код ответа сервера: \n{req.json()}")
                        break
                    else:
                        print("Произошла непредвиденная ошибка")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        print(f"JSON-код запроса: {body}")
                        print(f"JSON-код ответа сервера: \n{req.json()}")
                        break

                # Обработка ошибки, если не удалось соединиться с сервером API Директа
                except ConnectionError:
                    # В данном случае мы рекомендуем повторить запрос позднее
                    print("Произошла ошибка соединения с сервером API")
                    # Принудительный выход из цикла
                    break

                # Если возникла какая-либо другая ошибка
                except:
                    # В данном случае мы рекомендуем проанилизировать действия приложения
                    print("Произошла непредвиденная ошибка")
                    # Принудительный выход из цикла
                    break
        return resultcsv
    

class YandexMessengerBot:
    def __init__(self, token, chat_id):
        """
        Initializes a new instance of the Yandex bot with the provided 
        token and chat ID.

        Parameters:
            token (str): The token for the Yandex bot.
            chat_id (int): The ID of the chat.
        """
        self.token = token
        self.base_url = "https://botapi.messenger.yandex.net/bot/v1/messages/"
        self.chat_id = chat_id

    def send_text(self, text):
        self.headers = {"Authorization": f"OAuth {self.token}",
                        'Content-Type': 'application/json'}
        url = self.base_url + "sendText/"
        if '/' in self.chat_id:
            data = {"chat_id": self.chat_id,
                    "text": text}
        else:
            data = {"login": self.chat_id,
                    "text": text}
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def getupdate(self, offset=0):
        self.headers = {"Authorization": f"OAuth {self.token}"}
        url = self.base_url + "getUpdates/"
        params = {"offset": offset}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()