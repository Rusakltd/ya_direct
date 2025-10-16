import os
import json

from dotenv import load_dotenv

from api_lib.api_functions import YandexDirect as yd
from api_lib.api_functions import TelegramBot
from api_lib.api_functions import YandexMessengerBot

## Get env variables
load_dotenv()
bot_token = os.getenv("TELEGRAM_API_TOKEN")
token = os.getenv("YANDEX_TOKEN")
yam_token = os.getenv("YAM_TOKEN")

## Load accounts from json
# Получаем директорию, где находится скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))
# Путь к logins2.json в той же папке
logins_path = os.path.join(script_dir, 'logins2.json')

with open(logins_path, 'r') as f:
    accounts_tokens = json.load(f)


## Create Yandex messenger bot instances
chat_id_ya = '0/0/6b2bfa7e-ed2e-4be9-9a12-b753a68a4a3e' # Канал с алёртами в Yandex Messenger
# chat_id_ya = 'aleksey.rusakov@astrum.team'
ya_bot = YandexMessengerBot(yam_token, chat_id_ya)


## Yandex Export
### Create Yandex Direct instance
yad = yd(token)

### Get balances
balances =  yad.get_multiple_accounts_balances(accounts_dict=accounts_tokens)

message = []
message.append(f"**Баланс MGCom аккаунтов Yandex Direct**\n")

for account in balances:
    message.append(f"{account['login']} – {account['amount']:,.0f}")

print('\n'.join(message))
ya_bot.send_text('\n'.join(message))