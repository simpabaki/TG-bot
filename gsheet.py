import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
import json

def get_gsheet_client():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds_dict = json.loads(os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON'])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def get_config(sheet_name):
    gc = get_gsheet_client()
    sheet = gc.open(sheet_name).worksheet('config')
    config_data = sheet.get_all_records()
    return {row['key']: row['value'] for row in config_data}

def save_user_data(sheet_name, user_id, username, full_name, phone, status):
    gc = get_gsheet_client()
    sheet = gc.open(sheet_name).worksheet('users')
    sheet.append_row([user_id, username, full_name, phone, status, datetime.datetime.now().isoformat()])
def update_user_status(sheet_name, telegram_id, new_status):
    gc = get_gsheet_client()
    sheet = gc.open(sheet_name).worksheet('users')
    records = sheet.get_all_records()

    for idx, row in enumerate(records, start=2):  # с учётом заголовков, начинаем с 2
        if str(row['telegram_id']) == str(telegram_id):
            sheet.update_cell(idx, 5, new_status)  # 5-я колонка — статус
            break
