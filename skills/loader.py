"""
Carregador dinâmico de skills
"""
import importlib
import logging
from pathlib import Path
from typing import Dict, Type, List

from .base import Skill

logger = logging.getLogger("jitro.skills")


class SkillLoader:
    """Gerencia carregamento e registro de skills"""

    def __init__(self, skills_dir: Path = None):
        self.skills_dir = skills_dir or Path(__file__).parent
        self._skills: Dict[str, Type[Skill]] = {}
        self._instances: Dict[str, Skill] = {}

    def load_all(self) -> int:
        """
        Carrega todas as skills do diretório.
        Retorna número de skills carregadas.
        """
        loaded = 0

        for file_path in self.skills_dir.glob("*.py"):
            if file_path.name in ("__init__.py", "base.py", "loader.py"):
                continue

            try:
                module_name = f"skills.{file_path.stem}"
                module = importlib.import_module(module_name)

                # Procura classe Skill no módulo
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, Skill)
                        and attr not in (Skill, JsonPersistableSkill)
                    ):
                        skill_instance = attr()
                        self._skills[skill_instance.name] = attr
                        self._instances[skill_instance.name] = skill_instance
                        logger.info(f"Skill carregada: {skill_instance.name}")
                        loaded += 1

            except Exception as e:
                logger.error(f"Erro ao carregar skill de {file_path.name}: {e}")

        logger.info(f"Total de skills carregadas: {loaded}")
        return loaded

    def get(self, name: str) -> Skill | None:
        """Obtém instância de uma skill por nome"""
        return self._instances.get(name)

    def list_available(self) -> List[Dict[str, str]]:
        """Lista todas as skills disponíveis"""
        return [
            {"name": name, "description": skill.description}
            for name, skill in self._skills.items()
        ]

    def execute(self, name: str, params: dict, session_id: str = "default"):
        """Executa uma skill por nome"""
        skill = self.get(name)
        if not skill:
            return None

        # Validar parâmetros
        is_valid, error = skill.validate_params(params)
        if not is_valid:
            return skill.execute.__func__(
                skill,
                params,
                session_id
            ).__class__(
                success=False,
                data=None,
                message="Validação falhou",
                error=error
            )

        return skill.execute(params, session_id)
