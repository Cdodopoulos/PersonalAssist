#!/usr/bin/env python3
"""
Telegram Bot for Jitro Assistant
Connects Telegram to the Enhanced Jitro Layer API
"""

import os
import httpx
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from config import JITRO_PORT
# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
JITRO_API_URL = os.getenv("JITRO_API_URL", f"http://localhost:{JITRO_PORT}")

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
    exit(1)

class JitroApiClient:
    """Cliente assíncrono para a API Jitro Layer"""
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    async def generate_response(self, prompt: str, session_id: str) -> dict:
        """Chama o endpoint /generate"""
        payload = {
            "prompt": prompt,
            "session_id": session_id,
            "use_memory": True,
            "max_context_length": 5
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/generate", json=payload)
            response.raise_for_status()
            return response.json()

    async def get_stats(self, session_id: str) -> dict:
        """Chama o endpoint /memory/{session_id}"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/memory/{session_id}")
            response.raise_for_status()
            return response.json()

    async def clear_memory(self, session_id: str) -> bool:
        """Chama o endpoint DELETE /memory/{session_id}"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(f"{self.base_url}/memory/{session_id}")
            return response.status_code == 200

class JitroTelegramBot:
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.api_client = JitroApiClient(JITRO_API_URL)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup command and message handlers"""
        # Commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("clear", self.clear_memory))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        
        # Messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_html(
            rf"Hi {user.mention_html()}! 👋",
            reply_markup=ForceReply(selective=True),
        )
        await update.message.reply_text(
            "I'm your Jitro Assistant! I have memory and can help you with various tasks.\n\n"
            "Commands:\n"
            "/help - Show this help message\n"
            "/clear - Clear our conversation memory\n"
            "/stats - Show conversation statistics\n\n"
            "Just send me any message and I'll respond using AI with memory!"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        help_text = """
🤖 *Jitro Assistant Help*

*Basic Usage:*
Just send me any message and I'll respond using AI with persistent memory!

*Commands:*
/start - Start the bot and see welcome message
/help - Show this help message
/clear - Clear our conversation memory
/stats - Show conversation statistics

*Features:*
• Persistent conversation memory
• Context-aware responses
• Session-based memory isolation
• Tool usage capabilities (coming soon)

*Example:*
You: "What's the capital of France?"
Me: "The capital of France is Paris."
You: "What language do they speak there?"
Me: "In Paris, they speak French."

Send me a message to get started!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def clear_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear conversation memory for this user."""
        user_id = str(update.effective_user.id)
        try:
            success = await self.api_client.clear_memory(user_id)
            if success:
                await update.message.reply_text("🧹 Memória da conversa limpa com sucesso!")
            else:
                await update.message.reply_text("❌ Falha ao limpar a memória.")
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            await update.message.reply_text("❌ Erro ao conectar com o servidor.")
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show conversation statistics."""
        user_id = str(update.effective_user.id)
        try:
            data = await self.api_client.get_stats(user_id)
            history_count = len(data.get('conversation_history', []))
            summary = data.get('memory_summary', 'Ainda não há resumo disponível.')
            
            stats_text = f"""
📊 *Estatísticas da Conversa*

*ID do Usuário:* {user_id}
*Mensagens trocadas:* {history_count}
*Resumo da Memória:* {summary[:200]}{'...' if len(summary) > 200 else ''}
*Data:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            await update.message.reply_text(stats_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text("❌ Erro ao recuperar estatísticas.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler principal de mensagens com lógica de retentativas assíncrona."""
        user_id = str(update.effective_user.id)
        user_message = update.message.text
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await self.api_client.generate_response(user_message, user_id)
                ai_response = result.get("response", "Desculpe, não consegui gerar uma resposta.")
                await self._send_long_message(update, ai_response)
                return

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Falha de conexão (tentativa {attempt + 1}). Tentando em {wait_time}s... Error: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    await update.message.reply_text(
                        "❌ O servidor está instável ou demorando muito para responder. "
                        "Por favor, tente novamente em alguns instantes."
                    )
            except httpx.HTTPStatusError as e:
                error_detail = "Erro interno do servidor"
                try:
                    error_detail = e.response.json().get('detail', error_detail)
                except: pass
                
                logger.error(f"API HTTP Error: {e.response.status_code} - {error_detail}")
                await update.message.reply_text(f"❌ Erro na API: {error_detail}")
                return
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await update.message.reply_text("❌ Ocorreu um erro inesperado no bot.")
                return

    async def _send_long_message(self, update: Update, text: str):
        """Envia mensagens longas dividindo em blocos de 4000 caracteres."""
        if not text:
            return
            
        if len(text) <= 4000:
            await update.message.reply_text(text)
        else:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
                await asyncio.sleep(0.5) # Pequena pausa entre chunks
    
    def run(self):
        """Start the bot."""
        logger.info("Starting Jitro Telegram Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Start the bot."""
    bot = JitroTelegramBot()
    bot.run()

if __name__ == '__main__':
    main()