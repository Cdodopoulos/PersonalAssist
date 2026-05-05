import logging
from pathlib import Path
from typing import List, Optional
import config

logger = logging.getLogger("jitro.file_service")

class FileService:
    def __init__(self, base_dir: Path, allowed_extensions: set):
        self.base_dir = base_dir.resolve()
        self.allowed_extensions = allowed_extensions

    def _validate_path(self, file_path: str) -> Path:
        """Valida se o caminho está dentro do diretório base e é seguro"""
        path_obj = Path(file_path).resolve()
        if not str(path_obj).startswith(str(self.base_dir)):
            raise ValueError("Acesso negado: Tentativa de acessar arquivo fora do diretório permitido.")
        return path_obj

    def read_file(self, file_path: str) -> str:
        """Lê o conteúdo de um arquivo de texto"""
        path_obj = self._validate_path(file_path)
        
        if not path_obj.exists() or not path_obj.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        if path_obj.suffix.lower() not in self.allowed_extensions:
            raise ValueError(f"Extensão não permitida: {path_obj.suffix}")
            
        with open(path_obj, 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, file_path: str, content: str) -> str:
        """Escreve conteúdo em um arquivo"""
        path_obj = self._validate_path(file_path)
        
        # Cria diretórios se necessário
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path_obj, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Arquivo escrito com sucesso: {file_path}"

    def list_files(self, dir_path: str = ".") -> List[str]:
        """Lista arquivos em um diretório"""
        path_obj = self._validate_path(dir_path)
        
        if not path_obj.is_dir():
            raise ValueError(f"O caminho não é um diretório: {dir_path}")
            
        return [f.name for f in path_obj.iterdir() if not f.name.startswith('.')]
