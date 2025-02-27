from fastapi import APIRouter, Path, Body
from fastapi.responses import StreamingResponse
import uuid
from schemas.chat import SessionResponse, ChatRequest
import redis
from service.ragflow.session import create_chat_session
from service.ragflow.chat import converse_with_chat_assistant
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "infini_rag_flow")
SERVICE_PREFIX = os.getenv("SERVICE_PREFIX", "gsk-poc")

# raflow
RAGFLOW_API_ADDRESS = os.getenv("RAGFLOW_API_ADDRESS", "localhost:9380")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-Q4MTM2OTllZjJiMzExZWY5ODBhMDI0Mm")
RAGFLOW_CHAT_ID = os.getenv("RAGFLOW_CHAT_ID", "6cdad254e6e611efb2ef0242ac130006")

router = APIRouter()



##################################
# 创建一个新的对话 Session
##################################

@router.post("/create_session", response_model=SessionResponse)
async def create_session():
  
    session_name = str(uuid.uuid4()).replace("-", "")[:16]
    response = create_chat_session(RAGFLOW_API_ADDRESS, RAGFLOW_API_KEY, RAGFLOW_CHAT_ID, session_name)
    if response.get("code") == 0:
        session_id = str(response["data"]["id"])
        return {
            "session_id": session_id,
            "status": "success",
            "message": "Session created successfully"
        }
    else:
        return {
            "session_id": "",
            "status": "error",
            "message": response.get("message", "")
        }




##################################
# 基于ragflow知识库对话
##################################
# 假设这是服务 A，为键名添加前缀
# Redis 客户端
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password = REDIS_PASSWORD)


@router.post("/chat_on_docs/{session_id}")
async def chat_on_docs(
    session_id: str = Path(..., description="Session ID from the user"),
    request: ChatRequest = Body(..., description="User message")
):
    question = request.message

    # 生成一个唯一的 key
    key = f"{SERVICE_PREFIX}:{uuid.uuid4()}"

    async def stream_generator():
        try:
            async for chunk in converse_with_chat_assistant(RAGFLOW_API_ADDRESS, RAGFLOW_API_KEY, RAGFLOW_CHAT_ID, question, session_id=session_id):
                # 将每个 chunk 存储到 Redis 列表中
                r.rpush(key, chunk)  # 使用 RPUSH 将数据追加到列表
                r.expire(key, 600)  # 设置过期时间为 10分钟
                yield f"data: {chunk}\n\n"
        except Exception as e:
            r.rpush(key, f"Error: {str(e)}")  # 存储错误信息
            yield f"data: Error: {str(e)}\n\n"
        finally:
            # 流式响应结束，存储结束标识
            end_message = '{"code": 0, "data": true}'
            r.rpush(key, end_message)  # 存储结束标识
            yield f"data: {end_message}\n\n"

    # 返回 key 给前端
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"X-Stream-Key": key}
    )

@router.get("/get_chat_data")
async def get_chat_data(key: str):
    # 从 Redis 列表中获取所有数据
    data_list = r.lrange(key, 0, -1)
    if data_list:
        # 将数据列表转换为字符串列表
        data = [item.decode("utf-8") for item in data_list]
        return data
    else:
        return {"data": []}