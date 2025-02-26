import os
import time
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from settings import *
from utils.llm_handler import llm
from utils.chart_generator_gauge import create_gauge_chart
from utils.chart_generator_radial import create_radial_chart
from utils.remove_image_whitespace import remove_image_whitespace


def upload_image(service, path, folder_id):
    """
    上傳圖片到指定的 Google Drive 資料夾並回傳可共享的圖片連結。

    :param service: Google Drive API 服務對象
    :param path: 圖片檔案路徑
    :param folder_id: 目標資料夾 ID
    :return: 圖片共享連結，若失敗則回傳 None
    """
    # 清除圖片多餘的空白
    remove_image_whitespace(path)

    try:
        file_metadata = {
            'name': os.path.basename(path),
            'parents': [folder_id]
        }
        media = MediaFileUpload(path, resumable=True)
        
        # 上傳圖片並取得文件 ID
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')
        print(f"\n    ▪ 圖片成功上傳，File ID: {file_id}")
        
        # 設定圖片為公開可讀
        try:
            permission = {'role': 'reader', 'type': 'anyone'}
            service.permissions().create(fileId=file_id, body=permission, fields="id").execute()
            shared_link = f"https://drive.google.com/uc?export=view&id={file_id}"
            print(f"\n    ▪ 圖片已設為公開，分享連結: {shared_link}")
            return shared_link
        except HttpError as error:
            print(f"\n  \033[31m[ERROR] 圖片分享連結取得失敗: {error}\033[0m")
            return None
    except HttpError as error:
        print(f"\n  \033[31m[ERROR] 圖片上傳過程中出現錯誤: {error}\033[0m")
        return None


def generate_charts(service, data):
    """
    根據數據生成圖表，並上傳至 Google Drive，再將圖片連結儲存到數據字典中。

    :param service: Google Drive API 服務對象
    :param data: 包含整體與各主題數據的字典
    :return: 更新後包含圖表連結的數據字典
    """
    print("\n╔═════════════════════════════ 報表圖片繪製進行中 ════════════════════════════╗")

    # 取得當前時間並格式化日期字串
    formatted_date = time.strftime("%Y%m%d%H%M", time.localtime())

    # 生成整體儀表圖
    total_maturity = round(data['total_score'] / data['total_num'] * 100, 1)
    gauge_path = create_gauge_chart("0", total_maturity, formatted_date)
    shared_link = upload_image(service, gauge_path, GOOGLE_DRIVE_FOLDER_ID)
    data['chart_path'] = [shared_link] if shared_link else []
    data['chart_cat'] = ["gauge"]

    # 為每個主題生成圖表
    for i, topic in enumerate(data['topics']):
        if topic['not_applicable']:
            continue
        if topic['topic'] == QUESTIONNAIRE_END_MARKER:
            break

        # 生成主題儀表圖
        topic_maturity = round(topic['topic_score'] / topic['topic_num'] * 100, 1)
        gauge_path = create_gauge_chart(f"{i+1}", topic_maturity, formatted_date)
        shared_link = upload_image(service, gauge_path, GOOGLE_DRIVE_FOLDER_ID)
        topic['chart_path'] = [shared_link] if shared_link else []
        topic['chart_cat'] = ["gauge"]

        # 為該主題中的問題生成徑向圖
        maturities = []
        categories = []
        for question in topic['questions']:
            if question['not_applicable']:
                continue
            question_maturity = round(question['score'] / question['num'] * 100, 1)
            maturities.append(question_maturity)
            category_title = llm(LLM_NAME, "extract_question_aspects", "target sentences", question['question'])
            categories.append(category_title)

        radial_path = create_radial_chart(f"{i+1}", maturities, categories, formatted_date)
        shared_link = upload_image(service, radial_path, GOOGLE_DRIVE_FOLDER_ID)
        topic['chart_path'].append(shared_link)
        topic['chart_cat'].append("radial")

    print("\n╚═════════════════════════════ 報表圖片繪製已完成 ════════════════════════════╝")
    return data