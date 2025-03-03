import time
from settings import *

def update_doc(service, requests: list) -> list:
    """
    發送批次更新請求到 Google Docs 並清空請求列表。

    :param service: Google Docs API 服務對象
    :param requests: 請求列表
    :return: 清空後的請求列表
    """
    if requests:
        service.documents().batchUpdate(documentId=GOOGLE_DOC_ID, body={"requests": requests}).execute()
        time.sleep(SLEEP)
    return []

def get_content_start(requests: list, service, target_text: str) -> (int, list):
    """
    尋找文件中指定的定位文字，並回傳其起始索引。

    :param requests: 當前請求列表
    :param service: Google Docs API 服務對象
    :param target_text: 定位用的文字（必須存在於文件中）
    :return: (找到的起始索引, 更新後的請求列表)；若未找到則回傳 0
    """
    requests = update_doc(service, requests)
    doc = service.documents().get(documentId=GOOGLE_DOC_ID).execute()
    time.sleep(SLEEP)
    content = doc.get('body').get('content')

    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            start_index = element.get('startIndex', 0)
            if paragraph['elements'] and 'textRun' in paragraph['elements'][0]:
                text = paragraph['elements'][0]['textRun']['content']
                if target_text in text:
                    return start_index, requests

    print(f"\n  \033[31m[ERROR]: 未找到定位文字，請於文件模板中加入定位文字: 「{target_text}」\033[0m\n")
    return 0, requests

def insert_text(requests: list, text: str, style: str = "NORMAL_TEXT", startIndex: int = 1, indent: int = 0) -> (int, list):
    """
    插入指定文字到文件，並設置段落樣式。

    :param requests: 當前請求列表
    :param text: 要插入的文字
    :param style: 段落樣式（例如 "NORMAL_TEXT", "HEADING_1"）
    :param startIndex: 插入位置的起始索引
    :param indent: 縮排層級（若為 2，則在文字前加入制表符）
    :return: (更新後的插入位置索引, 更新後的請求列表)
    """
    if text == "":
        return startIndex + len(text), requests

    if indent == 2:
        text = '\t' + text

    text = f"{text}\n"
    text_length = len(text)

    insert_request = {
        "insertText": {
            "location": {"index": startIndex},
            "text": text
        }
    }
    style_request = {
        'updateParagraphStyle': {
            'range': {
                'startIndex': startIndex,
                'endIndex': startIndex + text_length,
            },
            'paragraphStyle': {
                'namedStyleType': style,
            },
            'fields': 'namedStyleType'
        }
    }
    requests.extend([insert_request, style_request])
    return startIndex + text_length, requests

def insert_bullet(requests: list, service, startIndex: int, endIndex: int) -> (int, list):
    """
    為指定範圍內的段落創建項目符號。

    :param requests: 當前請求列表
    :param service: Google Docs API 服務對象
    :param startIndex: 範圍起始索引
    :param endIndex: 範圍結束索引
    :return: (定位符所在索引, 更新後的請求列表)
    """
    requests = update_doc(service, requests)
    requests.append({
        'createParagraphBullets': {
            'range': {
                'startIndex': startIndex,
                'endIndex': endIndex,
            },
            'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE',
        }
    })
    text_here, requests = get_content_start(requests, service, DOC_INSERTION_POINT)
    return text_here, requests

def insert_link(requests: list, startIndex: int, endIndex: int, url: str) -> list:
    """
    在指定文字範圍內插入超連結。

    :param requests: 當前請求列表
    :param startIndex: 連結文字的起始索引
    :param endIndex: 連結文字的結束索引
    :param url: 超連結 URL
    :return: 更新後的請求列表
    """
    requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': startIndex,
                'endIndex': endIndex
            },
            'textStyle': {
                'link': {
                    'url': url
                }
            },
            'fields': 'link'
        }
    })
    return requests

def insert_image(requests: list, insertIndex: int, path: str, img_serial_num: int, img_num: int, img_cat='gauge') -> (int, list):
    """
    在指定位置插入圖片，並根據是否為最後一張圖片決定換行格式。

    :param requests: 當前請求列表
    :param insertIndex: 插入位置的起始索引
    :param path: 圖片的 URL
    :param img_serial_num: 當前圖片序號
    :param img_num: 圖片總數
    :param img_cat: 圖片類型（例如 'gauge' 或 'radial'）
    :return: (更新後的插入位置索引, 更新後的請求列表)
    """
    if img_serial_num != 0:
        insertIndex -= len("\n")

    img_height = {'gauge': 140, 'radial': 140, 'total': 200}

    requests.append({
        'insertInlineImage': {
            'location': {'index': insertIndex},
            'uri': path,
            'objectSize': {
                'height': {'magnitude': img_height[img_cat], 'unit': 'PT'},
                # 'width': {'magnitude': img_width[img_cat], 'unit': 'PT'}
            }
        }
    })
    time.sleep(SLEEP_IMAGE_PROCESSING)

    # 插入換行或空白以確保定位符正確換行
    if img_serial_num == img_num - 1:
        insertIndex, requests = insert_text(requests, " ", "NORMAL_TEXT", insertIndex + 1)
    else:
        insertIndex, requests = insert_text(requests, "          ", "NORMAL_TEXT", insertIndex + 1)

    return insertIndex, requests

def delete_text(requests: list, service, text: str) -> list:
    """
    刪除文件中指定的文字範圍。

    :param requests: 當前請求列表
    :param service: Google Docs API 服務對象
    :param text: 要刪除的文字
    :return: 更新後的請求列表
    """
    startIndex, requests = get_content_start(requests, service, text)
    endIndex = startIndex + len(text)
    requests.append({
        'deleteContentRange': {
            'range': {'startIndex': startIndex, 'endIndex': endIndex}
        }
    })
    return requests


def merge_data(requests: list, placeholder: str, text: str) -> list:
    """
    替換文件中的佔位符文字。

    :param requests: 當前請求列表
    :param placeholder: 佔位符（不包含大括號）
    :param text: 替換為的文字
    :return: 更新後的請求列表
    """
    requests.append({
        'replaceAllText': {
            'containsText': {
                'text': '{{' + placeholder + '}}',
                'matchCase': 'true'
            },
            'replaceText': text
        }
    })
    return requests


def generate_report(service, data: dict) -> None:
    """
    根據數據生成報告並寫入 Google Docs 文件中。

    :param service: Google Docs API 服務對象
    :param data: 包含報告各項數據的字典
    """
    print("\n╔═════════════════════════ GOOGLE DOC 內容寫入進行中 ═════════════════════════╗")
    requests = []

    formatted_date = time.strftime("%Y 年 %m 月 %d 日", time.localtime())
    date = formatted_date if not REPORT_DATE else REPORT_DATE
    requests = merge_data(requests, "REPORT_DATE", date)

    # 定位到插入點並插入總成熟度分數
    text_here, requests = get_content_start(requests, service, DOC_INSERTION_POINT)
    total_score = data['total_score']
    total_num = data['total_num']
    total_maturity = f"{round(total_score/total_num * 100, 1)}%"
    text_here, requests = insert_text(requests, f"\nWell Architect 整體成熟度: {total_maturity}\n", "HEADING_1", text_here)

    # 插入整體圖表
    for img_serial_num, uri in enumerate(data['chart_path']):
        text_here, requests = insert_image(requests, text_here, uri, img_serial_num, len(data['chart_path']), 'total')
    text_here, requests = insert_text(requests, f"\n\n", "HEADING_1", text_here)

    topic_cnt = 0

    # 處理每個主題
    for topic in data['topics']:
        if topic['topic'] == QUESTIONNAIRE_END_MARKER:
            break
        if topic['not_applicable']:
            continue
        
        topic_cnt += 1
        text_here, requests = get_content_start(requests, service, DOC_INSERTION_POINT)
        text_here, requests = insert_text(requests, f"\nTopic {topic_cnt}", "HEADING_6", text_here)
        text_here, requests = insert_text(requests, f"{topic['topic']} ☁️", "HEADING_1", text_here)
        text_here, requests = insert_text(requests, f"主題成熟度：{round(topic['topic_score']/topic['topic_num'] * 100, 1)}%", "NORMAL_TEXT", text_here)

        # 插入主題圖表
        for img_serial_num, uri in enumerate(topic['chart_path']):
            text_here, requests = insert_image(requests, text_here, uri, img_serial_num, len(topic['chart_path']), topic['chart_cat'][img_serial_num])
        
        # 處理每個問題
        for question in topic['questions']:
            if question['not_applicable']:
                continue

            # 插入問題文字
            text_here, requests = insert_text(requests, "\n" + question['question'], "HEADING_2", text_here)
            
            # 整理問題中各項目的資訊
            grouped_items = [[], []]
            group_titles = ["已達成項目", "未達成項目"]
            best_practices = []
            best_practices_ref = []
            for item in question['items']:
                if item['check']:
                    grouped_items[0].append({
                        'item': item['item'],
                        'note': item['note'],
                        'refined_note': item['refined_note']
                    })
                else:
                    grouped_items[1].append({
                        'item': item['item'],
                        'note': item['note'],
                        'refined_note': item['refined_note']
                    })
                    for i, bp in enumerate(item['best_practice']):
                        if bp not in best_practices:
                            best_practices.append(bp)
                            best_practices_ref.append(item['best_practice_ref'][i])

            # 插入項目資訊
            for idx_group, group in enumerate(grouped_items):
                text_here, requests = insert_text(requests, group_titles[idx_group], "HEADING_3", text_here)
                bullet_start = text_here
                bullet_end = bullet_start
                for item in group:
                    bullet_end, requests = insert_text(requests, item['item'], "NORMAL_TEXT", bullet_end, 1) # 項目內容
                    bullet_end, requests = insert_text(requests, item['refined_note'], "HEADING_5", bullet_end, 2) # 客戶現況
                if group:
                    text_here, requests = insert_bullet(requests, service, bullet_start, bullet_end)
                else:
                    text_here, requests = insert_text(requests, "    (無)", "NORMAL_TEXT", text_here, 1)
            
            # 插入建議發展階段
            text_here, requests = insert_text(requests, "建議發展階段", "HEADING_3", text_here)
            stage_text = question['stage'] if question['stage'] else "(無)"
            text_here, requests = insert_text(requests, "    " + stage_text, "NORMAL_TEXT", text_here, 1)
        
            # 插入現況成熟度
            text_here, requests = insert_text(requests, "現況成熟度", "HEADING_3", text_here)
            text_here, requests = insert_text(requests, f"{round(question['score']/question['num'] * 100, 1)}%", "NORMAL_TEXT", text_here)
            
            # 插入現況總整理
            text_here, requests = insert_text(requests, "現況總整理", "HEADING_3", text_here)
            condition = question['client_condition'] if question['client_condition'] else "(無)"
            text_here, requests = insert_text(requests, "    " + condition, "NORMAL_TEXT", text_here)
            
            # 插入最佳實務建議
            text_here, requests = insert_text(requests, "最佳實務建議", "HEADING_3", text_here)
            improvement = question['improvement_plan'] if question['improvement_plan'] else "(無)"
            text_here, requests = insert_text(requests, "    " + improvement, "NORMAL_TEXT", text_here)
            
            # 插入最佳實務參考
            text_here, requests = insert_text(requests, "最佳實務參考", "HEADING_3", text_here)
            best_practices_start = text_here
            best_practices_end = best_practices_start
            for idx_bp, bp in enumerate(best_practices):
                link_length = 0
                if bp == "NA":
                    best_practices_end, requests = insert_text(requests, best_practices_ref[idx_bp], "NORMAL_TEXT", best_practices_end, 1)
                    link_length = best_practices_end - len(best_practices_ref[idx_bp]) - 1
                else:
                    best_practices_end, requests = insert_text(requests, bp, "NORMAL_TEXT", best_practices_end, 1)
                    link_length = best_practices_end - len(bp) - 1

                if best_practices_ref[idx_bp] != "NA":
                    requests = insert_link(requests, link_length, best_practices_end, best_practices_ref[idx_bp])
            
            if best_practices:
                text_here, requests = insert_bullet(requests, service, best_practices_start, best_practices_end)
            else:
                text_here, requests = insert_text(requests, "    (無)", "NORMAL_TEXT", text_here, 1)

            requests = update_doc(service, requests)

        print(f"\n  ❏ Topic {topic['topic']} 寫入完成")

    # # 刪除定位用字串
    # requests = delete_text(requests, service, DOC_INSERTION_POINT)
    # requests = update_doc(service, requests)

    print("\n╚═════════════════════════ GOOGLE DOC 資料寫入已完成 ═════════════════════════╝")