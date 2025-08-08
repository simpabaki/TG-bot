import os
import json
import gspread
from google.oauth2.service_account import Credentials

def get_config(sheet_name):
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON_STRING")
    credentials_dict = json.loads(credentials_json)
    creds = Credentials.from_service_account_info(credentials_dict)
    gc = gspread.authorize(creds)

    config_sheet = gc.open(sheet_name).worksheet("config")
    config = {
        "bot_token": config_sheet.acell("A2").value,
        "admin_id": config_sheet.acell("B2").value,
        "approve_text": config_sheet.acell("C2").value,
        "reject_text": config_sheet.acell("D2").value,
        "mini_course_link": config_sheet.acell("E2").value
    }
    return config

def save_user_to_sheet(user_data):
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON_STRING")
    credentials_dict = json.loads(credentials_json)
    creds = Credentials.from_service_account_info(credentials_dict)
    gc = gspread.authorize(creds)
    sheet = gc.open("config").worksheet("users")

    all_user_ids = sheet.col_values(1)
    if str(user_data["user_id"]) in all_user_ids:
        return

    row = [
        str(user_data["user_id"]),
        user_data.get("full_name", ""),
        user_data.get("username", ""),
        user_data.get("phone_number", "")
    ]
    sheet.append_row(row)
