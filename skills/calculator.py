"""
Skill de Calculadora
Operações matemáticas básicas e avançadas
"""
import math
from typing import Dict, Any
from .base import Skill, SkillResult


class CalculatorSkill(Skill):
    """Skill para operações matemáticas"""

    name = "calculator"
    description = "Realiza operações matemáticas: soma, subtração, multiplicação, divisão, potência, raiz quadrada"
    parameters = {
        "operation": str,
        "a": (int, float),
        "b": (int, float)  # Opcional para algumas operações
    }

    def execute(self, params: Dict[str, Any], session_id: str = "default") -> SkillResult:
        operation = params.get("operation", "").lower()
        a = params.get("a", 0)
        b = params.get("b", 0)

        try:
            if operation == "soma" or operation == "add":
                result = a + b
            elif operation == "subtracao" or operation == "sub":
                result = a - b
            elif operation == "multiplicacao" or operation == "mul":
                result = a * b
            elif operation == "divisao" or operation == "div":
                if b == 0:
                    return SkillResult(
                        success=False,
                        data=None,
                        error="Divisão por zero não é permitida"
                    )
                result = a / b
            elif operation == "potencia" or operation == "pow":
                result = math.pow(a, b)
            elif operation == "raiz" or operation == "sqrt":
                if a < 0:
                    return SkillResult(
                        success=False,
                        data=None,
                        error="Não existe raiz quadrada real de número negativo"
                    )
                result = math.sqrt(a)
            elif operation == "modulo" or operation == "mod":
                if b == 0:
                    return SkillResult(
                        success=False,
                        data=None,
                        error="Módulo por zero não é permitido"
                    )
                result = a % b
            else:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"Operação desconhecida: {operation}"
                )

            return SkillResult(
                success=True,
                data={"result": result, "operation": operation, "a": a, "b": b},
                message=f"Resultado: {result}"
            )

        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Erro na calculadora: {str(e)}"
            )
