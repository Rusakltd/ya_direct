import os
import json

from io import StringIO
from dotenv import load_dotenv
from pathlib import Path

import pandas as pd

from api_lib.api_functions import YandexDirect
from api_lib.api_functions import TelegramBot
from api_lib.api_functions import YandexMessengerBot

## Get env variables
load_dotenv()
bot_token = os.getenv("TELEGRAM_API_TOKEN")
token = os.getenv("YANDEX_TOKEN")
yam_token = os.getenv("YAM_TOKEN")

## Create Yandex messenger bot instances
chat_id_ya = '0/0/6b2bfa7e-ed2e-4be9-9a12-b753a68a4a3e'
ya_bot = YandexMessengerBot(yam_token, chat_id_ya)


url = 'https://api.direct.yandex.ru/live/v4/json/'
ReportsURL = 'https://api.direct.yandex.com/json/v5/reports'
       
## Yandex Export

### Create Yandex Direct instance
yandex = YandexDirect(token)

### Load accounts from json
with Path('logins.json').open('r', encoding='utf-8') as f:
    logins_actual = json.load(f)

### Create dataframe with accounts budgets
df = pd.DataFrame(yandex.accounts_budget(logins_actual))

### Create dataframe with accounts spent
budget_dict = yandex.get_account_spent(logins_actual)

### Create dataframe frome temporary dictionary
budget_dict = pd.read_csv(StringIO(budget_dict), sep=',', escapechar='\\', index_col=False)

### Filter accounts by spent for three days
budget_dict = budget_dict[(budget_dict['Costs']!= 0)]
merged_df = pd.merge(budget_dict, df, how='left', on='Login').fillna(0)

### Create column with average cost
merged_df['avg_cost'] = round(merged_df['Costs'] / 3, 2)

### Create column with days
merged_df['days'] = pd.to_numeric(merged_df['Amount'] // merged_df['avg_cost'], downcast='integer')

## Create message
message = []

### Add info to message for each account
for row in merged_df.index:
    if merged_df['days'][row] == 0 and merged_df['Amount'][row] < 5000:
        message.append(f"На аккаунте {merged_df['Login'][row]} закончился бюджет.")
    elif merged_df['days'][row] == 0 and merged_df['Amount'][row] > 5000:
        message.append(f"На аккаунте {merged_df['Login'][row]} бюджета меньше чем на день.")
    elif merged_df['days'][row] == 1:
        message.append(f"{merged_df['Login'][row]} хватит бюджета на {merged_df['days'][row]} день.")
    elif 1 < merged_df['days'][row] < 4:
        message.append(f"{merged_df['Login'][row]} хватит бюджета на {merged_df['days'][row]} дня.")

### Merge message from list to string
message = "\n\n".join(message)

## Send message
if message:
    message = f"Бюджеты в Yandex:\n {message}"
    ya_bot.send_text(message)

## Send Alert to Telegram
chat_id = '126841573'
telegram_bot = TelegramBot(bot_token, chat_id)
message_test = f"Yandex скрипт отработал"
telegram_bot.send_message(message_test)