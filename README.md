# WAF report generator doc

# Google WAF 報告生成工具

Edit by Yuna Lin 2025/02/13

## Abstract / 摘要

---

本專案是用於生成 WAF 報告的自動化工具，通過 Google Sheets 讀取 GCP Well Architect Questionnaire 問卷結果，並根據結果數據生成圖表、客戶現況統整與建議改善計畫，最終輸出至 Google Docs 報告中。

此工具使用 Google API 來讀取試算表、生成報表、上傳圖片，並透過生成式 AI（Gemini）來優化數據摘要。

### 功能介紹

- Google Sheets 整合 - 讀取試算表數據，解析內容
- 圖表自動生成 - 創建儀表圖（Gauge Chart）和輻射圖（Radial Chart）
- AI 賦能 - 透過 Gemini LLM 生成數據摘要
- Google Docs 報表輸出 - 自動填寫報告，包含數據圖表與分析

## Steps / 步驟說明

---

### 環境與安裝

1. 安裝必要套件
    
    請確保你的環境已安裝 Python（推薦 Python 3.8+），並安裝必要的套件：
    
    ```bash
    pip install -r requirements.txt
    ```
    
2. 確保 Google Cloud Project 已啟用需要的 API
    - Google Sheets API
    - Google Docs API
    - Vertex AI API
    - Gemini for Google Cloud API
    - Google Drive API
3. 下載 OAuth 2.0 認證文件（`client_secret.json`）放在 credentials 資料夾中，並在首次執行程式跳出授權頁面時，登入 Google 帳戶進行授權

### 執行報表生成

1. **準備三個必要 ID**
    - **(1) Google Sheet Questionnaire — Spreadsheet ID**
        
        請與客戶完成問卷後取得試算表 ID，程式將讀取此試算表的問卷填寫情形，以 LLM 進行統整，以利後續將資料寫入文件
        
        - LLM 統整欄位說明
            
            若 [settings.py](http://settings.py) 中 `ENABLE_AI_GENERATION` 設為 False，則程式會直接讀取欄位中原有的內容，不額外進行生成
            
            | Google Sheet 欄位名稱 | 欄位內容 | 參照欄位 |
            | --- | --- | --- |
            | Refined Notes | 潤飾 ‘Client Status Notes’ 欄位的內容 | `Client Status Notes`  |
            | Client Conditions | 依據 Question 中各個 Item 的達成情形，統整出客戶對於該 Question 的 WAF 現況 | `Items`, `Checklist`, `Refined Notes`/`Client Status Notes`  |
            | Suggested Improvements | 統整尚未達成的 Best Practices，總結出建議改善事項 | `GCP Best Practices`, `GCP Best Practice Content` |
            
        - Topic/Question 略過機制說明
            
            若 Question 中 Checklist 所有選項（含以上皆非）都沒被勾選，該 Question 就會被略過；若 Topic 中的所有 Question 都被略過，則該 Topic 會被略過
            
        
        ⚠️ 為了程式執行需要，Google Sheet 底部需包含 QUESTIONNAIRE_END_MARKER 列
        
    - **(2) Google Doc Template — Document ID**
        
        程式將把報告內容寫入此文件檔案，請複製原 WAF-Template 檔案後取得其 ID
        
        ⚠️  在「報告日期」欄位需包含 REPORT_DATE 字樣，用於代入報告日期
        
        ⚠️  為了程式執行需要，文件中需包含 DOC_INSERTION_POINT 字樣，此字樣用於標記 Google Doc 內的插入點，程式會由此開始寫入報告內容，寫入完畢後字樣將自動刪除
        
    - **(3) Google Drive Folder ID**
        
        圖片暫存需要，報告生成後可刪除，任何資料夾皆可
        
    
    <aside>
    📎
    
    以上三個 ID 皆可由網址中取得，位置分別如下：
    
    **(1) Spreadsheet ID:**
    
    https://docs.google.com/spreadsheets/d/**SPREADSHEET_ID**/edit?gid=SHEET_ID#gid=SHEET_ID
    
    **(2) Document ID:**
    
    https://docs.google.com/document/d/**DOCUMENT_ID**/edit
    
    **(3) Folder ID:** 
    
    https://drive.google.com/drive/u/0/folders/**FOLDER_ID**
    
    </aside>
    
2. 依需求修改 settings.py 檔案
    - (Required) 填入 GCP Project ID 與前一個步驟取得的三個 ID
        
        ```python
        # ========================
        # 變數設定（必須修改）
        # ========================
        
        GOOGLE_PROJECT_ID = "YOUR_GCP_PROJECT_ID"
        GOOGLE_SHEET_ID = "YOUR_SPREADSHEET_ID" 
        GOOGLE_DOC_ID = "YOUR_DOCUMENT_ID"
        GOOGLE_DRIVE_FOLDER_ID = "YOUR_FOLDERID"  
        ```
        
    - (Optional) 細節參數調整
        
        ```python
        # ========================
        # 參數設定
        # ========================
        
        # 文件日期設定（用於 Google Doc {{REPORT_DATE}} 佔位符）
        REPORT_DATE = ""  # 若留空，則自動填入當天日期
        
        # AI 使用設定，若設為 False，則只讀取 Google Sheet 既有內容，不進行 AI 生成
        ENABLE_AI_GENERATION = True
        ```
        
    - (Optional) LLM Prompt 調整
        
        ```python
        # ========================
        # AI 處理 Prompt 設定
        # ========================
        
        # 記錄任務名稱，以及進行該任務時對 LLM 下達的 system prompt
        # 修改 system prompt 時請勿更動任務名稱
        PROMPTS = {
            "rephrase_reply": "以下是Well Architect Framework的現況，請協助潤飾成客觀專業且簡潔的紀錄，不要加入額外資訊或建議， 字數在100字以內",
            "summarize_client_condition": "以下是Well Architect Framework的現況，請協助統整成客觀專業的紀錄，不要加入額外資訊或建議，字數在100字以內",
            "summarize_improvement_plan": "以下對客戶Well Architect Framework的所有建議改善事項，請協助統整成專業的建議建議事項，要參考所有提供的資料，包含具體細節，請用中文撰寫，字數在150字以內",
            "summarize_category_title": "Please extract a topic of five words or fewer from the question in English, for example: 'COST 1. How do you implement cloud financial management?' can be summarized as 'Financial Management'.",
            "match_text_with_web": "You are an assistant designed to match text with given best practices. Find and return the sections most similar to the following best practice. Return the relevant parts without any extra changes. If no content found, return 'NA'. Here is the webpage:",
        }
        ```
        
3. 執行專案
    
    ```bash
    python main.py
    ```
    
    - 受限於讀寫 API 限制 & Gen AI 生成回覆速度，此步驟耗費時間不一，每個 Topic 約需 5 分鐘
4. 檢查 Google Doc 內容
    1. 重新整理 Google Doc 目錄
    2. 檢查 AI 生成內容是否合宜

## 其他設定與常見問題 / Additional Notes

---

- 如何修改報告文字格式（字體、顏色…）
    
    程式在寫入報告時參考的是 Google Doc Template 當中的 Paragraph styles，若要更改 Template 文字格式，請在執行程式前利用從 Google Doc Template 中修改 Prargraph styles。
    
    - 例如，若要修改 Heading 1，請將 Heading 1 調整成想要的格式後從 Format > Paragraph styles > Heading 1 > Update ‘Heading 1’ to match 進行格式更新
- Best Practice 與 Reference 數量不符相關 WARNING
    
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

## Summary / 總結

---

本專案為 WAF 報告生成工具，能夠讀取 Google Sheets 問卷數據、使用 AI 生成數據摘要，並將結果輸出至 Google Docs 報告。其使用方式為：

1. 準備三個必要 ID
2. 修改 settings 檔案
3. 執行
4. 檢察報告內容

本工具適用於企業架構評估與最佳實踐分析，提升報告生成的自動化與專業度。