from fastapi import APIRouter, HTTPException, Path, Body
from fastapi.responses import StreamingResponse
import uuid
from schemas.chat import SessionResponse, ExploreRequest, ExploreResponse, AddDocsResponse, AddDocsRequest, ChatRequest
from service.chat_with_doc import chat_stream
import os
import json
from service.ragflow.session import create_chat_session
from service.ragflow.chat import converse_with_chat_assistant

router = APIRouter()

# 全局变量
session_list = []  # 会话列表



##################################
# 创建一个新的对话 Session
##################################

@router.post("/create_session", response_model=SessionResponse)
async def create_session():
    # try:
    #     # 生成唯一的 session_id
    #     session_id = str(uuid.uuid4()).replace("-", "")[:16]  # 生成一个 16 位的唯一标识

    #     # 将 session_id 添加到 session_list 和文件中
    #     session_list.append(session_id)

    #     return {
    #         "session_id": session_id,
    #         "status": "success",
    #         "message": "Session created successfully"
    #     }
    # except Exception as e:
    #     # 如果出现异常，返回错误信息
    #     raise HTTPException(status_code=500, detail="Failed to create session")
    address = "host.docker.internal:9380"
    api_key = "ragflow-AzMTU1N2IwZjM3MzExZWZiNTgyZDYyMz"
    chat_id = "b191e122f34c11efbfbce65b606a9fb3"
    session_name = str(uuid.uuid4()).replace("-", "")[:16]
    response = create_chat_session(address, api_key, chat_id, session_name)
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
# 基于用户发送的 message，后端检索并返回相关文档
##################################

# 模拟的文档数据
documents_db = [
    {
        "document_id": "doc123",
        "document_name": "国药集团物流合同.pdf",
        "preview": "xxxxxxxxxxxxxx",
        "create_time": 1740319113725,
        "update_time": 1740319113725,
    }
]


@router.post("/explore_docs/{session_id}", response_model=ExploreResponse)
async def explore_docs(session_id: str = Path(..., description="Session ID from the user"),
                       request: ExploreRequest = Body(..., description="User message")):
    # user_message = request.user_message

    try:
        # POC 只返回一份文档
        document = documents_db[0]
        
        response = {
            "documents": [document],
            "message": "Found 1 relevant document",
            "status": "success"
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

##################################
# 添加文档到会话上下文
##################################

session_document_map = {}
SESSION_DOCUMENT_MAP_FILE = "session_document_map.json"
def save_session_document_map():
    with open(SESSION_DOCUMENT_MAP_FILE, "w") as f:
        json.dump(session_document_map, f, indent=4)
    print("Session-document map saved to file.")

@router.post("/add_docs/{session_id}", response_model=AddDocsResponse)
async def add_docs_to_session(session_id: str = Path(..., description="Session ID from the user"),
                              request: AddDocsRequest = Body(..., description="Document IDs to add")):
    document_ids = request.document_id
    if not document_ids:
        raise HTTPException(status_code=400, detail="No document IDs provided")

    # POC 简化限制：只处理一份文档
    document_id = document_ids[0]
    if document_id not in [d["document_id"] for d in documents_db]:
        raise HTTPException(status_code=404, detail=f"Document ID {document_id} not found")

    # 建立 session_id 和 document_id 的联系
    document = documents_db[0]
    global session_document_map
    if session_id not in session_document_map:
        session_document_map[session_id] = document["document_id"]
        print(session_id)
        print(session_document_map[session_id])
        # 持久化到本地文件
        save_session_document_map()
    else:
        print(f"Session {session_id} already linked to document {session_document_map[session_id]}")


    # 获取文档名称
    document_name = document["document_name"]
    return {
        "status": "success",
        "message": f"Document {document_name} added to session"
    }

##################################
# 在已经添加文档的会话上下文基础上，对用户消息进行分析，并返回问答结果
##################################


@router.post("/chat_on_docs/{session_id}")
async def chat_on_docs(
    session_id: str = Path(..., description="Session ID from the user"),
    request: ChatRequest = Body(..., description="User message")
):
    # # 检查会话中是否有文档
    # if session_id not in session_document_map:
    #     raise HTTPException(status_code=400, detail={
    #         "status": "error",
    #         "err_code": 1001,
    #         "message": "No document added to this session."
    #     })
    
    # # 将文档内容和用户消息作为上下文
    # document_preview = "国药集团物流按件计费。。。"
    # context = "\n".join(document_preview)
    # user_message = request.message

    # # 构建提示内容
    # prompt = f'''
    # 请结合参考资料回答用户的问题，以下是参考资料：
    # {context}
    # 用户问题：{user_message}
    # '''

    # # 调用流式聊天函数
    # return StreamingResponse(chat_stream(prompt), media_type="text/event-stream")
    address = "host.docker.internal:9380"
    api_key = "ragflow-AzMTU1N2IwZjM3MzExZWZiNTgyZDYyMz"
    chat_id = "b191e122f34c11efbfbce65b606a9fb3"
    question = request.message
    return StreamingResponse(
        converse_with_chat_assistant(address, api_key, chat_id, question, session_id=session_id), 
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"}
    )


# 初始化时加载会话到文档的映射（如果有）
try:
    with open(SESSION_DOCUMENT_MAP_FILE, "r") as f:
        session_document_map = json.load(f)
    print("Loaded session-document map from file.")
except FileNotFoundError:
    print("No existing session-document map file found.")