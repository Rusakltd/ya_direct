import os
import json

from dotenv import load_dotenv

from datetime import datetime
from dateutil.relativedelta import relativedelta

from api_lib.api_functions import YandexDirect as yd
from api_lib.api_functions import TelegramBot
from api_lib.api_functions import YandexMessengerBot

## Get env variables
load_dotenv()
token = os.getenv("YANDEX_TOKEN")
yam_token = os.getenv("YAM_TOKEN")

## Create dates
### Текущая дата
now = datetime.now()

### Предыдущий месяц
previous_month = now - relativedelta(months=1)

### Форматируем вывод: October-2025
formatted_date = previous_month.strftime("%B-%Y")

## Load accounts from json
# Получаем директорию, где находится скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))
# Путь к logins2.json в той же папке
logins_path = os.path.join(script_dir, 'logins2.json')

with open(logins_path, 'r') as f:
    accounts_tokens = json.load(f)


## Create Yandex messenger bot instances
# chat_id_ya = '0/0/6b2bfa7e-ed2e-4be9-9a12-b753a68a4a3e' # Канал с алёртами в Yandex Messenger
chat_id_ya = 'aleksey.rusakov@astrum.team'
ya_bot = YandexMessengerBot(yam_token, chat_id_ya)


## Yandex Export
### Create Yandex Direct instance
yad = yd(token)

### Get spend
spend =  yad.get_multiple_accounts_spent(accounts_dict=accounts_tokens, date_range="LAST_MONTH")

print(spend)
message = []
message.append(f"**Расход MGCom аккаунтов Yandex Direct за {formatted_date}**\n")

for account in spend:
    message.append(f"{account['login']} – {account['cost']:,.0f}")

print('\n'.join(message))
ya_bot.send_text('\n'.join(message))