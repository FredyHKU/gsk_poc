import httpx
import json

async def converse_with_chat_assistant(address, api_key, chat_id, question, stream=True, session_id=None, user_id=None):
    url = f"http://{address}/api/v1/chats/{chat_id}/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    body = {
        "question": question,
        "stream": stream
    }
    if session_id:
        body["session_id"] = session_id
    if user_id:
        body["user_id"] = user_id

    timeout = httpx.Timeout(600.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            # 使用流式请求
            async with client.stream("POST", url, headers=headers, json=body) as response:
                async for line in response.aiter_lines():
                    yield f"{line}\n"
        except httpx.RequestError as e:
            print(f"Request failed: {e}")
            yield f"data: [ERROR] Request failed - {str(e)}\n\n"


# 示例调用
if __name__ == "__main__":
    address = os.getenv("RAGFLOW_BASE_URL")
    api_key = "ragflow-Q4MTM2OTllZjJiMzExZWY5ODBhMDI0Mm"
    chat_id = "c4269168f2b411ef99fc0242ac130005"
    question = "分析下世运电路成长性"
    session_id = "76f9b098f2b711ef960b0242ac130005"

    # 调用函数
    converse_with_chat_assistant(address, api_key, chat_id, question, session_id=session_id)