# 🤖 Jitro Assistant v2.0 - Nuvem

Este é um assistente de IA autônomo e pessoal, integrado ao Telegram e alimentado pela API do Google Gemini. O projeto utiliza o framework Jitro Layer para gerenciar memória persistente e execução de ferramentas.

## 🚀 Funcionalidades
- **Memória Persistente:** O assistente lembra de conversas passadas usando um banco SQLite.
- **Integração com Telegram:** Comunicação fluida via bot.
- **Cérebro na Nuvem:** Utiliza o Google Gemini (1.5 Flash/Pro) para respostas rápidas e inteligentes.
- **Skills System:** Capacidade de expandir as funções do assistente através de módulos.

## 🛠️ Tecnologias
- **Linguagem:** Python 3.10+
- **API Framework:** FastAPI
- **IA:** Google Generative AI (Gemini)
- **Database:** SQLite3

## ⚙️ Instalação e Deploy
Este projeto está configurado para ser hospedado no **Render.com**. 

### Configuração
1. Copie o arquivo `.env.example` para `.env`.
2. Preencha as variáveis:
   - `TELEGRAM_BOT_TOKEN`: Token do seu bot via @BotFather.
   - `GEMINI_API_KEY`: Sua chave do Google AI Studio.
   - `MODEL_NAME`: `gemini-1.5-flash` ou `gemini-1.5-pro`.

### Execução Local
```bash
pip install -r requirements.txt
python start_assistant_v2.py
```

## 🛡️ Segurança
O arquivo `.env` está no `.gitignore` para evitar o vazamento de chaves de API. Nunca suba suas chaves para repositórios públicos.

---
Desenvolvido com foco em autonomia e eficiência.
