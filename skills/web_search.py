"""
Skill de Busca Web
Busca informações na internet usando DuckDuckGo (sem API key necessária)
"""
from typing import Dict, Any
from .base import Skill, SkillResult


class WebSearchSkill(Skill):
    """Skill para busca na web usando DuckDuckGo"""

    name = "web_search"
    description = "Busca informações na web usando DuckDuckGo"
    parameters = {
        "query": str,
        "max_results": int
    }

    def execute(self, params: Dict[str, Any], session_id: str = "default") -> SkillResult:
        query = params.get("query", "")
        max_results = params.get("max_results", 5)

        if not query:
            return SkillResult(
                success=False,
                data=None,
                error="Query de busca é obrigatória"
            )

        try:
            # DuckDuckGo Search (biblioteca que não requer API key)
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            formatted_results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]

            if not formatted_results:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"A busca por '{query}' não retornou resultados no momento."
                )

            return SkillResult(
                success=True,
                data=formatted_results,
                message=f"Encontrados {len(formatted_results)} resultados para '{query}'."
            )

        except ImportError:
            return SkillResult(
                success=False,
                data=None,
                error="duckduckgo_search não instalada. Execute: pip install duckduckgo-search"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Erro na busca: {str(e)}"
            )
