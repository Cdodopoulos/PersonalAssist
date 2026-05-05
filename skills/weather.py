"""
Skill de Weather (Previsão do Tempo)
Usa API externa para obter previsão do tempo
"""
from typing import Dict, Any
from .base import Skill, SkillResult


class WeatherSkill(Skill):
    """Skill para consulta de previsão do tempo"""

    name = "weather"
    description = "Obtém previsão do tempo para uma cidade (requer API key configurada)"
    parameters = {
        "city": str
    }
    required_parameters = ["city"]

    def execute(self, params: Dict[str, Any], session_id: str = "default") -> SkillResult:
        import os
        import requests

        city = params.get("city", "")
        if not city:
            return SkillResult(
                success=False,
                data=None,
                error="Nome da cidade é obrigatório"
            )

        # API key da OpenWeatherMap (gratuita até 60 chamadas/min)
        # Usuário deve configurar no .env: WEATHER_API_KEY=xxx
        api_key = os.getenv("WEATHER_API_KEY", "")

        if not api_key or api_key == "SUA_API_KEY_AQUI":
            # Modo demo: retorna dados simulados
            return SkillResult(
                success=True,
                data={
                    "city": city,
                    "temperature": 25,
                    "condition": "Ensolarado",
                    "humidity": 60,
                    "demo": True
                },
                message=f"[Demo] {city}: 25°C, Ensolarado, 60% umidade",
            )

        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": api_key,
                    "units": "metric",
                    "lang": "pt"
                },
                timeout=10
            )

            if response.status_code == 404:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"Cidade não encontrada: {city}"
                )

            response.raise_for_status()
            data = response.json()

            weather_data = {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "condition": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"]
            }

            return SkillResult(
                success=True,
                data=weather_data,
                message=f"{weather_data['city']}: {weather_data['temperature']}°C, {weather_data['condition']}"
            )

        except requests.exceptions.Timeout:
            return SkillResult(
                success=False,
                data=None,
                error="Timeout ao consultar API do tempo"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=f"Erro ao obter previsão: {str(e)}"
            )
