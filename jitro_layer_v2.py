"""
Jitro Layer v2 - API Gateway para Assistente IA
Versão Refatorada (Arquitetura Limpa)
"""
import time
import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

import config
from infrastructure import database
from services import gemini_service, file_service, tool_manager
from core import security

# =============================================================================
# INICIALIZAÇÃO DE COMPONENTES
# =============================================================================
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("jitro")

# Instancia serviços
gemini = gemini_service.GeminiService()
files = file_service.FileService(config.BASE_DIR, config.ALLOWED_FILE_EXTENSIONS)

app = FastAPI(
    title="Jitro Layer API",
    description="Gateway para assistente IA com arquitetura modular",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Ajustar para produção se necessário
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# MODELOS DE DADOS
# =============================================================================
class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    session_id: str = Field(default="default")
    use_memory: bool = Field(default=True)
    max_context_length: int = Field(default=5, ge=1, le=20)

    @validator('prompt')
    def validate_prompt_content(cls, v):
        is_valid, error = security.validate_prompt(v)
        if not is_valid:
            raise ValueError(error)
        return v

class ToolRequest(BaseModel):
    tool_name: str
    parameters: dict = Field(default={})
    session_id: str = Field(default="default")

# =============================================================================
# ENDPOINTS
# =============================================================================
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.1.0",
        "model": config.MODEL_NAME,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/generate")
async def generate(request: ChatRequest):
    """Gera resposta usando Gemini com contexto de memória"""
    start_time = time.time()
    session_id = request.session_id

    # 1. Recuperar contexto da memória
    context_messages = []
    if request.use_memory:
        history = database.get_conversation_history(session_id, request.max_context_length)
        for conv in history:
            context_messages.append(f"Usuário: {conv['prompt']}")
            context_messages.append(f"Assistente: {conv['response']}")

        summary = database.get_memory_summary(session_id)
        if summary:
            context_messages.insert(0, f"Contexto: {summary}")

    context_messages.append(f"Usuário: {request.prompt}")
    full_prompt = "\n".join(context_messages)

    # 2. Chamar LLM
    data = gemini.call_gemini(full_prompt, tool_manager.get_tools_list())
    
    latency = time.time() - start_time
    response_text = data.get("response", "")

    # 3. Persistência e Logs
    database.store_conversation(session_id, request.prompt, response_text, config.MODEL_NAME, latency)
    
    # 4. Gerenciamento de Memória Periódico
    stats = database.get_session_stats(session_id)
    if stats["total_messages"] % config.SUMMARY_INTERVAL == 0:
        history = database.get_conversation_history(session_id, 10)
        gemini.generate_session_summary(session_id, history)

    return {
        "response": response_text,
        "latency": round(latency, 2),
        "session_id": session_id,
        "success": True
    }

@app.post("/tool/use")
async def use_tool(request: ToolRequest):
    """Executa ferramentas de sistema e arquivos"""
    start_time = time.time()
    session_id = request.session_id
    tool_name = request.tool_name
    params = request.parameters

    result = None
    success = True

    try:
        if tool_name == "current_time":
            result = datetime.now().isoformat()
        
        elif tool_name == "file_read":
            result = files.read_file(params.get("path", ""))
            
        elif tool_name == "file_write":
            result = files.write_file(params.get("path", ""), params.get("content", ""))
            
        elif tool_name == "list_files":
            result = "\n".join(files.list_files(params.get("path", ".")))
            
        else:
            result = f"Ferramenta desconhecida: {tool_name}"
            success = False

        latency = time.time() - start_time
        database.log_tool_usage(session_id, tool_name, json.dumps(params), str(result), success)

        return {
            "result": result,
            "latency": round(latency, 2),
            "success": success
        }

    except Exception as e:
        logger.error(f"Erro na ferramenta {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{session_id}")
async def get_memory(session_id: str):
    return {
        "session_id": session_id,
        "conversation_history": database.get_conversation_history(session_id, 20),
        "memory_summary": database.get_memory_summary(session_id),
        **database.get_session_stats(session_id)
    }

@app.delete("/memory/{session_id}")
async def clear_memory(session_id: str):
    count = database.clear_session_data(session_id)
    return {"message": f"Dados limpos", "deleted_records": count}

# =============================================================================
# LIFECYCLE
# =============================================================================
@app.on_event("startup")
async def startup():
    logger.info("Iniciando Jitro Layer v2.1.0...")
    database.init_memory_db()
    tool_manager.load_skills()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.JITRO_PORT)
