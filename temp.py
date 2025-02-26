import time

from config import *


def update_doc(service, requests):
    if len(requests) > 0:
        service.documents().batchUpdate(documentId=GOOGLE_DOC_ID, body={"requests": requests}).execute()
        time.sleep(SLEEP)
    requests = []
    return requests

def get_content_start(requests, service, target_text):
    requests = update_doc(service, requests)

    # 取得文檔內容
    doc = service.documents().get(documentId=GOOGLE_DOC_ID).execute()
    time.sleep(SLEEP)

    # 文檔的內容
    content = doc.get('body').get('content')

    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            start_index = element.get('startIndex', 0)

            if 'textRun' in paragraph['elements'][0]:
                text = paragraph['elements'][0]['textRun']['content']
                if target_text in text:  # 檢查文字是否匹配
                    end_index = start_index + len(text)
                    return start_index, requests
                
    print(f"\n  \033[31m[ERROR]: 未找到定位文字，請於文件模板中加入定位文字: 「{target_text}」\033[0m\n")
    return 0, requests

def insert_text(requests, text, style="NORMAL_TEXT", startIndex=1, indent=0):
    if text == "":
        return startIndex + len(text), requests
    # indent_offset = [0, 36, 72, 108]

    if indent == 2:
        text = '\t' + text

    """
    插入文字並設定樣式
    :param service: Google Docs API 服務
    :param document_id: Google Docs 文件 ID
    :param text: 要插入的文字
    :param style: 文字樣式（例如 "NORMAL_TEXT", "HEADING_1"）
    """
    text = f"{text}\n"
    text_length = len(text)

    # 插入文字的請求
    insert_request = {
        "insertText": {
            "location": {"index": startIndex},  # 插入到文件的起始位置
            "text": text
        }
    }

    # 設置樣式的請求
    style_request = {
        'updateParagraphStyle': 
        {
            'range': 
            {
                'startIndex': startIndex,
                'endIndex':  startIndex + text_length,
            },
            'paragraphStyle': 
            {
                'namedStyleType': style,
            },
            'fields': 'namedStyleType'
        }
    }

    # 合併兩個請求
    requests.extend([insert_request, style_request])

    return (startIndex + text_length), requests

def insert_bullet(requests, service, startIndex, endIndex):
    requests = update_doc(service, requests)
    requests.append(
        {
            'createParagraphBullets': 
            {
                'range': 
                {
                    'startIndex': startIndex,
                    'endIndex':  endIndex,
                },
                'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE',
            }
        }
    )
    text_here, requests = get_content_start(requests, service, DOC_INSERTION_POINT)
    return text_here,requests

def insert_link(requests, startIndex, endIndex, url):
    requests.append(
        {
            'updateTextStyle': {
                'range': {
                    'startIndex': startIndex,     # "Click Here" 的起始索引
                    'endIndex': endIndex       # "Click Here" 的結束索引 (包含字符)
                },
                'textStyle': {
                    'link': {
                        'url': url  # 超連結 URL
                    }
                },
                'fields': 'link'
            }
        }
    )
    return requests

def insert_image(requests, insertIndex, path, img_serial_num, img_num, img_cat):

    if img_serial_num != 0:
        insertIndex -= len("\n")

    img_width = {
        'gauge': 176,
        'radial': 250
    }
     
    requests.append({
        'insertInlineImage': {
            'location': {
                'index': insertIndex,
            },
            'uri': path,
            'objectSize': {
                'height': {
                    'magnitude': 140,
                    'unit': 'PT'
                },
                # 'width': {
                #     'magnitude': img_width[img_cat],
                #     'unit': 'PT'
                # }
            }
        }
    })
    
    time.sleep(SLEEP_IMAGE_PROCESSING)

    if img_serial_num == img_num - 1:
        # 為了讓定位符 "TEXT-HERE" 在插入圖片後換行
        # 由於 insert_text 會自動加入換行，傳入 "\n" 會多換一次
        # 由於 insert_text 會篩掉空字串，傳入 "" 無法讓 TEXT-HERE 換行
        # 綜上所述，所以此處要傳 " "，很醜我道歉
        insertIndex, requests = insert_text(requests, " ", "NORMAL_TEXT", insertIndex + 1) 
    else:
        insertIndex, requests = insert_text(requests, "          ", "NORMAL_TEXT", insertIndex + 1)

    return insertIndex, requests

def delete_text(requests, service, text):
    startIndex, requests = get_content_start(requests, service, text)
    endIndex = startIndex + len(text)

    requests.append(
        {
            'deleteContentRange': 
            {
                'range': 
                {
                    'startIndex': startIndex,
                    'endIndex': endIndex
                }
            }
        }
    )

    return requests


def merge_data(requests,placeholder, text):
    """
    替換 Google Docs 中的佔位符
    :param service: Google Docs API 服務
    :param document_id: Google Docs 文件 ID
    :param placeholder: 要替換的佔位符
    :param text: 替換為的文字
    """
    requests.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{' + placeholder + '}}',
                    'matchCase':  'true'
                },
                'replaceText': text
            }
        }
    )
    return requests

def write_doc(data, service):
    print("\n╔═════════════════════════ GOOGLE DOC 內容寫入進行中 ═════════════════════════╗")

    requests = []

    # 取得今天的時間戳
    current_time = time.localtime()
    # 格式化日期
    formatted_date = time.strftime("%Y 年 %m 月 %d 日", current_time)
    date = formatted_date if not REPORT_DATE else REPORT_DATE
    requests = merge_data(requests, "REPORT_DATE", date)

    text_here, requests = get_content_start(requests, service, DOC_INSERTION_POINT)
    total_score = data['total_score']
    total_num = data['total_num']

    total_maturity = f"{total_score}/{total_num} → {round(total_score/total_num * 100, 1)}%"
    text_here, requests = insert_text(requests, f"總成熟度分數: {total_maturity}", "HEADING_1", text_here)
    # text_here, requests = insert_text(requests, str(total_score) + "/" + str(total_num), "NORMAL_TEXT", text_here, 1)
    for img_serial_num, uri in enumerate(data['chart_path']):
        text_here, requests = insert_image(requests, text_here, uri, img_serial_num, len(data['chart_path']), data['chart_cat'][img_serial_num])

    for topic in data['topics']:
        if topic['topic'] == QUESTIONNAIRE_END_MARKER:
            break
        if topic['not_applicable']:
            continue
        text_here, requests = get_content_start(requests, service, DOC_INSERTION_POINT)
        text_here, requests = insert_text(requests, topic['topic'], "HEADING_1", text_here)
        text_here, requests = insert_text(requests, f"主題成熟度：{topic['topic_score']}/{topic['topic_num']} → {round(topic['topic_score']/topic['topic_num'] * 100, 1)}%", "NORMAL_TEXT", text_here)
        for img_serial_num, uri in enumerate(topic['chart_path']):
            text_here, requests = insert_image(requests, text_here, uri, img_serial_num, len(topic['chart_path']), topic['chart_cat'][img_serial_num])
        
        for question in topic['questions']:
            if question['not_applicable']:
                continue
            
            # text_here, requests = insert_text(requests, question['area'], "HEADING_4", text_here) # area (Practice Cloud Financial...)
            text_here, requests = insert_text(requests, "\n" + question['question'], "HEADING_2", text_here) # question (COST 1. 您如何...)

            grouped_items = [[], []]
            group_titles = ["已達成項目", "未達成項目"]
            # grouped_items = [[], [], []]
            # group_titles = ["已達成項目", "未達成項目", "略過項目"]
            best_practices = []
            best_practices_ref = []
            # best_practices_content = []
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
                            best_practices.append(bp) # Best Practice 蒐集
                            best_practices_ref.append(item['best_practice_ref'][i]) # Best Practice Reference 蒐集

            for _, group in enumerate(grouped_items):

                text_here, requests = insert_text(requests, group_titles[_], "HEADING_3", text_here)
                bullet_start = text_here
                bullet_end = bullet_start
                for item in group:
                    bullet_end, requests = insert_text(requests, item['item'], "NORMAL_TEXT", bullet_end, 1) # 項目名稱
                    bullet_end, requests = insert_text(requests, item['refined_note'], "HEADING_5", bullet_end, 2) # 客戶現況
                
                if len(group) > 0:
                    text_here, requests = insert_bullet(requests, service, bullet_start, bullet_end)
                else:
                    text_here, requests = insert_text(requests, "    (無)", "NORMAL_TEXT", text_here, 1)
                # text_here, requests = get_content_start(requests, service, EDIT_TARGET_TEXT)
                # text_here = bullet_end
            
            text_here, requests = insert_text(requests, "建議發展階段", "HEADING_3", text_here)
            reco = question['reco'] if question['reco'] else "(無)"
            text_here, requests = insert_text(requests, "    " + reco, "NORMAL_TEXT", text_here, 1) # reco

            # text_here, requests = get_content_start(requests, service, EDIT_TARGET_TEXT)
            text_here, requests = insert_text(requests, f"現況成熟度", "HEADING_3", text_here)
            text_here, requests = insert_text(requests, f"    {question['score']}/{question['num']} → {round(question['score']/question['num'] * 100, 1)}%", "NORMAL_TEXT", text_here)
            text_here, requests = insert_text(requests, "現況總整理", "HEADING_3", text_here)
            condition = question['client_condition'] if question['client_condition'] else "(無)"
            text_here, requests = insert_text(requests, "    " + condition, "NORMAL_TEXT", text_here) # client_condition

            text_here, requests = insert_text(requests, "最佳實務建議", "HEADING_3", text_here)
            improvement = question['improvement_plan'] if question['improvement_plan'] else "(無)"

            text_here, requests = insert_text(requests, "    " + improvement, "NORMAL_TEXT", text_here) # improvement_plan

            text_here, requests = insert_text(requests, "最佳實務參考", "HEADING_3", text_here)
            best_practices_start = text_here
            best_practices_end = best_practices_start
            for _, bp in enumerate(best_practices):

                link_length = 0
                if bp == "NA":
                    best_practices_end, requests = insert_text(requests, best_practices_ref[_], "NORMAL_TEXT", best_practices_end, 1)
                    link_length = best_practices_end - len(best_practices_ref[_]) - 1
                else:
                    best_practices_end, requests = insert_text(requests, bp, "NORMAL_TEXT", best_practices_end, 1)
                    link_length = best_practices_end - len(bp) - 1

                if best_practices_ref[_] != "NA":
                    requests = insert_link(requests, link_length, best_practices_end, best_practices_ref[_])

            if len(best_practices) > 0:
                text_here, requests = insert_bullet(requests, service, best_practices_start, best_practices_end)
            else:
                text_here, requests = insert_text(requests, "    (無)", "NORMAL_TEXT", text_here, 1)

            update_doc(service, requests)

        print(f"\n  ❏ Topic {topic['topic']} 寫入完成")
    
    # 刪除定位用字串
    requests = delete_text(requests, service, DOC_INSERTION_POINT)
    requests = update_doc(service, requests)

    print("\n╚═════════════════════════ GOOGLE DOC 資料寫入已完成 ═════════════════════════╝")