"""
Skill de Integração com Google Calendar
Permite sincronizar com a agenda real do celular
"""
import os
import datetime
from typing import Dict, Any, List
from .base import Skill, SkillResult

# Importações do Google (serão usadas se as credenciais existirem)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.generativeai.types import content_types
    from googleapiclient.discovery import build
    GOOGLE_SDK_AVAILABLE = True
except ImportError:
    GOOGLE_SDK_AVAILABLE = False

class GoogleCalendarSkill(Skill):
    """Skill para ler e escrever no Google Calendar (Agenda do Celular)"""

    name = "google_calendar"
    description = "Acessa a agenda real do Google (sincronizada com o celular). Ações: list_events, add_event"
    parameters = {
        "action": str,       # list_events, add_event
        "summary": str,      # título do evento
        "start_time": str,   # ISO format ou descrição
        "end_time": str      # ISO format
    }
    required_parameters = ["action"]

    def __init__(self):
        self.creds_file = "token.json" # Token de acesso gerado após o primeiro login
        self.client_secret_file = "credentials.json" # Arquivo que o usuário baixa do Google Cloud

    def _get_service(self):
        """Autentica e retorna o serviço do Google Calendar"""
        if not GOOGLE_SDK_AVAILABLE:
            return None
            
        creds = None
        if os.path.exists(self.creds_file):
            creds = Credentials.from_authorized_user_file(self.creds_file, ['https://www.googleapis.com/auth/calendar'])
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                return None # Requer nova autenticação manual inicial

        return build('calendar', 'v3', credentials=creds)

    def execute(self, params: Dict[str, Any], session_id: str = "default") -> SkillResult:
        service = self._get_service()
        if not service:
            return SkillResult(
                False, None, 
                "Integração com Google Agenda não configurada ou token expirado."
            )

        action = params.get("action", "").lower()
        handlers = {
            "list_events": self._list_events,
            "add_event": self._add_event
        }
        
        handler = handlers.get(action)
        if not handler:
            return SkillResult(False, None, f"Ação '{action}' não suportada no Google Calendar.")
            
        return handler(service, params)

    def _list_events(self, service, params: Dict) -> SkillResult:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=10, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return SkillResult(True, events, f"Você tem {len(events)} eventos agendados em breve.")

    def _add_event(self, service, params: Dict) -> SkillResult:
        summary = params.get("summary")
        start_time = params.get("start_time")
        if not summary or not start_time:
            return SkillResult(False, None, "Título e horário de início são obrigatórios.")
            
        # Implementação básica de criação de evento
        event = {
            'summary': summary,
            'start': {'dateTime': start_time},
            'end': {'dateTime': params.get("end_time", start_time)} # Fallback simples
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        return SkillResult(True, event, f"Evento '{summary}' criado com sucesso!")
