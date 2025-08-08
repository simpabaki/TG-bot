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

def update_user_status(sheet_name: str, user_id: int, new_status: str) -> bool:
    """
    Ищет строку пользователя по user_id в листе 'users' и обновляет колонку 'status'.
    Возвращает True, если получилось, иначе False.
    """
    gc = get_gsheet_client()
    ws = gc.open(sheet_name).worksheet('users')

    # Находим индексы колонок по заголовкам
    header = ws.row_values(1)
    try:
        user_id_col = header.index('user_id') + 1
        status_col = header.index('status') + 1
    except ValueError:
        # Фоллбек: если заголовков нет/другие имена — используем стандартный порядок
        # user_id, username, full_name, phone, status, timestamp
        user_id_col = 1
        status_col = 5

    # Ищем строку по user_id в соответствующей колонке
    col_values = ws.col_values(user_id_col)
    target_row = None
    for idx, val in enumerate(col_values, start=1):
        if str(val).strip() == str(user_id):
            target_row = idx
            break

    if not target_row:
        return False

    ws.update_cell(target_row, status_col, new_status)
    return True
