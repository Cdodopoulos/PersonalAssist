import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from config import MEMORY_DB_PATH

logger = logging.getLogger("jitro.database")

@contextmanager
def get_db_connection():
    """Context manager para conexões de banco - garante fechamento automático"""
    conn = sqlite3.connect(str(MEMORY_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_memory_db():
    """Inicializa as tabelas do banco de dados se não existirem"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Tabela de conversas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                model_used TEXT,
                latency REAL
            )
        ''')

        # Tabela de resumos de memória
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de uso de ferramentas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conversations_session
            ON conversations(session_id, timestamp DESC)
        ''')

        conn.commit()
        logger.info("Banco de dados de memória inicializado")

def store_conversation(session_id: str, prompt: str, response: str, model_used: str, latency: float):
    """Armazena uma interação na tabela conversations"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (session_id, prompt, response, model_used, latency)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, prompt, response, model_used, latency))
        conn.commit()

def get_conversation_history(session_id: str, limit: int = 10) -> List[Dict]:
    """Recupera o histórico recente de uma sessão"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT prompt, response, timestamp FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (session_id, limit))

        history = [
            {"prompt": row["prompt"], "response": row["response"], "timestamp": row["timestamp"]}
            for row in cursor.fetchall()
        ]

    return list(reversed(history))

def update_memory_summary(session_id: str, summary: str):
    """Atualiza ou cria o resumo de memória de uma sessão"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM memory_summary WHERE session_id = ?', (session_id,))

        if cursor.fetchone():
            cursor.execute('''
                UPDATE memory_summary
                SET summary = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (summary, session_id))
        else:
            cursor.execute('''
                INSERT INTO memory_summary (session_id, summary)
                VALUES (?, ?)
            ''', (session_id, summary))

        conn.commit()

def get_memory_summary(session_id: str) -> str:
    """Recupera o resumo de memória atual de uma sessão"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT summary FROM memory_summary WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        return row["summary"] if row else ""

def log_tool_usage(session_id: str, tool_name: str, input_data: str, output_data: str, success: bool = True):
    """Registra o uso de uma ferramenta no banco de dados"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tool_usage (session_id, tool_name, input_data, output_data, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, tool_name, input_data, output_data, success))
        conn.commit()

def get_session_stats(session_id: str) -> Dict[str, Any]:
    """Recupera estatísticas de uso de uma sessão específica"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM conversations WHERE session_id = ?', (session_id,))
        total_messages = cursor.fetchone()[0]

        cursor.execute('''
            SELECT tool_name, COUNT(*) as count FROM tool_usage
            WHERE session_id = ? GROUP BY tool_name
        ''', (session_id,))
        tool_stats = {row["tool_name"]: row["count"] for row in cursor.fetchall()}

    return {
        "total_messages": total_messages,
        "tool_usage_stats": tool_stats
    }

def clear_session_data(session_id: str) -> int:
    """Remove todos os dados associados a uma sessão"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM conversations WHERE session_id = ?', (session_id,))
        c1 = cursor.rowcount
        cursor.execute('DELETE FROM memory_summary WHERE session_id = ?', (session_id,))
        c2 = cursor.rowcount
        cursor.execute('DELETE FROM tool_usage WHERE session_id = ?', (session_id,))
        c3 = cursor.rowcount
        conn.commit()
        return c1 + c2 + c3
