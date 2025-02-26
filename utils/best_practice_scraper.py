# 從 Best Practice 超連結簡易抓取 Best Practice 網頁內容，效果不彰暫緩使用

import requests
from bs4 import BeautifulSoup
from utils.llm_handler import llm


def scrape_website(url: str) -> str:
    """
    抓取指定 URL 的網頁文字內容。

    :param url: 目標網頁的 URL
    :return: 該網頁的純文字內容；若發生錯誤則返回空字串
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # 若 HTTP 請求出現錯誤則拋出異常
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return ""

def best_practice_content_scraper(urls: list, best_practices: list) -> str:
    """
    根據提供的 Best Practice 超連結抓取網頁內容，並使用 LLM 提取相關內容。

    :param urls: 包含各 Best Practice 連結的列表
    :param best_practices: 與每個 URL 對應的 Best Practice 文字列表
    :return: 所有提取後內容的整合字串；若任何網頁無法抓取則返回空字串
    """
    print(f"\nbest_practices: {best_practices}")
    result = ""

    for i in range(len(urls)):
        
        if urls[i] == "":
            continue

        # 抓取網頁內容
        web_content = scrape_website(urls[i])
        if not web_content:
            print("Error: Unable to fetch web content.")
            return ""

        # 使用 LLM 提取與目標文字相關的內容
        target_text = f"Here is the target text: {best_practices[i]}"
        relevant_content = llm("gemini", "find_relevant_best_practices", web_content, target_text)
        print(f"\n[bp]: {best_practices[i]}")
        result += relevant_content + "\n"

    return result
