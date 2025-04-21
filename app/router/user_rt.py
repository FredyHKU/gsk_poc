from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from exceptions.auth import  AuthError
from service.auth import authenticate, register_user
from pydantic import BaseModel

router = APIRouter()


# 定义登录请求体的 Pydantic 模型
class LoginRequest(BaseModel):
    """
    用户登录请求模型
    包含用户名和密码字段
    """
    username: str
    password: str

# 用户认证接口
@router.post("/login")
async def login(request: LoginRequest):
    """
    用户登录接口
    验证用户身份并返回JWT令牌
    """
    try:
        # 调用 authenticate 函数进行认证
        token = authenticate(request.username, request.password)
        return {"access_token": token, "token_type": "bearer"}
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# 定义请求体的 Pydantic 模型
class RegisterRequest(BaseModel):
    """
    用户注册请求模型
    包含用户名和密码字段
    """
    username: str
    password: str

# 用户注册接口
@router.post("/register")
async def register(request: RegisterRequest):
    """
    用户注册接口
    创建新用户账户并存入数据库
    """
    try:
        # 调用 register_user 函数进行注册
        register_user(request.username, request.password)
        return {"message": "User registered successfully"}
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )