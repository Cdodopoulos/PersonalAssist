"""
Configurações centralizadas da Jitro Layer
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Diretório base
BASE_DIR = Path(__file__).parent

# Configurações do Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
MODELS_PRIORITY = [
    MODEL_NAME,
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-2.0-pro"
]

# Configurações da API
JITRO_PORT = int(os.getenv("PORT", os.getenv("JITRO_PORT", 8000)))
HOST = os.getenv("JITRO_HOST", "0.0.0.0")

# Configurações de memória
MEMORY_DB_PATH = Path(os.getenv("MEMORY_DB_PATH", BASE_DIR / "jitro_memory.db"))

# Timeout para requests (segundos)
GENERATE_TIMEOUT = int(os.getenv("GENERATE_TIMEOUT", 120))

# Limites e thresholds
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", 10))
LATENCY_WARNING_THRESHOLD = float(os.getenv("LATENCY_WARNING_THRESHOLD", 2.0))
SUMMARY_INTERVAL = int(os.getenv("SUMMARY_INTERVAL", 5))  # Gera resumo a cada N mensagens

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Rate limiting (requisições por minuto por sessão)
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 30))

# Segurança
MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", 10000))
ALLOWED_FILE_EXTENSIONS = {".txt", ".md", ".json", ".py", ".js", ".ts", ".log"}

# Telegram (opcional)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "SEU_TOKEN_AQUI")
