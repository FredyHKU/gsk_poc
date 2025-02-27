import requests
import json
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 从.env文件中获取配置
API_URL = os.getenv("API_URL")
API_MODEL = os.getenv("API_MODEL")
API_TOKEN = os.getenv("API_TOKEN")

def chat_stream(prompt: str):
    """
    调用大模型 API 并以流式方式返回回答，格式化为 SSE 格式。
    :param prompt: 用户输入的提示内容
    :yield: SSE 格式的回答内容
    """
    if not API_URL or not API_MODEL or not API_TOKEN:
        raise ValueError("API 配置未正确加载，请检查.env文件")

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": API_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True,  # 启用流式响应
        "max_tokens": 512,
        "stop": ["null"],
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "response_format": {"type": "text"}
    }

    response = requests.post(API_URL, json=payload, headers=headers, stream=True)

    if response.status_code != 200:
        raise Exception(f"API 请求失败，状态码：{response.status_code}, 响应内容：{response.text}")

    assistant_response = ""  # 用于拼接完整的回答

    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            if decoded_line.startswith("data:"):
                if decoded_line == "data: [DONE]":
                    # 明确处理结束标记
                    yield "event: end\n" \
                          f"data: [DONE]\n\n"
                    break
                else:
                    try:
                        data = json.loads(decoded_line[5:])  # 去掉 "data: " 前缀
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "").strip()
                            if content:
                                assistant_response += content  # 拼接回答内容
                                yield f"event: message\n" \
                                      f"data: {{\"role\": \"assistant\", \"content\": \"{content}\"}}\n\n"
                            # if choices[0].get("finish_reason") == "stop":
                            #     yield f"event: end\n" \
                            #           f"data: [DONE]\n\n"
                    except json.JSONDecodeError as e:
                        print(f"JSON 解码错误: {e}")
                        print(f"原始数据: {decoded_line}")

# 示例调用
if __name__ == "__main__":
    prompt = "中国大模型行业2025年将会迎来哪些机遇和挑战？"
    for output in chat_stream(prompt):
        print(output, end="")