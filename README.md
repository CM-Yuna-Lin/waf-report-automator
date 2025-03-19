# WAF Report Automator

Edit by Yuna Lin 2025/03/12

## Abstract / 專案摘要


本專案是用於生成 WAF 報告的自動化工具，通過 Google Sheets 讀取 GCP Well-Architected Framework Questionnaire 問卷結果，並根據結果數據生成圖表、客戶現況統整與建議改善計畫，最終輸出至 Google Docs 報告中。藉由自動化統整與輸出，此工具期望節省整理 WAF 報告的時間與人力，並優化客戶體驗，讓客戶在 WAF 訪談後的短時間內可以取得初步報告、進行初步審視與規劃。

此工具使用 Google API 來讀取試算表、生成報表、上傳圖片，並透過生成式 AI（Gemini）來優化數據摘要。

### 主要功能

- 從 Google Sheets 擷取並處理問卷資料
- 使用生成式 AI（如 Gemini）處理資料潤飾與統整
- 自動生成各類圖表並上傳至 Google Drive
- 自動填充 Google Docs 報告模板



## Excetion Guide / 執行步驟說明


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
4. 從 GCP console > API & Services > Credentials 下載 OAuth 2.0 Client ID (Application type 需選擇 Desktop app)，重新命名為 `client_secret.json` 放在 credentials 資料夾中（首次執行時，程式會引導進行 Google 帳戶登入授權）

### 執行報表生成

- **SUMMARY**

    <aside>

        1️⃣ 準備三個必要 ID (Spreadsheet, Document, Folder)

        2️⃣ 修改設定檔案 (settings.py)

        3️⃣ 執行專案

        4️⃣ 檢查 Google Doc 內容

    </aside>

1. **準備三個必要 ID**

    <aside>
    
        三個 ID 皆可由網址中取得，位置分別如下：
    
        1️⃣ Spreadsheet ID:
    
            https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit?gid=SHEET_ID#gid=SHEET_ID
    
        2️⃣ Document ID:
    
            https://docs.google.com/document/d/<DOCUMENT_ID>/edit
    
        3️⃣ Folder ID:
    
            https://drive.google.com/drive/u/0/folders/<FOLDER_ID>
    
    </aside>

    - **1️⃣ Google Sheet Questionnaire — Spreadsheet ID**
        
        請與客戶完成問卷後取得試算表 ID，程式將讀取此試算表的問卷填寫情形，以 LLM 進行統整，以利後續將資料寫入文件
        
        - LLM 統整欄位說明
            
            Google Sheet 中以下四個欄位供 LLM 生成使用，若 settings.py 中 `ENABLE_AI_GENERATION` 設為 False，則程式會直接讀取欄位中原有的內容，不額外進行生成
            
            | Google Sheet 欄位名稱 | 欄位內容 | 參照欄位 |
            | --- | --- | --- |
            | Refined Notes | 潤飾 `Client Status Notes` 欄位的內容 | `Client Status Notes`  |
            | Client Conditions | 依據 Question 中各個 Item 的達成情形，統整出客戶對於該 Question 的 WAF 現況 | `Items`, `Checklist`, `Refined Notes`/`Client Status Notes`  |
            | Suggested Improvements | 統整 Question 中各個 Item 尚未達成的 Best Practices，總結出建議改善事項 | `GCP Best Practices`, `GCP Best Practice Content` |
            | Suggestion | 集合整份報告中的建議，依照 STAGE_ORDER 指定的順序進行分類統整，並由 Google Sheets 中 Suggestion 欄位的第 2 行開始往下填寫（STAGE_ORDER 預設順序為短期/中期/長期/其他） | `Topics`, `Suggested Development Stages`, `Client Conditions`, `Suggested Improvements` |

            
        - Topic/Question 略過機制說明
            
            若 Question 中 Checklist 所有選項（含以上皆非）都沒被勾選，該 Question 就會被略過；若 Topic 中的所有 Question 都被略過，則該 Topic 會被略過
            
        
        ⚠️ 為了程式執行需要，Google Sheet 底部需包含 `QUESTIONNAIRE_END_MARKER` 列
        
    - **2️⃣ Google Doc Template — Document ID**
        
        程式將把報告內容寫入此文件檔案，請複製原 Template 檔案後取得新檔案的 ID
        
        ⚠️  在「報告日期」欄位需包含 `REPORT_DATE` 字樣，用於代入報告日期
        
        ⚠️  為了程式執行需要，**文件中需包含 `INSERT_POINT` 字樣**，此字樣用於標記 Google Doc 內的插入點，程式會由此開始寫入報告內容，寫入完畢後字樣將自動刪除
        ```diff
        - 🌟🌟🌟 INSERT_POINT 用途 🌟🌟🌟

          INSERT_POINT 字樣的用途是讓程式知道該從 Google Doc 的何處開始寫入，程式會由 INSERT_POINT 開始寫入報告內容，寫入完畢後字樣將自動刪除

          => 只要有包含 INSERT_POINT 字樣，程式可以將內容寫入任何 Google Doc

          => 對一份已完成的 WAF report 重新執行一遍程式，程式可以接續 INSERT_POINT 的位置繼續寫入，不會移除或覆蓋原本的內容。但目前程式在寫入完畢後為自動將 INSERT_POINT 字樣刪除，故重新執行可能會因為在文件中無法找到 INSERT_POINT 而報錯，手動加入字樣後再執行即可
        ```
        
    - **3️⃣ Google Drive Folder — Folder ID**
        
        圖片暫存需要，報告生成後可刪除，任何資料夾皆可
    
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
        GOOGLE_DOC_ID = "<DOCUMENT_ID>"
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
        STAGE_ORDER = STAGE_ORDER = ["短期", "中期", "長期", "其他"]
        ```

    - (Optional) LLM Prompt 調整
        
        ```python
        # =========================================================================
        # AI 處理 Prompt 設定
        #   - PROMPTS: 各任務對應的系統提示文字，用以引導 LLM 生成內容
        #
        #              [形式] 
        #              {
        #                  "任務名稱_1": "任務提示文字_1",
        #                  "任務名稱_2": "任務提示文字_2",
        #                  "任務名稱_3": "任務提示文字_3"
        #              }
        # 
        #              (若要調整 prompt，請編輯任務提示文字，請勿改動任務名稱)
        # =========================================================================
        PROMPTS = {
            "refine_client_status_notes": "以下是Well-Architected Framework的現況，請協助潤飾成客觀專業且簡潔的紀錄，不要加入額外資訊或建議， 字數在100字以內",
            "summarize_client_conditions": "以下是Well-Architected Framework的現況，請協助統整成客觀專業的紀錄，不要加入額外資訊或建議，字數在100字以內",
            "summarize_improvement_plans": "以下對客戶Well-Architected Framework的所有建議改善事項，請協助統整成專業的建議建議事項，要參考所有提供的資料，包含具體細節，請用中文撰寫，字數在150字以內",
            "extract_question_aspects": "Please extract an aspect of five words or fewer from the question in English, for example: 'COST 1. How do you implement cloud financial management?' can be summarized as 'Financial Management'.",
            "find_relevant_best_practices": "You are an assistant designed to match text with given best practices. Find and return the sections most similar to the following best practice. Return the relevant parts without any extra changes. If no content found, return 'NA'. Here is the webpage:",
            "summarize_suggestion": "以下是客戶Well-Architected Framework各topic的現況與建議，請整理出重點，解釋其為何被劃為「短期/中期/長期」，並強調能這些改善能為客戶帶來的效果與價值，字數在200字以內"
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

## Project Structure / 專案架構


```bash
.
├── README.md                   # 專案說明文件，介紹專案用途與使用方式
├── main.py                     # 主入口程式，負責整合流程（認證、讀取資料、生成圖表與報告）
├── settings.py                 # 全域設定檔，定義 API 金鑰、文件 ID、參數等配置
├── requirements.txt
│
├── credentials/                
│   ├── client_secret.json      # Google API 用戶端金鑰設定檔
│   └── token.pickle            # 存儲 Google API 存取令牌的檔案，在第一次登入授權後自動產生
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

## Additional Information / 其他說明


1. **Best Practice 與 Reference 數量不符相關 WARNING**
    
    由於 Google Sheet Questionnaire 中的 Best Practices 與 Best Practice References 可能存在一對多或多對一的對應關係，若 Best Practice 與 Reference 出現數量不一致的情況，就會以 WARNING 提醒注意超連結正確性
    
    - 例如，Google Sheet 中若出現如下情形，程式會依照順序將 best practice 進行對應：
        
        
        | GCP Best Practices | GCP Best Practices |
        | --- | --- |
        | best practice a<br>best practice b<br>best practice c | link_a<br>link_c_1<br>link_c_2 |
        - 對應結果：
            - best practice a ↔ link_a
            - best practice b ↔ link_c
            - best practice c
        
        解決方法是在 Google Sheet 中以 “NA” 取代缺少的 Best Practice 或 Reference，即可取得正確對應：
        
        | GCP Best Practices | GCP Best Practices |
        | --- | --- |
        | best practice a<br>best practice b<br>best practice c<br>NA | link_a<br>NA<br>link_c_1<br>link_c_2 |
        - 對應結果：
            - best practice a ↔ link_a
            - best practice b
            - best practice c ↔ link_c_1
            - link_c_2

2. **提升報告生成效率**
    
    報告產生的速度主要受限於 LLM 回覆速度與 API 的 quota (60 次/min)，為避免出錯，目前程式設有 sleep 機制，每次發出一般 API 請求後會休息一秒，可由 settings.py 中的 SLEEP 參數進行調整（單位：秒）

    1. 解決 LLM 瓶頸
    
        在特定情況下，若不需要重新生成內容，可將 ENABLE_AI_GENERATION 改為 False，省去 LLM 回覆時間

    2. 解決 API 請求額度瓶頸

        由 GCP console 調高 API 請求額度，便可將 SLEEP 調整為更短的秒數


## Feature Modifications & Expansion Suggestions / 功能修改 & 擴充建議

1. **修改報告文字格式（字體、顏色…）**
    
    程式在寫入報告時參考的是 Google Doc Template 當中的 Paragraph styles，若要更改 Template 文字格式，請在執行程式前利用從 Google Doc Template 中修改 Paragraph styles。
    
    - 例如，若要修改 Heading 1，請直接在 Template doc 中將 Heading 1 調整成想要的格式後從 Format > Paragraph styles > Heading 1 > Update ‘Heading 1’ to match 進行格式更新

2. **批次處理寫入請求，提升報告生成效率**

    報告產生的速度主要受限於 LLM 回覆速度與 API 的 quota (60 次/min)，為避免出錯，目前程式設有 sleep 機制，每次發出一般 API 請求後會休息一秒，可由 settings.py 中的 SLEEP 參數進行調整（單位：秒）。
    
    為清晰顯示資料處理進度，目前許多寫入請求為單項處理，若有需要，後續可整併為批次處理，減少請求次數，便可調降 sleep 機制的時長與觸發次數

2. **修改 DataFrame 結構，提升可讀性**

    google sheets 問卷中的資料經 process_sheet_data() 轉換後，DataFrame 會整理成嵌套的 JSON-like 結構，其層級大致如下：

    ```python
    {
        "total_score": int,   # 總得分
        "total_num": int,     # 總問題數
        "topics": [           # 主題清單
            {
                "topic": str,       # 主題名稱
                "topic_score": int, # 該主題得分
                "topic_num": int,   # 該主題的問題數
                "not_applicable": bool, # 是否適用該主題
                "questions": [      # 問題清單
                    {
                        "score": int,        # 問題得分
                        "num": int,          # 該問題的選項數
                        "client_condition": str,  # 客戶現況
                        "improvement_plan": str,  # 改進計畫
                        "area": str,         # 問題所屬領域
                        "question": str,     # 具體問題
                        "stage": str,        # 建議的發展階段
                        "not_applicable": bool, # 是否適用
                        "items": [           # 選項清單
                            {
                                "check": bool,   # 是否勾選該選項
                                "item": str,     # 選項名稱
                                "note": str,     # 客戶填寫的原始備註
                                "refined_note": str,  # AI 生成的潤飾備註
                                "best_practice": list[str], # 最佳實踐
                                "best_practice_ref": list[str], # 最佳實踐參考連結
                                "best_practice_content": str   # 最佳實踐內容
                            }
                        ]
                    }
                ]
            }
        ],
        "suggestions": list[str] # 改善建議
    }
    ```

    若要提升可讀性，後續可考慮改以 python Class 管理結構，例如：

    ```python
    from typing import List, Optional

    class Item:
        def __init__(self, check: bool, item: str, note: str, refined_note: str, best_practice: List[str], best_practice_ref: List[str], best_practice_content: str):
            self.check = check
            self.item = item
            self.note = note
            self.refined_note = refined_note
            self.best_practice = best_practice
            self.best_practice_ref = best_practice_ref
            self.best_practice_content = best_practice_content

    class Question:
        def __init__(self, question: str, area: str, reco: str, client_condition: str, improvement_plan: str, score: int, num: int, not_applicable: bool, items: List[Item]):
            self.question = question
            self.area = area
            self.reco = reco
            self.client_condition = client_condition
            self.improvement_plan = improvement_plan
            self.score = score
            self.num = num
            self.not_applicable = not_applicable
            self.items = items

    class Topic:
        def __init__(self, topic: str, topic_score: int, topic_num: int, not_applicable: bool, questions: List[Question]):
            self.topic = topic
            self.topic_score = topic_score
            self.topic_num = topic_num
            self.not_applicable = not_applicable
            self.questions = questions

    class ReportData:
        def __init__(self, total_score: int, total_num: int, topics: List[Topic], suggestions: List[str]):
            self.total_score = total_score
            self.total_num = total_num
            self.topics = topics
            self.suggestions = suggestions

    ```