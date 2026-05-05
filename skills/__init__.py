"""
Sistema de Skills para Jitro Layer
Skills são capacidades extensíveis que podem ser carregadas dinamicamente
"""
from .base import Skill, SkillResult
from .loader import SkillLoader

__all__ = ["Skill", "SkillResult", "SkillLoader"]
