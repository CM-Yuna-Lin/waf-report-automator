from settings import *

def display_settings():
    # 準備要顯示的設定資訊
    config_lines = [
        f"REPORT_DATE: {REPORT_DATE if REPORT_DATE else 'auto-filled'}",
        f"GOOGLE_SHEET_ID: {GOOGLE_SHEET_ID}",
        f"GOOGLE_DOC_ID: {GOOGLE_DOC_ID}",
        "GenAI is Currently Enabled" if ENABLE_AI_GENERATION else "GenAI is Currently Disabled",
        f"STAGE_ORDER: {STAGE_ORDER}"
    ]

    # 定義邊框樣式與寬度（header 的長度即為整體寬度）
    header = "╔════════════════════════ CONFIGURATION INFORMATION ════════════════════════╗"
    footer = "╚═══════════════════════════════════════════════════════════════════════════╝"
    total_width = len(header) - 2  # 邊框左右各佔一個字元
    empty_line = "║" + " " * total_width + "║"

    # 輸出設定資訊區塊
    print("\n\033[34m" + header)
    print(empty_line)
    
    for line in config_lines:
        # 在每行前加上提示符號，並置中顯示
        content = f" ❏ {line}"
        print("║" + content + " " * (total_width - len(content)) + "║")
        print(empty_line)
    
    print(f"{footer}\033[0m")