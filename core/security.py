import re
import logging
from typing import Tuple
from config import MAX_PROMPT_LENGTH

logger = logging.getLogger("jitro.security")

def validate_prompt(prompt: str) -> Tuple[bool, str]:
    """
    Valida o prompt contra padrões perigosos e limites de tamanho.
    Retorna (é_válido, mensagem_de_erro)
    """
    if not prompt or not prompt.strip():
        return False, "Prompt vazio não é permitido"

    if len(prompt) > MAX_PROMPT_LENGTH:
        return False, f"Prompt muito longo (máximo: {MAX_PROMPT_LENGTH} caracteres)"

    # Detectar tentativas de prompt injection
    injection_patterns = [
        r"ignore\s+previous\s+instructions",
        r"ignore\s+all\s+prior",
        r"forget\s+all\s+instructions",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"system\s*:",
        r"<system>",
        r"\[system\]",
        r"dan\s*=",
        r"do\s+not\s+follow\s+your\s+guidelines",
    ]

    prompt_lower = prompt.lower()
    for pattern in injection_patterns:
        if re.search(pattern, prompt_lower):
            logger.warning(f"Tentativa de prompt injection detectada: {pattern}")
            return False, "Conteúdo do prompt não permitido por motivos de segurança"

    return True, ""
