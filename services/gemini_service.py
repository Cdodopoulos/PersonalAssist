import logging
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

import config
from config import GEMINI_API_KEY, MODEL_NAME
from infrastructure import database

logger = logging.getLogger("jitro.gemini")

# Configura o SDK
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        self.model_name = MODEL_NAME
        self.clean_model_name = MODEL_NAME.split('/')[-1]

    def call_gemini(self, prompt: str, tools_list: List[Any] = None) -> dict:
        """Faz a chamada principal ao Gemini com suporte a ferramentas"""
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=503, detail="Gemini API Key não configurada.")

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=tools_list
            )
            
            # Chat com suporte a chamadas automáticas de função
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(prompt)
            
            return {"response": response.text}
        except Exception as e:
            logger.error(f"Erro no Gemini Service: {e}")
            # Fallback para texto puro se ferramentas falharem
            try:
                model_basic = genai.GenerativeModel(self.clean_model_name)
                response = model_basic.generate_content(prompt)
                return {"response": response.text}
            except Exception as inner_e:
                logger.error(f"Erro no Fallback do Gemini: {inner_e}")
                raise HTTPException(status_code=502, detail=f"Erro na API Gemini: {str(e)}")

    def generate_session_summary(self, session_id: str, history: List[Dict]):
        """Gera um resumo do histórico de conversa e salva no DB"""
        if not history:
            return

        summary_prompt = "Resuma de forma concisa o seguinte histórico de conversa:\n\n"
        for conv in history[-10:]:
            summary_prompt += f"Usuário: {conv['prompt']}\nAssistente: {conv['response']}\n\n"

        try:
            model = genai.GenerativeModel(self.clean_model_name)
            response = model.generate_content(summary_prompt)
            
            summary_text = response.text.strip()
            if summary_text:
                database.update_memory_summary(session_id, summary_text)
        except Exception as e:
            logger.error(f"Erro ao gerar resumo automático: {e}")
