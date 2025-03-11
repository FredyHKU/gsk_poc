from fastapi import APIRouter, Path, Body, UploadFile, File, HTTPException, Query
import uuid
from schemas.chat import SessionResponse, ChatRequest
from fastapi.responses import StreamingResponse
import os
import json
from dotenv import load_dotenv
from typing import List
from service.ragflow.file_parse import execute_insert_process
from service.ragflow.api.utils.file_utils import get_project_base_directory
# from service.ragflow.retrieval2 import retrieve_content
from service.ragflow.retrieval import retrieve_content
from service.ragflow.chat import get_chat_completion
from typing import List, Optional

# 加载 .env 文件
load_dotenv()


router = APIRouter()



##################################
# 创建一个新的对话 Session
##################################

@router.post("/create_session", response_model=SessionResponse)
async def create_session():
  
    session_id = str(uuid.uuid4()).replace("-", "")[:16]
    # response = create_chat_session(RAGFLOW_API_ADDRESS, RAGFLOW_API_KEY, RAGFLOW_CHAT_ID, session_name)
    # if response.get("code") == 0:
    #     session_id = str(response["data"]["id"])
    return {
        "session_id": session_id,
        "status": "success",
        "message": "Session created successfully"
    }
    # else:
    #     return {
    #         "session_id": "",
    #         "status": "error",
    #         "message": response.get("message", "")
    #     }


@router.post("/upload_files/")
async def upload_files(
    session_id: Optional[str] = Query(None),
    files: List[UploadFile] = File(...)
):
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
            print(session_id)

            execute_insert_process(file_url, file_name, session_id)

        return {
            "status": "success",
            "message": "文件解析成功"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")

    

##################################
# 基于ragflow知识库对话
##################################


@router.post("/chat_on_docs/")
async def chat_on_docs(
    session_id: Optional[str] = Query(None),
    request: ChatRequest = Body(..., description="User message")
):
    question = request.message
    if session_id is None:
        session_id = "default"  # 设置默认值

    references = retrieve_content(session_id, question)
    

    # 判断 contents 是否为空
    if not references:
        formatted_references = "知识库没有找到相关内容, 请结合你自己的知识回答"
    else:
        # 格式化参考内容
        formatted_references = "\n".join([f"[{ref['id']}] {ref['content_with_weight']}" for ref in references])
    
        
    prompt = f"""
    你是一个智能助手，负责根据用户的问题和提供的参考内容生成回答。请严格按照以下要求生成回答：
    1. 回答必须基于提供的参考内容。
    2. 在回答中，每一块内容都必须标注引用的来源，格式为：##引用编号$$。例如：##1$$ 表示引用自第1条参考内容。
    3. 如果没有参考内容，请明确说明。
    
    参考内容：
    {formatted_references}
    
    用户问题：{question}
    """

    print(prompt)


    # 返回流式响应
    return StreamingResponse(
        get_chat_completion(session_id, prompt, references
        ),
        media_type="text/event-stream"
    )