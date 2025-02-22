from fastapi import APIRouter, HTTPException, Path, Body
from fastapi.responses import StreamingResponse
import uuid
from schemas.chat import SessionResponse, ExploreRequest, ExploreResponse, AddDocsResponse, AddDocsRequest, ChatRequest
from service.chat_with_doc import chat_stream
import os

router = APIRouter()

# 全局变量
session_list = []  # 会话列表



##################################
# 创建一个新的对话 Session
##################################

@router.post("/create_session", response_model=SessionResponse)
async def create_session():
    try:
        # 生成唯一的 session_id
        session_id = str(uuid.uuid4()).replace("-", "")[:16]  # 生成一个 16 位的唯一标识

        # 将 session_id 添加到 session_list 和文件中
        session_list.append(session_id)

        return {
            "session_id": session_id,
            "status": "success",
            "message": "Session created successfully"
        }
    except Exception as e:
        # 如果出现异常，返回错误信息
        raise HTTPException(status_code=500, detail="Failed to create session")

##################################
# 基于用户发送的 message，后端检索并返回相关文档
##################################

@router.post("/explore_docs/{session_id}", response_model=ExploreResponse)
async def explore_docs(session_id: str = Path(..., description="Session ID from the user"),
                       request: ExploreRequest = Body(..., description="User message")):
    # user_message = request.user_message
    # 模拟的文档数据
    documents_db = [
        {
            "document_id": "doc123",
            "document_name": "国药集团物流合同.pdf",
            "preview": "xxxxxxxxxxxxxx"
        }
    ]
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

# 模拟的文档数据库
documents_db = {
    "doc123": {"document_name": "国药集团物流合同.pdf"},
    "doc456": {"document_name": "物流服务协议.docx"}
}

@router.post("/add_docs/{session_id}", response_model=AddDocsResponse)
async def add_docs_to_session(session_id: str = Path(..., description="Session ID from the user"),
                              request: AddDocsRequest = Body(..., description="Document IDs to add")):
    document_ids = request.document_id
    if not document_ids:
        raise HTTPException(status_code=400, detail="No document IDs provided")

    # POC 简化限制：只处理一份文档
    document_id = document_ids[0]
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail=f"Document ID {document_id} not found")

    # 获取文档名称
    document_name = documents_db[document_id]["document_name"]

    # 模拟的会话上下文存储
    session_context = {}

    # 将文档 ID 添加到会话上下文
    if session_id not in session_context:
        session_context[session_id] = []
    session_context[session_id].append(document_id)

    return {
        "status": "success",
        "message": f"Document {document_name} added to session"
    }

##################################
# 在已经添加文档的会话上下文基础上，对用户消息进行分析，并返回问答结果
##################################



session_doc_data = [
    {"session_01": [{"document_id": "doc123", "document_name": "国药集团物流合同.pdf", "preview": "xxxxxxxxxxxxxx"}]}, 
    { "session_02": []}
]

@router.post("/chat_on_docs/{session_id}")
async def chat_on_docs(
    session_id: str = Path(..., description="Session ID from the user"),
    request: ChatRequest = Body(..., description="User message")
):
    # 检查会话中是否有文档
    if session_id not in ["session_01"]:
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "err_code": 1001,
            "message": "No document added to this session."
        })
    
    # 将文档内容和用户消息作为上下文
    document_preview = "国药集团物流按件计费。。。"
    context = "\n".join(document_preview)
    user_message = request.message

    # 构建提示内容
    prompt = f'''
    请结合参考资料回答用户的问题，以下是参考资料：
    {context}
    用户问题：{user_message}
    '''

    # 调用流式聊天函数
    return StreamingResponse(chat_stream(prompt), media_type="text/event-stream")

