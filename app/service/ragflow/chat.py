from openai import OpenAI
import os

def get_chat_completion(session_id, question):
    """
    获取流式聊天完成结果，并按照指定格式输出。

    :param session_id: 会话 ID（可选，如需区分不同会话可传入）
    :param question: 用户问题
    :return: 流式输出的生成器，每个元素为符合 SSE 格式的字符串
    """
    try:
        # 初始化 OpenAI 客户端
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY", "sk-f25b431f918a4796b65b1ae4a2c3ce56"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # 创建聊天完成请求
        completion = client.chat.completions.create(
            model="deepseek-r1",  # 可按需更换模型名称
            messages=[
                {"role": "user", "content": question}
            ],
            stream=True,
        )

        # 处理流式响应
        for chunk in completion:
            # print("原始 chunk 数据:", chunk)
            if chunk.choices[0].finish_reason == "stop":
                # 结束时发送 [DONE] 事件
                yield "event: end\ndata: [DONE]\n\n"
                break
            else:
                # 实时输出消息
                delta = chunk.choices[0].delta
                if delta.content:
                    # 构造 SSE 格式的消息
                    message = {
                        "role": "assistant",
                        "content": delta.content,
                        "thinking": False,
                    }
                    yield f"event: message\ndata: {message}\n\n"
                else :
                    message = {
                        "role": "assistant",
                        "content": delta.reasoning_content,
                        "thinking": True,
                    }
                    yield f"event: message\ndata: {message}\n\n"

    except Exception as e:
        # 发生错误时返回错误信息
        error_message = {
            "role": "error",
            "content": str(e)
        }
        yield f"event: error\ndata: {error_message}\n\n"


# 调用函数并获取流式输出
if __name__ == "__main__":
    session_id = "example_session"
    question = "你好"

    # 获取流式输出结果
    stream = get_chat_completion(session_id, question)

    # 输出符合 SSE 格式的结果
    for result in stream:
        print(result, end="", flush=True)