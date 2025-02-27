
# =========================================================================
# 必須修改的變數
#   - GOOGLE_PROJECT_ID: Google Cloud 專案 ID
#   - GOOGLE_SHEET_ID: WAF Google Sheet 問卷 ID
#   - GOOGLE_DOC_ID: WAF Google Doc 報告 ID
#   - GOOGLE_DRIVE_FOLDER_ID: Google Drive 資料夾 ID（用於上傳圖片）
# =========================================================================
GOOGLE_PROJECT_ID = "YOUR_PROJECT_ID"
GOOGLE_SHEET_ID = "YOUR_SHEET_ID" 
GOOGLE_DOC_ID = "YOUR_DOC_ID"
GOOGLE_DRIVE_FOLDER_ID = "YOUR_FOLDER_ID"  

# =========================================================================
# 參數設定
#   - REPORT_DATE: 用於替換 Google Doc 中 {{REPORT_DATE}} 的日期字串，若留空則自動填入當天日期
#   - ENABLE_AI_GENERATION: 是否使用 Gen AI 生成報告內容，False 時只讀取 Google Sheet 的現有資料
# =========================================================================
REPORT_DATE = ""
ENABLE_AI_GENERATION = True

# =========================================================================
# AI 處理 Prompt 設定
#   - PROMPTS: 各任務對應的系統提示文字，用以引導 LLM 生成內容
# =========================================================================
PROMPTS = {
    "refine_client_status_notes": "以下是Well Architect Framework的現況，請協助潤飾成客觀專業且簡潔的紀錄，不要加入額外資訊或建議， 字數在100字以內",
    "summarize_client_conditions": "以下是Well Architect Framework的現況，請協助統整成客觀專業的紀錄，不要加入額外資訊或建議，字數在100字以內",
    "summarize_improvement_plans": "以下對客戶Well Architect Framework的所有建議改善事項，請協助統整成專業的建議建議事項，要參考所有提供的資料，包含具體細節，請用中文撰寫，字數在150字以內",
    "extract_question_aspects": "Please extract an aspect of five words or fewer from the question in English, for example: 'COST 1. How do you implement cloud financial management?' can be summarized as 'Financial Management'.",
    "find_relevant_best_practices": "You are an assistant designed to match text with given best practices. Find and return the sections most similar to the following best practice. Return the relevant parts without any extra changes. If no content found, return 'NA'. Here is the webpage:",
}

# ========================================================================
# Google API 相關設定
#   - GOOGLE_LOCATION: 根據實際區域設定（例如 "asia-east1"）
#   - SLEEP: 一般 API 請求的延遲時間（秒）
#   - SLEEP_IMAGE_PROCESSING: 圖片處理的額外延遲時間（秒）
#   - GOOGLE_WORKSHEET_NAME: 問卷工作表名稱
#   - QUESTIONNAIRE_END_MARKER: 問卷結尾標記字串，系統遇到此標記時停止讀取資料
#   - DOC_INSERTION_POINT: Google Doc 插入點標記，寫入後會自動刪除
#   - GOOGLE_SCOPES: Google API 權限設定
#   - TOKEN_DIR: 存放憑證的資料夾路徑
#   - GOOGLE_CLIENT_SECRET_FILE: OAuth 2.0 客戶端密鑰檔案路徑
#   - GOOGLE_TOKEN_PICKLE: 已驗證憑證儲存檔案路徑
# ========================================================================
GOOGLE_LOCATION = "asia-east1"

SLEEP = 1
SLEEP_IMAGE_PROCESSING = 5

GOOGLE_WORKSHEET_NAME = "Questionnaire"
QUESTIONNAIRE_END_MARKER = "QUESTIONNAIRE_END_MARKER"
DOC_INSERTION_POINT = "DOC_INSERTION_POINT"

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file"
]

TOKEN_DIR = "credentials/"
GOOGLE_CLIENT_SECRET_FILE = TOKEN_DIR + "client_secret.json"
GOOGLE_TOKEN_PICKLE = TOKEN_DIR + "token.pickle"

# ========================================================================
# AI 相關設定
#   - LLM_NAME: 使用的 LLM 名稱，目前僅支援 "gemini"
#   - GEMINI_MODEL_NAME: Gemini 模型名稱
# ========================================================================

LLM_NAME = "gemini" # 目前只有使用 gemini 的版本
GEMINI_MODEL_NAME = "gemini-1.5-flash-002"