from openai import OpenAI
import os
import json


def generate_recommended_questions(user_question, retrieved_content):
    """
    根据用户提问和检索到的内容生成推荐问题。

    :param user_question: 用户提问
    :param retrieved_content: 检索到的内容
    :return: 推荐问题列表
    """
    # 示例：基于用户提问和检索内容生成推荐问题

    # 判断 contents 是否为空
    if not retrieved_content:
        formatted_references = "知识库没有找到相关内容, 请结合你自己的知识回答"
    else:
        # 格式化参考内容
        formatted_references = "\n".join([f"[{ref['id']}] {ref['content_with_weight']}" for ref in retrieved_content])

   # 构造提示词
    prompt = f"""
    请根据以下用户提问和检索到的内容，生成 3 个相关的推荐问题：
    用户提问：{user_question}
    检索内容：{formatted_references}

    要求：
    1. 每个问题以“问题X：”开头，X 为问题编号。
    2. 每个问题后面紧跟具体问题内容。
    3. 返回一个 JSON 对象，包含一个字段 "recommended_questions"，值为问题列表。

    输出格式示例：
    {{
      "recommended_questions": [
        "问题1：具体问题内容1",
        "问题2：具体问题内容2",
        "问题3：具体问题内容3"
      ]
    }}
    
    请严格按照上述格式返回 JSON 对象。
    """
    
    # 调用大模型生成推荐问题
    client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY", "sk-f25b431f918a4796b65b1ae4a2c3ce56"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    completion = client.chat.completions.create(
        model="qwen2.5-72b-instruct",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        stream=False,
    )

    # 提取生成的推荐问题
    if completion.choices:
        response = completion.choices[0].message.content
        try:
            # 解析 JSON 响应
            response_json = json.loads(response)
            recommended_questions = response_json.get("recommended_questions", [])
            print("推荐的问题：\n")
            print(recommended_questions)
            return recommended_questions
        except json.JSONDecodeError:
            print("Failed to parse JSON response.")
            return []
    return []



def get_chat_completion(session_id, question, retrieved_content):
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

        # 返回检索内容
        message = {
            "documents": retrieved_content,
        }
        json_message = json.dumps(message)
        yield f"event: message\ndata: {json_message}\n\n"

        # 处理流式响应
        for chunk in completion:
            # print("原始 chunk 数据:", chunk)
            if chunk.choices[0].finish_reason == "stop":

                # 生成推荐问题
                recommended_questions = generate_recommended_questions(question, retrieved_content)
                if recommended_questions:
                    message = {
                        "recommended_questions": recommended_questions,
                    }
                    json_message = json.dumps(message)
                    yield f"event: message\ndata: {json_message}\n\n"

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
                    json_message = json.dumps(message)
                    yield f"event: message\ndata: {json_message}\n\n"
                else :
                    message = {
                        "role": "assistant",
                        "content": delta.reasoning_content,
                        "thinking": True,
                    }
                    json_message = json.dumps(message)
                    yield f"event: message\ndata: {json_message}\n\n"

    except Exception as e:
        # 发生错误时返回错误信息
        error_message = {
            "role": "error",
            "content": str(e)
        }
        json_error_message = json.dumps(error_message)
        yield f"event: error\ndata: {json_error_message}\n\n"


# 调用函数并获取流式输出
if __name__ == "__main__":
    session_id = "example_session"
    question = "你好"

    # 获取流式输出结果
    stream = get_chat_completion(session_id, question)

    # 输出符合 SSE 格式的结果
    for result in stream:
        print(result, end="", flush=True)