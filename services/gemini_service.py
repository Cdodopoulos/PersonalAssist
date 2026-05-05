import logging
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

import config
from infrastructure import database

logger = logging.getLogger("jitro.gemini")

if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        self.priority_models = config.MODELS_PRIORITY

    def call_gemini(self, prompt: str, tools_list: List[Any] = None) -> dict:
        """
        Faz a chamada ao Gemini com redundância (Fallback automático).
        Tenta os modelos da lista de prioridade um por um.
        """
        if not config.GEMINI_API_KEY:
            raise HTTPException(status_code=503, detail="Gemini API Key não configurada.")

        last_error = None
        system_instruction = (
            "Você é o Jitro, um assistente pessoal inteligente e proativo. "
            "Você tem acesso a ferramentas reais para gerenciar a vida do usuário. "
            "Quando o usuário pedir para ver compromissos, pesquisar na web, calcular algo ou salvar notas, "
            "USE AS FERRAMENTAS DISPONÍVEIS imediatamente sem dar desculpas. "
            "Sua resposta deve ser útil, concisa e natural."
        )

        for model_name in self.priority_models:
            try:
                logger.info(f"Tentando gerar conteúdo com o modelo: {model_name}")
                
                model = genai.GenerativeModel(
                    model_name=model_name,
                    tools=tools_list,
                    system_instruction=system_instruction
                )
                
                chat = model.start_chat(enable_automatic_function_calling=True)
                response = chat.send_message(prompt)
                
                if response.text:
                    logger.info(f"Sucesso com o modelo: {model_name}")
                    return {"response": response.text, "model_used": model_name}
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Falha no modelo {model_name}: {last_error}")
                # Continua para o próximo modelo na lista
                continue

        # Se todos falharem
        logger.error(f"Todos os modelos falharam. Último erro: {last_error}")
        raise HTTPException(
            status_code=502, 
            detail=f"Todos os modelos de IA falharam ou excederam a quota. Erro: {last_error}"
        )

    def generate_session_summary(self, session_id: str, history: List[Dict]):
        """Gera um resumo usando o primeiro modelo disponível da lista"""
        if not history: return

        summary_prompt = "Resuma de forma concisa o histórico de conversa:\n\n"
        for conv in history[-10:]:
            summary_prompt += f"U: {conv['prompt']}\nA: {conv['response']}\n\n"

        for model_name in self.priority_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(summary_prompt)
                summary_text = response.text.strip()
                if summary_text:
                    database.update_memory_summary(session_id, summary_text)
                    return
            except:
                continue
