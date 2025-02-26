import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import gspread
from googleapiclient.discovery import build
from settings import *

def authenticate_services():
    """
    通用的 Google API 驗證邏輯：
      - 嘗試從檔案載入憑證；如果不存在或無效，則透過 OAuth 流程進行授權，
        並將新的憑證保存至檔案中。
      - 初始化並回傳以下服務對象：
          • sheets_service: 透過 gspread 操作 Google Sheets
          • sheets_service_for_merged_range: 用於取得合併儲存格範圍的 Sheets API (v4)
          • docs_service: 用於操作 Google Docs 的 API (v1)
          • drives_service: 用於上傳檔案至 Google Drive 的 API (v3)
    """
    creds = None

    # 嘗試從檔案中載入已存在的憑證
    if os.path.exists(GOOGLE_TOKEN_PICKLE):
        with open(GOOGLE_TOKEN_PICKLE, "rb") as token_file:
            creds = pickle.load(token_file)

    # 如果憑證不存在或無效，則進行重新授權
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CLIENT_SECRET_FILE, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        # 保存新的憑證到檔案中
        with open(GOOGLE_TOKEN_PICKLE, "wb") as token_file:
            pickle.dump(creds, token_file)

    # 初始化各 Google API 服務
    sheets_service = gspread.authorize(creds)
    sheets_service_for_merged_range = build('sheets', 'v4', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    drives_service = build('drive', 'v3', credentials=creds)

    return sheets_service, sheets_service_for_merged_range, docs_service, drives_service