"""
Skill de Agenda/Lembretes
Refatorada com JsonPersistableSkill para remover duplicidade de código.
"""
from datetime import datetime
from typing import Dict, Any, List
from .base import JsonPersistableSkill, SkillResult
import config

class AgendaSkill(JsonPersistableSkill):
    """Skill para gerenciar lembretes e compromissos"""

    name = "agenda"
    description = "Gerencia lembretes e compromissos com suporte a datas. Ações: add, list, remove, list_today"
    parameters = {
        "action": str,
        "task": str,
        "date": str,
        "index": int
    }

    def __init__(self):
        file_path = config.BASE_DIR / "reminders.json"
        super().__init__(str(file_path))

    def execute(self, params: Dict[str, Any], session_id: str = "default") -> SkillResult:
        action = params.get("action", "").lower()
        
        handlers = {
            "add": self._add_task,
            "list": self._list_tasks,
            "list_today": self._list_tasks,
            "remove": self._remove_task,
            "clear": self._clear_all
        }
        
        handler = handlers.get(action)
        if not handler:
            return SkillResult(False, None, f"Ação '{action}' não suportada pela Agenda.")
            
        return handler(params, session_id)

    def _add_task(self, params: Dict, session_id: str) -> SkillResult:
        task = params.get("task", "")
        if not task:
            return SkillResult(False, None, "A descrição da tarefa é obrigatória.")
            
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        reminders = self._load_data()
        
        new_item = {
            "task": task, 
            "date": date, 
            "session_id": session_id, 
            "created_at": datetime.now().isoformat()
        }
        
        reminders.append(new_item)
        self._save_data(reminders)
        return SkillResult(True, new_item, f"Tarefa agendada: {task} para {date}")

    def _list_tasks(self, params: Dict, session_id: str) -> SkillResult:
        action = params.get("action", "").lower()
        reminders = self._load_data()
        
        # Filtro básico por usuário
        user_tasks = [r for r in reminders if r.get("session_id") == session_id]
        
        if action == "list_today":
            today = datetime.now().strftime("%Y-%m-%d")
            user_tasks = [r for r in user_tasks if r.get("date") == today]
            msg = f"Você tem {len(user_tasks)} compromissos para hoje."
        else:
            msg = f"Você tem {len(user_tasks)} compromissos agendados."
            
        return SkillResult(True, user_tasks, msg)

    def _remove_task(self, params: Dict, session_id: str) -> SkillResult:
        index = params.get("index")
        reminders = self._load_data()
        
        user_indices = [i for i, r in enumerate(reminders) if r.get("session_id") == session_id]
        
        if index is not None and 0 <= index < len(user_indices):
            removed = reminders.pop(user_indices[index])
            self._save_data(reminders)
            return SkillResult(True, removed, "Tarefa removida com sucesso.")
            
        return SkillResult(False, None, "Índice de tarefa inválido.")

    def _clear_all(self, params: Dict, session_id: str) -> SkillResult:
        # Nota: Por segurança, limpa apenas as tarefas da sessão atual
        reminders = self._load_data()
        original_count = len(reminders)
        reminders = [r for r in reminders if r.get("session_id") != session_id]
        
        self._save_data(reminders)
        deleted_count = original_count - len(reminders)
        return SkillResult(True, None, f"Foram removidas {deleted_count} tarefas da sua sessão.")
