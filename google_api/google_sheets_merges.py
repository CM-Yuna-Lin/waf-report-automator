from googleapiclient.discovery import build
from settings import GOOGLE_SHEET_ID

def fetch_merged_cells(service) -> list:
    """
    取得試算表的合併儲存格範圍

    :param service: Google Sheets API 服務對象
    :return: 合併儲存格範圍的列表；若無合併範圍則回傳空列表
    """
    request = service.spreadsheets().get(
        spreadsheetId=GOOGLE_SHEET_ID,
        fields="sheets(merges)"
    )
    response = request.execute()
    sheets_data = response.get('sheets', [])

    if not sheets_data:
        print("No sheets found or no merges in the sheet.")
        return []
    
    # 回傳第一個工作表的合併儲存格範圍（若無則為空列表）
    return sheets_data[0].get('merges', [])

def check_cell_merge_status(row: int, column: int, merges: list) -> int:
    """
    檢查指定的儲存格 (row, column) 是否屬於任何合併儲存格範圍，
    若是則回傳該合併區塊的起始列索引，否則回傳 -1。

    :param row: 儲存格所在的列索引（從 0 開始）
    :param column: 儲存格所在的行索引（從 0 開始）
    :param merges: 合併儲存格範圍的列表
    :return: 合併範圍的起始列索引，若該儲存格未屬於任何合併範圍則回傳 -1
    """
    if not merges:
        return -1

    for merge in merges:
        if (merge['startRowIndex'] <= row < merge['endRowIndex'] and
            merge['startColumnIndex'] <= column < merge['endColumnIndex']):
            return merge['startRowIndex']
    
    return -1