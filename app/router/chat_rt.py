from fastapi import APIRouter, Path, Body, UploadFile, File, HTTPException
import uuid
from schemas.chat import SessionResponse, ChatRequest
from fastapi.responses import StreamingResponse
import os
import json
from dotenv import load_dotenv
from typing import List
from service.ragflow.file_parse import execute_insert_process
from service.ragflow.api.utils.file_utils import get_project_base_directory
from service.ragflow.retrieval2 import retrieve_content
from service.ragflow.chat import get_chat_completion
from service.ragflow.retrieval import search_documents

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


@router.post("/upload_files/{session_id}")
async def upload_files(
    session_id: str,
    files: List[UploadFile] = File(...)
):
    
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


@router.post("/chat_on_docs/{session_id}")
async def chat_on_docs(
    session_id: str = Path(..., description="Session ID from the user"),
    request: ChatRequest = Body(..., description="User message")
):
    question = request.message
    contents = retrieve_content(session_id, question)
    # 判断 contents 是否为空
    if not contents:
        combined_content = "知识库没有找到相关内容"
    else:
        # 提取 content_with_weight 并拼接
        content_with_weight_list = [item['content_with_weight'] for item in contents]
        combined_content = "\n\n ".join(content_with_weight_list)
    
        # 拼接用户问题和提取的内容
        prompt = f"""
请根据相关背景信息回答用户的问题：
用户问题: {question}
相关背景信息: {combined_content}
"""

        print(prompt)


    # 返回流式响应
    return StreamingResponse(
        get_chat_completion(session_id, prompt
        ),
        media_type="text/event-stream"
    )

from typing import List, Optional
from pydantic import BaseModel

# 定义请求体模型
class SearchRequest(BaseModel):
    question: str
    indexNames: str
    # knowledgebaseIds: Optional[List[str]] = None
    selectFields: Optional[List[str]] = None
    highlightFields: Optional[List[str]] = None
    condition: Optional[dict] = None
    offset: Optional[int] = 0
    limit: Optional[int] = 10
    aggFields: Optional[List[str]] = None
    rank_feature: Optional[dict] = None
    topn: Optional[int] = 10
    text_match_weight: Optional[float] = 0.3
    dense_match_weight: Optional[float] = 0.7
    similarity_threshold: Optional[float] = 0.5
    minimum_should_match: Optional[float] = 0.3

# 定义搜索接口
@router.post("/search")
def search(request: SearchRequest):
    """
    搜索接口，接收用户问题和索引名称，返回搜索结果。
    """
    try:
        # 调用 search_documents 函数
        results = search_documents(
            question=request.question,
            indexNames=request.indexNames
        )
        return {"status": "success", "data": results}
    except Exception as e:
        # 捕获异常并返回错误信息
        raise HTTPException(status_code=500, detail=str(e))