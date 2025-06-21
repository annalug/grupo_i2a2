import os
from pydantic import BaseModel, Field
from enum import Enum
from typing import List
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

# --- 1. DEFINIÇÃO DOS MODELOS DE DADOS (ESTRUTURA DA RESPOSTA) ---

class StatusAnalise(str, Enum):
    APROVADO = "Aprovado com sucesso"
    PENDENTE = "Pendente - Requer atenção humana"
    REPROVADO = "Reprovado - Erros críticos encontrados"


class ImpostosItem(BaseModel):
    icms: float = Field(..., description="Valor do ICMS do item.")
    ipi: float = Field(..., description="Valor do IPI do item.")
    pis: float = Field(..., description="Valor do PIS do item.")
    cofins: float = Field(..., description="Valor do COFINS do item.")


class ItemNotaFiscal(BaseModel):
    descricao: str = Field(..., description="Descrição do produto ou serviço.")
    ncm: str = Field(..., description="Código NCM do item.")
    quantidade: float = Field(..., description="Quantidade do item.")
    valor_unitario: float = Field(..., description="Valor unitário do item.")
    valor_total: float = Field(..., description="Valor total do item.")
    impostos: ImpostosItem = Field(..., description="Detalhes dos impostos para o item.")


class AnaliseFiscal(BaseModel):
    id_documento: str = Field(..., description="Identificador único do documento fiscal analisado.")
    status_geral: StatusAnalise = Field(..., description="Status geral da validação do documento.")
    pontos_de_atencao: List[str] = Field(..., description="Lista de problemas ou inconsistências encontradas.")
    sugestoes_correcao: List[str] = Field(..., description="Lista de ações sugeridas para corrigir os problemas.")
    resumo_executivo: str = Field(..., description="Breve resumo da análise para um gestor (CFO/Controller).")


# --- 2. DEFINIÇÃO DO PROMPT DO SISTEMA (A "PERSONALIDADE" DO AGENTE) ---

SYSTEM_PROMPT_AFI = """
Você é o "Auditor Fiscal Inteligente (AFI)", um especialista em legislação tributária brasileira.
Sua função é analisar dados de documentos fiscais para garantir conformidade e identificar erros.

Suas tarefas são:
1. Verificar cálculos de totais (quantidade vs. valor unitário).
2. Analisar a consistência dos impostos (ICMS, IPI, PIS, COFINS).
3. Identificar riscos e dados inconsistentes.
4. Gerar um status claro, problemas, sugestões e um resumo para gestão.

Sua resposta DEVE OBRIGATORIAMENTE seguir a estrutura do modelo Pydantic `AnaliseFiscal`.
"""


# --- 3. FUNÇÃO PARA CRIAR E CONFIGURAR O AGENTE ---

def criar_agente_afi() -> Agent:
    """
    Cria e retorna uma instância configurada do Agente Auditor Fiscal Inteligente.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi encontrada. Verifique seu arquivo .env.")

    model = GeminiModel(
        'gemini-2.0-flash', provider=GoogleGLAProvider(api_key=api_key)
    )
    agente = Agent(model,output_model=AnaliseFiscal,)

    return agente