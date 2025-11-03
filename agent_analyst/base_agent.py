import json
from pathlib import Path
from typing import Dict, Any

class BaseAgent:
    """
    Agente base que fornece funcionalidades comuns para outros agentes,
    como carregar arquivos de configuração JSON e normalizar CFOPs.
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def _carregar_json(self, path: Path, key: str = None) -> Dict:
        """
        Carrega um arquivo JSON de forma segura.
        Retorna um dicionário vazio em caso de erro.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(key) if key else data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Erro ao carregar o arquivo de configuração {path.name}: {e}")
            return {}

    def _normalize_cfop(self, cfop_str: str) -> str:
        """
        Garante que o CFOP esteja no formato 'X.XXX'.
        """
        if not cfop_str or not isinstance(cfop_str, str):
            return ""
        clean_cfop = cfop_str.replace('.', '')
        if clean_cfop.isdigit() and len(clean_cfop) >= 4:
            return f"{clean_cfop[0]}.{clean_cfop[1:]}"
        return cfop_str
