# WAF Report Automator

Edit by Yuna Lin 2025/02/26

## Abstract / 專案摘要

---

本專案是用於生成 WAF 報告的自動化工具，通過 Google Sheets 讀取 GCP Well Architect Questionnaire 問卷結果，並根據結果數據生成圖表、客戶現況統整與建議改善計畫，最終輸出至 Google Docs 報告中。藉由自動化統整與輸出，此工具期望節省整理 WAF 報告的時間與人力，並優化客戶體驗，讓客戶在 WAF 訪談後的短時間內可以取得初步報告、進行初步審視與規劃。

此工具使用 Google API 來讀取試算表、生成報表、上傳圖片，並透過生成式 AI（Gemini）來優化數據摘要。

### 主要功能

- 從 Google Sheets 擷取並處理問卷資料
- 使用生成式 AI（如 Gemini）處理資料潤飾與統整
- 自動生成各類圖表並上傳至 Google Drive
- 自動填充 Google Docs 報告模板

## 專案架構

---

```bash
.
├── README.md                   # 專案說明文件，介紹專案用途與使用方式
├── main.py                     # 主入口程式，負責整合流程（認證、讀取資料、生成圖表與報告）
├── settings.py                 # 全域設定檔，定義 API 金鑰、文件 ID、參數等配置
├── requirements.txt
│
├── credentials/                
│   ├── client_secret.json      # Google API 用戶端金鑰設定檔
│   └── token.pickle            # 存儲 Google API 存取令牌的檔案
│
├── google_api/                 
│   ├── google_auth.py          # Google API 驗證與服務初始化模組
│   ├── google_docs.py          # Google Docs 報告生成相關函式
│   ├── google_sheets.py        # Google Sheets 資料讀取相關函式
│   └── google_sheets_merges.py # 處理試算表合併儲存格狀態的工具
│
├── images/                     # 圖表圖片輸出資料夾
│
└── utils/ 
    ├── best_practice_scraper.py   # 用於抓取最佳實務網站內容（效果不彰暫緩使用）
    ├── chart_generate_handler.py  # 圖表生成處理與圖片上傳 Google Drive 的整合模組
    ├── chart_generator_gauge.py   # 使用 pyecharts 生成儀表圖的模組
    ├── chart_generator_radial.py  # 使用 matplotlib 生成徑向條形圖及圖例合併的模組
    ├── display_settings.py        # 輸出當前配置設定的工具模組
    ├── remove_image_whitespace.py # 圖片裁剪工具，移除圖片多餘的空白邊界
    └── llm_handler.py             # 與 LLM 互動的封裝函式，用於生成或潤飾文字
```

## Steps / 執行步驟說明

---

### 安裝與環境

1. 從 GitHub clone repository
2. 安裝必要套件
    
    ```bash
    pip install -r requirements.txt
    ```
    
3. 確保 Google Cloud Project 已啟用需要的 API
    - Google Sheets API
    - Google Docs API
    - Vertex AI API
    - Gemini for Google Cloud API
    - Google Drive API
4. 從 GCP console > API & Services > Credentials 下載 OAuth 2.0 Client ID，重新命名為 `client_secret.json` 放在 credentials 資料夾中（首次執行時，程式會引導進行 Google 帳戶登入授權）

### 執行報表生成

1. **準備三個必要 ID**
    - **1️⃣ Google Sheet Questionnaire — Spreadsheet ID**
        
        請與客戶完成問卷後取得試算表 ID，程式將讀取此試算表的問卷填寫情形，以 LLM 進行統整，以利後續將資料寫入文件
        
        - LLM 統整欄位說明
            
            若 settings.py 中 `ENABLE_AI_GENERATION` 設為 False，則程式會直接讀取欄位中原有的內容，不額外進行生成
            
            | Google Sheet 欄位名稱 | 欄位內容 | 參照欄位 |
            | --- | --- | --- |
            | Refined Notes | 潤飾 `Client Status Notes` 欄位的內容 | `Client Status Notes`  |
            | Client Conditions | 依據 Question 中各個 Item 的達成情形，統整出客戶對於該 Question 的 WAF 現況 | `Items`, `Checklist`, `Refined Notes`/`Client Status Notes`  |
            | Suggested Improvements | 統整尚未達成的 Best Practices，總結出建議改善事項 | `GCP Best Practices`, `GCP Best Practice Content` |
            
        - Topic/Question 略過機制說明
            
            若 Question 中 Checklist 所有選項（含以上皆非）都沒被勾選，該 Question 就會被略過；若 Topic 中的所有 Question 都被略過，則該 Topic 會被略過
            
        
        ⚠️ 為了程式執行需要，Google Sheet 底部需包含 QUESTIONNAIRE_END_MARKER 列
        
    - **2️⃣ Google Doc Template — Document ID**
        
        程式將把報告內容寫入此文件檔案，請複製原 WAF-Template 檔案後取得其 ID
        
        ⚠️  在「報告日期」欄位需包含 REPORT_DATE 字樣，用於代入報告日期
        
        ⚠️  為了程式執行需要，文件中需包含 DOC_INSERTION_POINT 字樣，此字樣用於標記 Google Doc 內的插入點，程式會由此開始寫入報告內容，寫入完畢後字樣將自動刪除
        
    - **3️⃣ Google Drive Folder — Folder ID**
        
        圖片暫存需要，報告生成後可刪除，任何資料夾皆可
        
    
    <aside>
    
        以上三個 ID 皆可由網址中取得，位置分別如下：
    
        1️⃣ Spreadsheet ID:
    
            https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit?gid=SHEET_ID#gid=SHEET_ID
    
        2️⃣ Document ID:
    
            https://docs.google.com/document/d/<DOCUMENT_ID>/edit
    
        3️⃣ Folder ID:
    
            https://drive.google.com/drive/u/0/folders/<FOLDER_ID>
    
    </aside>
    
2. 依需求修改 settings.py 檔案
    - (Required) 填入 GCP Project ID 與前一個步驟取得的三個 ID
        
        ```python
        # =========================================================================
        # 必須修改的變數
        #   - GOOGLE_PROJECT_ID: Google Cloud 專案 ID
        #   - GOOGLE_SHEET_ID: WAF Google Sheet 問卷 ID
        #   - GOOGLE_DOC_ID: WAF Google Doc 報告 ID
        #   - GOOGLE_DRIVE_FOLDER_ID: Google Drive 資料夾 ID（用於上傳圖片）
        # =========================================================================
        GOOGLE_PROJECT_ID = "YOUR_GCP_PROJECT_ID"
        GOOGLE_SHEET_ID = "<SPREADSHEET_ID>" 
        GOOGLE_DOC_ID = "<DOCUMENT_ID>/"
        GOOGLE_DRIVE_FOLDER_ID = "<FOLDER_ID>"  
        ```
        
    - (Optional) 細節參數調整
        
        ```python
        # =========================================================================
        # 參數設定
        #   - REPORT_DATE: 用於替換 Google Doc 中 {{REPORT_DATE}} 的日期字串，若留空則自動填入當天日期
        #   - ENABLE_AI_GENERATION: 是否使用 Gen AI 生成報告內容，False 時只讀取 Google Sheet 的現有資料
        # =========================================================================
        REPORT_DATE = ""
        ENABLE_AI_GENERATION = True
        ```
        
    - (Optional) LLM Prompt 調整
        
        ```python
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
        ```
        
3. 執行專案
    
    ```bash
    python main.py
    ```
    
    - 受限於讀寫 API 限制 & Gen AI 生成回覆速度，因應每份問卷需處理的項目不同，此步驟耗費時間不一，每個 Topic 約需 5 分鐘
4. 檢查 Google Doc 內容
    1. 重新整理 Google Doc 目錄
    2. 檢查 AI 生成內容是否合宜

---

以下內容增修中...

---

## 其他說明

---

1. Best Practice 與 Reference 數量不符相關 WARNING
    
    由於 Google Sheet Questionnaire 中的 Best Practices 與 Best Practice References 可能存在一對多或多對一的對應關係，若 Best Practice 與 Reference 出現數量不一致的情況，就會以 WARNING 提醒注意超連結正確性
    
    - 例如，Google Sheet 中若出現如下情形，程式會依照順序將 best practice 進行對應：
        
        
        | GCP Best Practices | GCP Best Practices |
        | --- | --- |
        | best practice a
        best practice b
        best practice c | link_a
        link_c_1
        link_c_2 |
        - 對應結果：
            - best practice a ↔ link_a
            - best practice b ↔ link_c
            - best practice c
        
        解決方法是在 Google Sheet 中以 “NA” 取代缺少的 Best Practice 或 Reference，即可取得正確對應：
        
        | GCP Best Practices | GCP Best Practices |
        | --- | --- |
        | best practice a
        best practice b
        best practice c
        NA | link_a
        NA
        link_c_1
        link_c_2 |
        - 對應結果：
            - best practice a ↔ link_a
            - best practice b
            - best practice c ↔ link_c_1
            - link_c_2
2. 提升讀寫效率
    
    目前產生報告的速度主要受限於 API 的 quota (60 次/min)，為避免超過額度，
    
3. 

### 功能修改/擴充建議

1. 如何修改報告文字格式（字體、顏色…）
    
    程式在寫入報告時參考的是 Google Doc Template 當中的 Paragraph styles，若要更改 Template 文字格式，請在執行程式前利用從 Google Doc Template 中修改 Paragraph styles。
    
    - 例如，若要修改 Heading 1，請直接在 Template doc 中將 Heading 1 調整成想要的格式後從 Format > Paragraph styles > Heading 1 > Update ‘Heading 1’ to match 進行格式更新
2. 