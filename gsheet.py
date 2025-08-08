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

def update_user_status(sheet_name: str, telegram_id: int, new_status: str) -> bool:
    """
    Ищет ПОСЛЕДНЮЮ запись с этим telegram_id в листе 'users'
    и обновляет колонку 'status' на new_status. Возвращает True/False.
    """
    gc = get_gsheet_client()
    ws = gc.open(sheet_name).worksheet('users')

    header = ws.row_values(1)

    # Колонка ID — сначала пробуем 'telegram_id', потом 'user_id', иначе 1-я
    try:
        id_col = header.index('telegram_id') + 1
    except ValueError:
        try:
            id_col = header.index('user_id') + 1
        except ValueError:
            id_col = 1

    # Колонка статуса — ищем 'status', иначе по умолчанию 5-я
    try:
        status_col = header.index('status') + 1
    except ValueError:
        status_col = 5

    # Ищем ПОСЛЕДНЮЮ строку с этим ID
    col_vals = ws.col_values(id_col)
    target_row = None
    for i, v in enumerate(col_vals, start=1):
        if str(v).strip() == str(telegram_id):
            target_row = i

    if not target_row:
        return False

    ws.update_cell(target_row, status_col, new_status)
    return True
