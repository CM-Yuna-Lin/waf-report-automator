from google_api.google_auth import authenticate_services
from google_api.google_sheets import load_and_process_sheet_data
from google_api.google_sheets_merges import fetch_merged_cells
from google_api.google_docs import generate_report
from utils.chart_generate_handler import generate_charts
from utils.display_settings import display_settings

def main():

    # 顯示目前的系統與設定資訊
    display_settings()

    # 驗證 Google API 並取得各服務的對象：
    # - sheets_service: 用於讀取 Google Sheets 數據（透過 gspread）
    # - metadata_service: 用於取得試算表元資料（如合併儲存格範圍）
    # - docs_service: 用於操作 Google Docs 報告
    # - drives_service: 用於上傳圖表圖片到 Google Drive
    sheets_service, metadata_service, docs_service, drives_service = authenticate_services()
    
    # 取得試算表中所有合併儲存格的範圍資訊
    merged_ranges = fetch_merged_cells(metadata_service)
    
    # 讀取問卷數據並處理
    data = load_and_process_sheet_data(sheets_service, merged_ranges)
    
    # 根據數據生成圖表（例如儀表圖與徑向圖），並上傳至 Google Drive
    data = generate_charts(drives_service, data)

    # 根據處理後的數據，生成並更新 Google Docs 報告內容
    generate_report(docs_service, data)

    print(f"\n\033[32m╔═══════════════════════════════════════════════╗\033[0m")
    print(f"\033[32m║ TASK COMPLETED! REPORT PROCESSING SUCCESSFUL! ║\033[0m")
    print(f"\033[32m╚═══════════════════════════════════════════════╝\033[0m\n")

if __name__ == "__main__":
    main()