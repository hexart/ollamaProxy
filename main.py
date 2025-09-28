#!/usr/bin/env python3
"""
Ollama OpenAI 兼容 API 代理服务
将 Ollama API 转换为 OpenAI 兼容格式
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import json
import logging
import time
import uuid
from typing import List, Dict, Optional
from pydantic import BaseModel
import os
import sys

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ollama OpenAI Compatible API",
    description="OpenAI-compatible proxy for Ollama",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama配置
OLLAMA_BASE_URL = "http://localhost:11434"
TIMEOUT = 60.0

# 从环境变量或配置文件加载设置
def load_config():
    global OLLAMA_BASE_URL, TIMEOUT
    
    # 尝试从配置文件加载
    config_file = 'config.json'
    if getattr(sys, 'frozen', False):
        # 打包后的应用
        config_file = os.path.join(os.getcwd(), 'config.json')
    else:
        # 开发环境
        config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                OLLAMA_BASE_URL = config.get('ollama_base_url', OLLAMA_BASE_URL)
                TIMEOUT = config.get('timeout', TIMEOUT)
    except Exception:
        pass

# 加载配置
load_config()

# Pydantic 模型定义


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False


class CompletionRequest(BaseModel):
    model: str
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False


@app.get("/v1/models")
@app.get("/models")
async def list_models():
    """列出所有可用模型"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OLLAMA_BASE_URL}/api/tags",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            ollama_models = response.json()

            # 转换为OpenAI格式
            openai_models = {
                "object": "list",
                "data": [
                    {
                        "id": tag["name"],
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "ollama"
                    }
                    for tag in ollama_models.get("models", [])
                ]
            }
            return openai_models

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ollama request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """聊天完成接口"""
    try:
        # 构造Ollama请求
        ollama_request = {
            "model": request.model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in request.messages
            ],
            "stream": request.stream,
            "options": {
                "temperature": request.temperature
            }
        }

        if request.max_tokens:
            ollama_request["options"]["num_predict"] = request.max_tokens

        if request.stream:
            # 流式响应
            return StreamingResponse(
                stream_response(ollama_request),
                media_type="text/event-stream"
            )
        else:
            # 非流式响应
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json=ollama_request,
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                ollama_response = response.json()

                # 转换为OpenAI格式
                openai_response = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": ollama_response.get("message", {}).get("content", "")
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
                return openai_response

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ollama request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def stream_response(ollama_request: dict):
    """流式响应处理"""
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json=ollama_request,
                timeout=TIMEOUT
            ) as response:
                response.raise_for_status()
                
                openai_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
                created_time = int(time.time())
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            ollama_data = json.loads(line)
                            
                            # 转换为OpenAI SSE格式
                            if ollama_data.get("done"):
                                # 结束标记
                                openai_data = {
                                    "id": openai_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_time,
                                    "model": ollama_request["model"],
                                    "choices": [{
                                        "index": 0,
                                        "delta": {},
                                        "finish_reason": "stop"
                                    }]
                                }
                            else:
                                # 内容标记
                                openai_data = {
                                    "id": openai_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_time,
                                    "model": ollama_request["model"],
                                    "choices": [{
                                        "index": 0,
                                        "delta": {
                                            "content": ollama_data.get("message", {}).get("content", "")
                                        },
                                        "finish_reason": None
                                    }]
                                }
                            
                            yield f"data: {json.dumps(openai_data)}\n\n"
                            
                        except json.JSONDecodeError:
                            continue
                
                # 结束流
                yield "data: [DONE]\n\n"
                
    except httpx.TimeoutException:
        yield 'data: {"error": "Ollama request timeout"}\n\n'
    except httpx.RequestError as e:
        yield f'data: {{"error": "Ollama request failed: {str(e)}"}}\n\n'
    except Exception as e:
        yield f'data: {{"error": "{str(e)}"}}\n\n'


@app.post("/v1/completions")
@app.post("/completions")
async def completions(request: CompletionRequest):
    """文本补全接口"""
    try:
        # 构造Ollama请求
        ollama_request = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": request.stream,
            "options": {
                "temperature": request.temperature
            }
        }

        if request.max_tokens:
            ollama_request["options"]["num_predict"] = request.max_tokens

        if request.stream:
            # 流式响应
            return StreamingResponse(
                stream_completions(ollama_request),
                media_type="text/event-stream"
            )
        else:
            # 非流式响应
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json=ollama_request,
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                ollama_response = response.json()

                # 转换为OpenAI格式
                openai_response = {
                    "id": f"cmpl-{uuid.uuid4().hex[:12]}",
                    "object": "text_completion",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "text": ollama_response.get("response", ""),
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
                return openai_response

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ollama request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def stream_completions(ollama_request: dict):
    """文本补全流式响应处理"""
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/generate",
                json=ollama_request,
                timeout=TIMEOUT
            ) as response:
                response.raise_for_status()
                
                openai_id = f"cmpl-{uuid.uuid4().hex[:12]}"
                created_time = int(time.time())
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            ollama_data = json.loads(line)
                            
                            # 转换为OpenAI SSE格式
                            if ollama_data.get("done"):
                                # 结束标记
                                openai_data = {
                                    "id": openai_id,
                                    "object": "text_completion",
                                    "created": created_time,
                                    "model": ollama_request["model"],
                                    "choices": [{
                                        "index": 0,
                                        "text": "",
                                        "finish_reason": "stop"
                                    }]
                                }
                            else:
                                # 内容标记
                                openai_data = {
                                    "id": openai_id,
                                    "object": "text_completion",
                                    "created": created_time,
                                    "model": ollama_request["model"],
                                    "choices": [{
                                        "index": 0,
                                        "text": ollama_data.get("response", ""),
                                        "finish_reason": None
                                    }]
                                }
                            
                            yield f"data: {json.dumps(openai_data)}\n\n"
                            
                        except json.JSONDecodeError:
                            continue
                
                # 结束流
                yield "data: [DONE]\n\n"
                
    except httpx.TimeoutException:
        yield 'data: {"error": "Ollama request timeout"}\n\n'
    except httpx.RequestError as e:
        yield f'data: {{"error": "Ollama request failed: {str(e)}"}}\n\n'
    except Exception as e:
        yield f'data: {{"error": "{str(e)}"}}\n\n'


@app.get("/")
@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/version", timeout=5.0)
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "ollama": "connected",
                    "api": "openai-compatible"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "ollama": "disconnected",
            "error": str(e)
        }


# 保留FastAPI默认的文档接口
# FastAPI会自动生成/docs和/redoc端点用于API文档
# /docs - Swagger UI文档
# /redoc - ReDoc文档

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)