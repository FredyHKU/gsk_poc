from fastapi import APIRouter, Body, UploadFile, File, HTTPException, Query, Security, status
import uuid
from schemas.chat import SessionResponse, ChatRequest
from fastapi.responses import StreamingResponse
import os
from dotenv import load_dotenv
from typing import List
from service.core.file_parse import execute_insert_process
from service.core.api.utils.file_utils import get_project_base_directory
from fastapi_jwt import JwtAuthorizationCredentials
from service.core.retrieval import retrieve_content
from service.core.chat import get_chat_completion
from service.auth import access_security
from utils import logger
from typing import List, Optional
from database.knowledgebase_operations import insert_knowledgebase, verify_user_knowledgebase

# 加载 .env 文件
load_dotenv()


router = APIRouter()



##################################
# 创建一个新的对话 Session
##################################

@router.post("/create_session", response_model=SessionResponse)
async def create_session(
    credentials: JwtAuthorizationCredentials = Security(access_security),
):
    """
    创建一个新的聊天会话，生成唯一的会话ID
    验证用户身份并返回会话ID
    """
    try:
        user_id = credentials.subject.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        # 生成16位会话ID
        session_id = str(uuid.uuid4()).replace("-", "")[:16]

        return {
            "session_id": session_id,
            "status": "success",
            "message": "Session created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



@router.post("/upload_files/")
async def upload_files(
    session_id: Optional[str] = Query(None),
    files: List[UploadFile] = File(...),
    credentials: JwtAuthorizationCredentials = Security(access_security),
):
    """
    上传文件到指定会话
    将文件保存到本地存储并插入到ElasticSearch和PostgreSQL数据库中
    """
    if session_id is None:
        session_id = "default"  # 设置默认值
    # 确保 storage/file 文件夹存在
    storage_dir = os.path.join(get_project_base_directory(), "storage/file")
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    
    # 根据 session_id 创建子文件夹
    session_dir = os.path.join(storage_dir, session_id)
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    try:
        user_id = str(credentials.subject.get("user_id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        for file in files:
            file_name = file.filename
            file_path = os.path.join(session_dir, file_name)
            
            # 保存文件到本地
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            
            # 保存文件 URL 和 Base64 编码的文件流
            file_url = f"{storage_dir}/{session_id}/{file_name}"
            # file_streams.append(await file.read())  # 或根据需要处理文件流
            print(file_url)
            print(file_name)

            # 将文件内容解析并存入ES
            execute_insert_process(file_url, file_name, user_id)
            logger.info("数据插入es")

            # 将文件记录存入PostgreSQL
            insert_knowledgebase(user_id, file_name)
            logger.info("数据插入pg")

        return {
            "status": "success",
            "message": "文件解析成功"
        }
    
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    



@router.post("/chat_on_docs/")
async def chat_on_docs(
    session_id: str = Query(...),
    request: ChatRequest = Body(..., description="User message"),
    credentials: JwtAuthorizationCredentials = Security(access_security),
):
    """
    基于已上传文档进行聊天
    从知识库中检索相关内容，并生成流式响应
    """
    try:
        user_id = str(credentials.subject.get("user_id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        # 验证用户是否有自己的知识库
        verify_user_knowledgebase(user_id)

        question = request.message
    
        # 从知识库检索与问题相关的内容
        references = retrieve_content(user_id, question)


        # 返回流式响应
        return StreamingResponse(
            get_chat_completion(session_id, question, references, user_id
            ),
            media_type="text/event-stream"
        )
    
    except HTTPException as e:
        # 捕获 HTTPException 并重新抛出，保持状态码和详情
        raise e
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )