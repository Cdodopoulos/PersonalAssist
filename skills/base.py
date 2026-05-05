"""
Classe base para todas as skills
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SkillResult:
    """Resultado padronizado de execução de skill"""
    success: bool
    data: Any
    message: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "timestamp": datetime.now().isoformat()
        }


class Skill(ABC):
    """
    Classe abstrata base para skills.
    Todas as skills devem herdar desta classe e implementar execute().
    """

    # Nome único da skill (usado para chamá-la)
    name: str = "base_skill"

    # Descrição do que a skill faz (para descoberta)
    description: str = "Skill base"

    # Parâmetros esperados (para validação)
    parameters: Dict[str, type] = {}

    # Se requer sessão (padrão: True)
    requires_session: bool = True

    @abstractmethod
    def execute(self, params: Dict[str, Any], session_id: str = "default") -> SkillResult:
        """
        Executa a skill com os parâmetros fornecidos.

        Args:
            params: Dicionário de parâmetros
            session_id: ID da sessão atual

        Returns:
            SkillResult com o resultado da execução
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """
        Valida os parâmetros contra o esperado.

        Returns:
            (é_válido, mensagem_de_erro)
        """
        for param_name, param_type in self.parameters.items():
            if param_name not in params:
                return False, f"Parâmetro '{param_name}' é obrigatório"

            if not isinstance(params[param_name], param_type):
                return False, f"Parâmetro '{param_name}' deve ser do tipo {param_type.__name__}"

        return True, ""


class JsonPersistableSkill(Skill):
    """
    Skill que automatiza a persistência de dados em arquivos JSON.
    Resolve o 'Bad Smell' de Código Duplicado em skills de armazenamento simples.
    """
    def __init__(self, file_path: str):
        import json
        from pathlib import Path
        self.json = json
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.file_path.exists():
            self._save_data([])

    def _load_data(self) -> list:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return self.json.load(f)
        except Exception:
            return []

    def _save_data(self, data: list):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            self.json.dump(data, f, indent=2, ensure_ascii=False)
