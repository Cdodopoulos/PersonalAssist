import logging
from datetime import datetime
from typing import List, Any
from skills.loader import SkillLoader

logger = logging.getLogger("jitro.tools")
skill_loader = SkillLoader()

def get_current_time():
    """Retorna a data e hora atual do sistema."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def weather_search(city: str):
    """Obtém a previsão do tempo atual para uma cidade específica."""
    result = skill_loader.execute("weather", {"city": city})
    return result.to_dict()

def calculator(operation: str, a: float, b: float = 0):
    """Realiza cálculos matemáticos: soma, subtracao, multiplicacao, divisao, potencia, raiz."""
    result = skill_loader.execute("calculator", {"operation": operation, "a": a, "b": b})
    return result.to_dict()

def google_search(query: str):
    """Busca informações em tempo real na internet sobre qualquer assunto."""
    result = skill_loader.execute("web_search", {"query": query, "max_results": 3})
    return result.to_dict()

def manage_agenda(action: str, task: str = None, index: int = None, date: str = None):
    """Gerencia lembretes e tarefas. Ações: 'add', 'list', 'list_today', 'remove'."""
    params = {"action": action}
    if task: params["task"] = task
    if index is not None: params["index"] = index
    if date: params["date"] = date
    result = skill_loader.execute("agenda", params)
    return result.to_dict()

def manage_notes(action: str, content: str = None, index: int = None, category: str = None):
    """Salva e recupera notas por categoria. Ações: 'save', 'list', 'delete'."""
    params = {"action": action}
    if content: params["content"] = content
    if index is not None: params["index"] = index
    if category: params["category"] = category
    result = skill_loader.execute("notes", params)
    return result.to_dict()

def sync_phone_calendar(action: str, summary: str = None, start_time: str = None):
    """Acessa a agenda real do Google. Ações: 'list_events', 'add_event'."""
    params = {"action": action}
    if summary: params["summary"] = summary
    if start_time: params["start_time"] = start_time
    result = skill_loader.execute("google_calendar", params)
    return result.to_dict()

def get_tools_list() -> List[Any]:
    """Retorna a lista de funções disponíveis para o Gemini"""
    return [
        get_current_time,
        weather_search,
        calculator,
        google_search,
        manage_agenda,
        manage_notes,
        sync_phone_calendar
    ]

def load_skills():
    """Inicializa o carregamento de todas as skills"""
    skill_loader.load_all()
