#!/usr/bin/env python3
"""
Launcher para Jitro Assistant v2
Verifica dependências, ambiente e inicia o servidor
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Configura stdout para UTF-8 para suportar caracteres Unicode no Windows
if sys.platform == 'win32' and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Cores para output (Windows 10+ suporta ANSI)
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text: str):
    print(f"{Colors.BLUE}→ {text}{Colors.RESET}")


def check_gemini() -> bool:
    """Verifica se a chave da API do Gemini está configurada"""
    import os
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        print_error("GEMINI_API_KEY não encontrada no arquivo .env")
        print_info("Pegue sua chave grátis em: aistudio.google.com")
        return False
    print_success("Chave do Gemini configurada")
    return True


def check_environment() -> bool:
    """Verifica configuração do ambiente"""
    # Na nuvem (Render/Railway), as variáveis já vêm no sistema.
    # Se elas já existem, não precisamos do arquivo .env.
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    if gemini_key and telegram_token:
        print_success("Configurações detectadas via Variáveis de Ambiente")
        return True

    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists():
        print_warning("Arquivo .env não encontrado")

        if env_example.exists():
            print_info("Criando .env a partir de .env.example...")
            with open(env_example, 'r', encoding='utf-8') as f:
                content = f.read()

            with open(".env", 'w', encoding='utf-8') as f:
                f.write(content)

            print_success(".env criado.")
            return False  # Localmente, ainda queremos que o usuário edite o .env
        else:
            print_error("Nem .env nem .env.example encontrados")
            return False

    # Carregar variáveis de ambiente do arquivo
    from dotenv import load_dotenv
    load_dotenv()
    print_success("Variáveis de ambiente do arquivo .env carregadas")
    return True


def install_dependencies() -> bool:
    """Na nuvem, as dependências são instaladas via requirements.txt automaticamente."""
    return True


def check_database() -> bool:
    """Verifica/inicializa banco de dados"""
    try:
        from infrastructure.database import init_memory_db
        init_memory_db()
        print_success("Banco de dados verificado/inicializado")
        return True
    except Exception as e:
        print_error(f"Erro ao inicializar banco de dados: {e}")
        return False


def load_skills() -> int:
    """Carrega sistema de skills"""
    try:
        from skills.loader import SkillLoader
        loader = SkillLoader()
        count = loader.load_all()
        print_success(f"{count} skills carregadas")
        return count
    except Exception as e:
        print_warning(f"Erro ao carregar skills: {e}")
        return 0


def show_startup_info():
    """Exibe informações de inicialização"""
    from config import JITRO_PORT, MODEL_NAME, TELEGRAM_ENABLED

    print_header("Jitro Assistant v2.0 - Pronto para uso")

    print_info(f"API disponível em: http://localhost:{JITRO_PORT}")
    print_info(f"Health check: http://localhost:{JITRO_PORT}/health")
    print_info(f"Documentação: http://localhost:{JITRO_PORT}/docs")
    print_info(f"Modelo: {MODEL_NAME}")

    if TELEGRAM_ENABLED:
        print_success("Bot do Telegram HABILITADO")
    else:
        print_warning("Bot do Telegram DESABILITADO (configure TOKEN no .env)")

    print_info("\nComandos úteis:")
    print_info("  - Testar API: curl http://localhost:8000/health")
    print_info("  - Ver logs: arquivo gateway.log")
    print_info("  - Parar: Ctrl+C")

    print(f"\n{Colors.GREEN}{'=' * 60}{Colors.RESET}")


def main() -> int:
    """Função principal"""
    print_header("Jitro Assistant v2.0 - Inicialização")

    # Mudar para diretório do script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # 1. Verificar ambiente
    if not check_environment():
        print_error("\nConfiguração incompleta. Edite .env e execute novamente.")
        return 1

    # 2. Verificar Gemini
    if not check_gemini():
        print_warning("\nAPI do Gemini não configurada. A API iniciará mas falhará ao gerar respostas.")

    # 4. Verificar banco de dados
    check_database()

    # 5. Carregar skills
    load_skills()

    # 6. Mostrar informações
    show_startup_info()

    # 7. Iniciar servidor
    print_info("Iniciando servidor...\n")

    try:
        from jitro_layer_v2 import app
        import uvicorn
        from config import JITRO_PORT, HOST, TELEGRAM_ENABLED
        
        telegram_process = None
        if TELEGRAM_ENABLED:
            print_info("Iniciando bot do Telegram em background...")
            telegram_process = subprocess.Popen([sys.executable, "telegram_bot.py"])

        uvicorn.run(app, host=HOST, port=JITRO_PORT)
        
        if telegram_process:
            telegram_process.terminate()
            
        return 0

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Servidor encerrado pelo usuário{Colors.RESET}")
        if 'telegram_process' in locals() and telegram_process:
            telegram_process.terminate()
        return 0
    except Exception as e:
        print_error(f"Erro ao iniciar servidor: {e}")
        if 'telegram_process' in locals() and telegram_process:
            telegram_process.terminate()
        return 1


if __name__ == "__main__":
    sys.exit(main())
