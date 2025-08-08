import os
import json
import gspread
from google.oauth2.service_account import Credentials

def get_config(sheet_name):
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON_STRING")
    if not credentials_json:
        raise ValueError("Переменная GOOGLE_CREDENTIALS_JSON_STRING не установлена.")

    credentials_dict = json.loads(credentials_json)
    creds = Credentials.from_service_account_info(credentials_dict)
    gc = gspread.authorize(creds)

    sheet = gc.open(sheet_name).worksheet("config")

    config = {
        "bot_token": sheet.acell("A2").value,
        "admin_id": sheet.acell("B2").value,
        "approve_text": sheet.acell("C2").value,
        "reject_text": sheet.acell("D2").value,
        "mini_course_link": sheet.acell("E2").value,
    }
    return config

