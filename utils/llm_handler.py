import vertexai
from vertexai.generative_models import GenerativeModel

from settings import *

def gemini(task, topic, content):

    if content == "":
        return ""

    vertexai.init(project=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)

    model = GenerativeModel(
        model_name=GEMINI_MODEL_NAME,
        system_instruction=[
            "不要回傳任何與回覆無關的說明文字",
            "不要列點，要以文章形式回覆",
            "只回傳文字段落，不要回傳json或markdown格式",
            f"Task: {PROMPTS[task]}"
        ],
    )

    prompt = f"""
    User input: {topic}\n {content}
    Answer:
    """

    # Send text to Gemini
    response = model.generate_content(prompt)
    result = response.text.strip()

    # print(f"\n  ➤ Gemini Response: {response.text}")
    return result

def llm(llm, task, topic, content):
    if llm == "gemini":
        return gemini(task, topic, content)
    else:
        print(f"\n  \033[31m[ERROR] 不支援的 LLM 名稱 - {llm}\033[0m")
        return ""