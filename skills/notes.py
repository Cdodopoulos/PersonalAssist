"""
Skill de Notas Rápidas
Refatorada com JsonPersistableSkill para remover duplicidade de código.
"""
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from .base import JsonPersistableSkill, SkillResult
import config

class NotesSkill(JsonPersistableSkill):
    """Skill para salvar e ler notas rápidas"""

    name = "notes"
    description = "Salva e recupera notas organizadas por categorias. Ações: save, list, delete"
    parameters = {
        "action": str,
        "content": str,
        "category": str,
        "index": int
    }

    def __init__(self):
        # Usa o diretório base das configurações para o arquivo
        file_path = config.BASE_DIR / "notes.json"
        super().__init__(str(file_path))

    def execute(self, params: Dict[str, Any], session_id: str = "default") -> SkillResult:
        action = params.get("action", "").lower()
        
        handlers = {
            "save": self._save_note,
            "list": self._list_notes,
            "delete": self._delete_note
        }
        
        handler = handlers.get(action)
        if not handler:
            return SkillResult(False, None, f"Ação '{action}' não reconhecida.")
            
        return handler(params, session_id)

    def _save_note(self, params: Dict, session_id: str) -> SkillResult:
        content = params.get("content", "")
        if not content:
            return SkillResult(False, None, "Conteúdo da nota não pode estar vazio.")
            
        category = params.get("category", "Geral").capitalize()
        notes = self._load_data()
        
        new_note = {
            "content": content, 
            "category": category,
            "session_id": session_id, 
            "date": datetime.now().isoformat()
        }
        
        notes.append(new_note)
        self._save_data(notes)
        return SkillResult(True, new_note, f"Nota salva com sucesso em '{category}'!")

    def _list_notes(self, params: Dict, session_id: str) -> SkillResult:
        notes = self._load_data()
        user_notes = [n for n in notes if n.get("session_id") == session_id]
        
        category_filter = params.get("category")
        if category_filter:
            user_notes = [n for n in user_notes if n.get("category").lower() == category_filter.lower()]
            msg = f"Encontradas {len(user_notes)} notas na categoria '{category_filter}'."
        else:
            msg = f"Encontradas {len(user_notes)} notas ao todo."
            
        return SkillResult(True, user_notes, msg)

    def _delete_note(self, params: Dict, session_id: str) -> SkillResult:
        index = params.get("index")
        notes = self._load_data()
        
        # Mapeia os índices globais que pertencem a este usuário
        user_indices = [i for i, n in enumerate(notes) if n.get("session_id") == session_id]
        
        if index is not None and 0 <= index < len(user_indices):
            removed = notes.pop(user_indices[index])
            self._save_data(notes)
            return SkillResult(True, removed, "Nota excluída com sucesso.")
            
        return SkillResult(False, None, "Índice da nota inválido.")
