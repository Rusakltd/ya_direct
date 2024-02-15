# -*- coding: utf-8 -*-
import requests
import os
import pandas as pd
import sys
from requests.exceptions import ConnectionError
from time import sleep
import json
from datetime import date, timedelta
from time import time
from io import StringIO
from dotenv import load_dotenv

load_dotenv()

# chat_id = '-4090186402' ## Мой канал с алёртами
chat_id = '-1002145547826' ## Чат закупка аструма
bot_token = os.getenv("TELEGRAM_API_TOKEN")
token = os.getenv("YANDEX_DIRECT_TOKEN")

url = 'https://api.direct.yandex.ru/live/v4/json/'
ReportsURL = 'https://api.direct.yandex.com/json/v5/reports'

logins_actual = ['lost-ark-mrt', 'perfect-world-mrt', 'arche-age-mrt', 
                 'allodsonline-games', 'atomicheart-game', 'battle-teams2', 
                 'warface2016-2017warfacerwyndxg', 'revival-astrum']


if sys.version_info < (3,):
    def u(x):
        try:
            return x.encode("utf8")
        except UnicodeDecodeError:
            return x
else:
    def u(x):
        if isinstance(x, bytes):
            return x.decode('utf8')
        else:
            return x
        
class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.chat_id = chat_id

    def send_message(self, text):
        url = self.base_url + "sendMessage"
        params = {"chat_id": self.chat_id, "text": text}
        response = requests.post(url, params=params)
        return response.json()

telegram_bot = TelegramBot(bot_token, chat_id)

AgencyClientsBody = {
    "method": "AccountManagement",
    "token": token,
    "param": {
        "Action": "Get",
        "SelectionCriteria": {
         "Logins": logins_actual  
        }
    }
}

response = requests.post(url, json=AgencyClientsBody)

if response.status_code == 200:
    print("Request was successful")
    # print(response.json())
    json_data = response.json()
else:
    print("Request failed with status code:", response.status_code)
    print(response.text)

data_list = [{'Login': account['Login'], 'Amount': round(float(account['Amount']), 2)} for account in json_data['data']['Accounts']]

df = pd.DataFrame(data_list)

headers = {
           "Authorization": "Bearer " + token,
           "Accept-Language": "ru"
           }

AgencyClientsBody = {
    "method": "get",
    "params": {
        "SelectionCriteria": {
            "Archived": "NO"
        },
        "FieldNames": ["Login"],
        "Page": {
            "Limit": 10000,
            "Offset": 0
        }
    }
}

ClientList = logins_actual

body = {
    "params": {
        "SelectionCriteria": {},
        "FieldNames": ["Cost"],
        "ReportName": u("ACCOUNT_PERFORMANCE"),
        "ReportType": "ACCOUNT_PERFORMANCE_REPORT",
        "DateRangeType": "LAST_3_DAYS",
        "Format": "TSV",
        "IncludeVAT": "YES",
        "IncludeDiscount": "NO"
    }
}

resultcsv = "Login,Costs\n"

headers['skipReportHeader'] = "true"
headers['skipColumnHeader'] = "true"
headers['skipReportSummary'] = "true"
headers['returnMoneyInMicros'] = "false"

for Client in ClientList:
    headers['Client-Login'] = Client
    requestBody = json.dumps(body, indent=4)
    while True:
        try:
            req = requests.post(ReportsURL, requestBody, headers=headers)
            req.encoding = 'utf-8'
            if req.status_code == 400:
                print("Параметры запроса указаны неверно или достугнут лимит отчетов в очереди")
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код запроса: {}".format(u(body)))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break
            elif req.status_code == 200:
                print("Отчет для аккаунта {} создан успешно".format(str(Client)))
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                if req.text != "":
                    tempresult = req.text.split('\t')
                    resultcsv += "{},{}\n".format(Client, tempresult[0])
                else:
                    resultcsv += "{},0\n".format(Client)
                break
            elif req.status_code == 201:
                print("Отчет для аккаунта {} успешно поставлен в очередь в режиме offline".format(str(Client)))
                retryIn = int(req.headers.get("retryIn", 60))
                print("Повторная отправка запроса через {} секунд".format(retryIn))
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                sleep(retryIn)
            elif req.status_code == 202:
                print("Отчет формируется в режиме офлайн".format(str(Client)))
                retryIn = int(req.headers.get("retryIn", 60))
                print("Повторная отправка запроса через {} секунд".format(retryIn))
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                sleep(retryIn)
            elif req.status_code == 500:
                print("При формировании отчета произошла ошибка. Пожалуйста, попробуйте повторить запрос позднее.")
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break
            elif req.status_code == 502:
                print("Время формирования отчета превысило серверное ограничение.")
                print(
                    "Пожалуйста, попробуйте изменить параметры запроса - уменьшить период и количество запрашиваемых данных.")
                print("JSON-код запроса: {}".format(body))
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break
            else:
                print("Произошла непредвиденная ошибка")
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код запроса: {}".format(body))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break

        except ConnectionError:
            # print("Произошла ошибка соединения с сервером API")
            break

        except:
            # print("Произошла непредвиденная ошибка")
            break

print("Создание отчетов для аккаунтов завершено")

spend_df = pd.read_csv(StringIO(resultcsv), sep=',', escapechar='\\', 
                       index_col=False)

spend_df = spend_df[(spend_df['Costs']!= 0)]

merged_df = pd.merge(spend_df, df, how='left', on='Login').fillna(0)

merged_df['avg_cost'] = round(merged_df['Costs'] / 3, 2)
merged_df['days'] = pd.to_numeric(merged_df['Amount'] // merged_df['avg_cost'],
                                  downcast='integer')

tg_message = []

for row in merged_df.index:
    if merged_df['days'][row] == 0 and merged_df['Amount'][row] < 5000:
        tg_message.append(f"На аккаунте {merged_df['Login'][row]} закончился бюджет.")
    elif merged_df['days'][row] == 0 and merged_df['Amount'][row] > 5000:
        tg_message.append(f"На аккаунте {merged_df['Login'][row]} бюджета меньше чем на день.")
    elif merged_df['days'][row] == 1:
        tg_message.append(f"{merged_df['Login'][row]} хватит бюджета на {merged_df['days'][row]} день.")
    elif 1 < merged_df['days'][row] < 4:
        tg_message.append(f"{merged_df['Login'][row]} хватит бюджета на {merged_df['days'][row]} дня.")

tg_message = "\n\n".join(tg_message)
if tg_message:
    tg_message = f"Yandex: \n {tg_message}"
    telegram_bot = TelegramBot(bot_token, chat_id)
    telegram_bot.send_message(tg_message)

message_text = "Скрипт Yandex сработал"
chat_id = '126841573'
telegram_bot = TelegramBot(bot_token, chat_id)
telegram_bot.send_message(message_text)