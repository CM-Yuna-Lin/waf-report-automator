import pandas as pd
import time

from settings import *
from utils.llm_handler import llm
from google_api.google_sheets_merges import check_cell_merge_status
# from utils.best_practice_scraper import best_practice_content_scraper

def fetch_sheet_data(service):
    """
    從 Google Sheet 讀取原始資料

    :param service: Google Sheets API 服務對象
    :return: (data, worksheet)，其中 data 為所有記錄的列表，worksheet 為工作表對象
    """
    sheet = service.open_by_key(GOOGLE_SHEET_ID)
    worksheet = sheet.worksheet(GOOGLE_WORKSHEET_NAME)
    data = worksheet.get_all_records()
    return data, worksheet

def clean_sheet_data(data):
    """
    將原始資料轉換為 Pandas DataFrame 並重新命名欄位

    :param data: 從 Google Sheet 取得的原始資料（列表形式）
    :return: 清理後的 DataFrame
    """
    df = pd.DataFrame(data)

    # 重新命名欄位，讓欄位名稱更簡潔一致
    df.rename(columns={
        'Topics': 'topic',
        'Best Practice Areas': 'area',
        'Questions': 'question',
        'Suggested Development Stages': 'stage',
        'Client Conditions': 'client_condition',
        'Suggested Improvements': 'improvement_plan',
        'Checklist': 'check',
        'Items': 'item',
        'Client Status Notes': 'note',
        'Refined Notes': 'refined_note',
        'GCP Best Practices': 'best_practice',
        'GCP Best Practice References': 'best_practice_ref',
        'GCP Best Practice Content': 'best_practice_content',
        'Suggestion': 'suggestion'
    }, inplace=True)

    return df

def process_best_practice(item, bp, bpr):
    """
    將 Best Practice 與其 Reference 分行處理，並在數量不符時補上 "NA"，
    同時輸出警告信息以提示超連結數量可能有誤。

    :param item: 項目名稱，用於警告輸出
    :param bp: 原始 Best Practice 字串（可能多行）
    :param bpr: 原始 Best Practice Reference 字串（可能多行）
    :return: (best_practice, best_practice_ref) 兩個列表
    """
    best_practice = [s for s in bp.split('\n') if s]
    best_practice_ref = [s for s in bpr.split('\n') if s]

    if best_practice_ref and len(best_practice) != len(best_practice_ref):
        print(f"\n  \033[33m[WARNING] 項目「{item}」中，Best Practice 與 Reference 數量不符，請注意超連結正確性。"
              f"-- Best Practice/Reference: {len(best_practice)}/{len(best_practice_ref)}\033[0m")
    
    # 補足列表使兩者長度一致
    length_max = max(len(best_practice), len(best_practice_ref))
    len_bp, len_bpr = len(best_practice), len(best_practice_ref)
    for i in range(length_max):
        if i >= len_bp:
            best_practice.append("NA")
        elif i >= len_bpr:
            best_practice_ref.append("NA")

    return best_practice, best_practice_ref

def summarize_condition_and_improvement(items):
    """
    統整各項目的客戶現況與改善建議，並透過 AI 進行摘要處理

    :param items: 包含各項目資料的列表
    :return: (conditions, improvements) 統整後的客戶現況與改善建議
    """
    if not ENABLE_AI_GENERATION:
        return "", ""

    conditions = ""
    improvements = ""

    for item in items:
        conditions += f"\n{item['item']}:{str(item['check'])}, "
        conditions += item['note'] if item['refined_note'] == "" else item['refined_note']

        if not item['check']:
            if item['best_practice_content'] == "":
                for bp in item['best_practice']:
                    improvements += bp if bp != "NA" else ""
            else:
                improvements += item['best_practice_content']
    
    if conditions:
        conditions = llm("gemini", "summarize_client_conditions", "", conditions)
        
    if improvements:
        improvements = llm("gemini", "summarize_improvement_plans", "", improvements)

    return conditions, improvements

def process_sheet_data(df, worksheet, merges):
    """
    根據 DataFrame 中的資料，依主題與問題進行分類、計分與資料統整，
    並利用 Google Sheet API 更新相關欄位。

    :param df: 清理後的 DataFrame
    :param worksheet: Google Sheet 工作表對象
    :param merges: 合併儲存格範圍列表
    :return: 處理後的資料字典
    """
    data = {
        'total_score': 0,
        'total_num': 0,
        'topics': []
    }

    num_topic, is_new_topic = -1, True 
    num_area, current_area = -1, ""
    num_question, idx_question, idx_question_prev = -1, 0, 0

    temp_score, temp_num = 0, 0

    suggestion_collection = []

    for idx, row in df.iterrows():
        # 若項目為空則略過
        if row['item'] == "":
            continue

        # 遇到新主題時更新主題資料
        if row['topic'] != "":
            if num_topic != -1:
                # 判斷該主題下所有問題是否皆標記為不適用
                topic_not_applicable = all(q['not_applicable'] for q in data['topics'][num_topic]['questions'])
                data['topics'][num_topic]['not_applicable'] = topic_not_applicable

            is_new_topic = True
            num_topic += 1
            data['topics'].append({
                'topic': row['topic'],
                'topic_score': 0,
                'topic_num': 0,
                'questions': [],
                'not_applicable': False
            })
        
        # 更新當前區域資訊
        if row['area'] != "":
            if is_new_topic:
                num_area = -1
            current_area = row['area']
            num_area += 1

        # 當遇到新問題時，先更新上一問題的分數及統整資訊
        if row['question'] != "":
            idx_question_prev = idx_question
            idx_question = idx
            if idx != 0:
                nt, nq = num_topic, num_question
                if is_new_topic:
                    nt -= 1
                    nq = len(data['topics'][nt]['questions']) - 1
                    num_question = -1

                data['topics'][nt]['questions'][nq]['score'] = temp_score
                data['topics'][nt]['questions'][nq]['num'] = temp_num

                if not data['topics'][nt]['questions'][nq]['not_applicable']:
                    data['topics'][nt]['topic_score'] += temp_score
                    data['topics'][nt]['topic_num'] += temp_num
                    data['total_num'] += temp_num
                    data['total_score'] += temp_score

                temp_score, temp_num = 0, 0

                # 統整客戶現況與改善建議
                nt, nq = num_topic, num_question
                if is_new_topic:
                    nt -= 1
                    nq = len(data['topics'][nt]['questions']) - 1
                
                if not data['topics'][nt]['questions'][nq]['not_applicable']:
                    client_condition, improvement_plan = summarize_condition_and_improvement(
                        data['topics'][nt]['questions'][nq]['items']
                    )
                    if not client_condition:
                        client_condition = data['topics'][nt]['questions'][nq]['client_condition']
                    if not improvement_plan:
                        improvement_plan = data['topics'][nt]['questions'][nq]['improvement_plan']
                    
                    worksheet.update_cell(idx_question_prev + 2, df.columns.get_loc('client_condition') + 1, client_condition)
                    time.sleep(SLEEP)
                    worksheet.update_cell(idx_question_prev + 2, df.columns.get_loc('improvement_plan') + 1, improvement_plan)
                    time.sleep(SLEEP)
                    data['topics'][nt]['questions'][nq]['client_condition'] = client_condition
                    data['topics'][nt]['questions'][nq]['improvement_plan'] = improvement_plan
                    suggestion_collection.append({
                        'topic': data['topics'][nt]['topic'],
                        'client_condition': client_condition,
                        'improvement_plan': improvement_plan,
                    })
                
                # else:
                #     worksheet.update_cell(idx_question_prev + 2, df.columns.get_loc('improvement_plan') + 1, "SKIPPED")
                #     time.sleep(SLEEP)

                print(f"\n  ❏ Topic 「{data['topics'][nt]['topic']}」 問題 {nq + 1} 讀取完成")

            # 新增該問題的初始資料
            data['topics'][num_topic]['questions'].append({
                'score': 0,
                'num': 0,
                'client_condition': row['client_condition'],
                'improvement_plan': row['improvement_plan'],
                'area': current_area,
                'question': row['question'],
                'stage': row['stage'],
                'items': [],
                'not_applicable': False
            })
            num_question += 1

        # 判斷該項目的狀態
        check = True if row['check'] == 'TRUE' else False

        # 若項目為 "以上皆非"，且未勾選且暫時分數為 0，則標記此問題不適用
        if row['item'] == "以上皆非":
            if (not check) and (temp_score == 0):
                data['topics'][num_topic]['questions'][num_question]['not_applicable'] = True
            continue

        # 處理 Best Practice 與其 Reference
        bp, bpr = row['best_practice'], row['best_practice_ref']
        if row['best_practice'] == "":
            # 若本行資料為空，嘗試從合併儲存格取得資料
            row_idx_bp = check_cell_merge_status(idx + 1, df.columns.get_loc('best_practice'), merges) - 1
            if row_idx_bp != -1:
                bp = df.iloc[row_idx_bp, df.columns.get_loc('best_practice')]
                bpr = df.iloc[row_idx_bp, df.columns.get_loc('best_practice_ref')]
        
        best_practice, best_practice_ref = process_best_practice(row['item'], bp, bpr)

        # 處理客戶現況備註，並在啟用 AI 生成時進行修正
        refined_note = row['refined_note']
        if ENABLE_AI_GENERATION:
            refined_note = llm("gemini", "refine_client_status_notes", row['item'], row['note'])
            worksheet.update_cell(idx + 2, df.columns.get_loc('refined_note') + 1, refined_note)
            time.sleep(SLEEP)
        refined_note = refined_note.replace("\n", "")

        best_practice_content = row['best_practice_content'] if row['best_practice_content'] else ""

        # if row['best_practice'] != "":
        #     best_practice_content = row['best_practice_content'] if row['best_practice_content'] else best_practice_content_scraper(best_practice_ref, best_practice)
        #     worksheet.update_cell(idx + 2, df.columns.get_loc('best_practice_content') + 1, best_practice_content)
        #     time.sleep(SLEEP)
        
        data['topics'][num_topic]['questions'][num_question]['items'].append({
            'check': check,
            'item': row['item'],
            'note': row['note'],
            'refined_note': refined_note,
            'best_practice': best_practice,
            'best_practice_ref': best_practice_ref,
            'best_practice_content': best_practice_content
        })
        best_practice, best_practice_ref = "", ""
        
        if check:
            temp_score += 1

        temp_num += 1
        is_new_topic = False

    suggestion = df.iloc[0, df.columns.get_loc('suggestion')]
    if ENABLE_AI_GENERATION and suggestion_collection:
        suggestion = llm("gemini", "summarize_suggestion", "", str(suggestion_collection))
    data['suggestion'] = suggestion
    worksheet.update_cell(2, df.columns.get_loc('suggestion') + 1, suggestion)
    time.sleep(SLEEP)


    return data

def load_and_process_sheet_data(service, merges):
    """
    讀取並處理 Google Sheet 資料

    :param service: Google Sheets API 服務對象
    :param merges: 合併儲存格範圍列表
    :return: 處理後的數據字典
    """
    print("\n╔══════════════════════ GOOGLE SHEET 資料讀取進行中 ═══════════════════════╗")
    data, worksheet = fetch_sheet_data(service)
    df = clean_sheet_data(data)
    data = process_sheet_data(df, worksheet, merges)
    print("\n╚══════════════════════ GOOGLE SHEET 資料讀取已完成 ═══════════════════════╝")
    return data