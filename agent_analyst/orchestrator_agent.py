# agent_analyst/orchestrator_agent.py

from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry
import pandas as pd
from pathlib import Path
import zipfile
import nest_asyncio

nest_asyncio.apply()


@dataclass
class QueryDeps:
    """Dependências para o agente de consulta, contendo o DataFrame final."""
    df: pd.DataFrame


class OrchestratorAgent:
    """
    Um agente orquestrador que usa código determinístico para tarefas de preparação
    e um agente LLM interno para a análise de dados inteligente.
    """

    def __init__(self, model_name: str = 'groq:gemma2-9b-it'):
        self.data_path = Path("data")
        self.df_completo = None

        # Este é o agente LLM interno, focado APENAS em consultar o DataFrame.
        # Seu prompt é simples e direto, tornando-o muito mais confiável.
        self.query_agent = Agent(
            model=model_name,
            system_prompt="""
            Você é um especialista em análise de dados com pandas.
            Você tem acesso a um DataFrame chamado 'df'.
            Sua tarefa é escrever e executar uma única linha de código pandas para responder à pergunta do usuário.
            Responda de forma concisa com o resultado e o código que você usou.
            Use os nomes exatos das colunas. Colunas com espaços devem estar entre aspas, ex: df['NOME DA COLUNA'].
            Colunas disponíveis: ['CHAVE DE ACESSO', 'MODELO', 'SÉRIE', 'NÚMERO', 'NATUREZA DA OPERAÇÃO', 'DATA EMISSÃO_CAB', 'EVENTO MAIS RECENTE', 'DATA/HORA EVENTO MAIS RECENTE', 'CPF/CNPJ Emitente', 'RAZÃO SOCIAL EMITENTE', 'INSCRIÇÃO ESTADUAL EMITENTE', 'UF EMITENTE', 'MUNICÍPIO EMITENTE', 'CNPJ DESTINATÁRIO', 'NOME DESTINATÁRIO', 'UF DESTINATÁRIO', 'INDICADOR IE DESTINATÁRIO', 'DESTINO DA OPERAÇÃO', 'CONSUMIDOR FINAL', 'PRESENÇA DO COMPRADOR', 'VALOR NOTA FISCAL', 'MODELO_ITEM', 'SÉRIE_ITEM', 'NÚMERO_ITEM', 'NATUREZA DA OPERAÇÃO_ITEM', 'DATA EMISSÃO_ITEM', 'CPF/CNPJ Emitente_ITEM', 'RAZÃO SOCIAL EMITENTE_ITEM', 'INSCRIÇÃO ESTADUAL EMITENTE_ITEM', 'UF EMITENTE_ITEM', 'MUNICÍPIO EMITENTE_ITEM', 'CNPJ DESTINATÁRIO_ITEM', 'NOME DESTINATÁRIO_ITEM', 'UF DESTINATÁRIO_ITEM', 'INDICADOR IE DESTINATÁRIO_ITEM', 'DESTINO DA OPERAÇÃO_ITEM', 'CONSUMIDOR FINAL_ITEM', 'PRESENÇA DO COMPRADOR_ITEM', 'NÚMERO PRODUTO', 'DESCRIÇÃO DO PRODUTO/SERVIÇO', 'CÓDIGO NCM/SH', 'NCM/SH (TIPO DE PRODUTO)', 'CFOP', 'QUANTIDADE', 'UNIDADE', 'VALOR UNITÁRIO', 'VALOR TOTAL']
            """,
            deps_type=QueryDeps,
            retries=3
        )
        self.query_agent.tool(self.safe_df_query)

    @staticmethod
    def safe_df_query(ctx: RunContext[QueryDeps], query: str) -> str:
        """Executa consultas pandas de forma segura no DataFrame fornecido."""
        try:
            print(f"🤖 Agente de consulta executando: {query}")
            df = ctx.deps.df
            # Dicionário seguro para eval
            safe_dict = {'df': df, 'pd': pd}
            result = eval(query, {'__builtins__': {}}, safe_dict)
            return f"Resultado: {str(result)}"
        except Exception as e:
            error_msg = f"Erro na consulta: {str(e)}. Verifique a sintaxe e os nomes das colunas."
            raise ModelRetry(error_msg) from e

    def _prepare_data(self, zip_filename: str, cabecalho_filename: str, itens_filename: str):
        """Etapa determinística: descompacta e carrega os dados."""
        print("--- Iniciando Etapa de Preparação de Dados (Determinística) ---")

        # 1. Descompactar
        zip_path = self.data_path / zip_filename
        path_cabecalho = self.data_path / cabecalho_filename

        if not path_cabecalho.exists():
            if not zip_path.exists():
                raise FileNotFoundError(f"Arquivo ZIP '{zip_path}' não encontrado.")
            print(f"📄 Descompactando '{zip_path}'...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.data_path)
            print("✅ Arquivos descompactados.")
        else:
            print("👍 Arquivos CSV já existem. Pulando descompactação.")

        # 2. Carregar e Mesclar
        print("🔄 Carregando e mesclando arquivos CSV...")
        df_cabecalho = pd.read_csv(path_cabecalho, sep=',', decimal='.', parse_dates=['DATA EMISSÃO'], dayfirst=False)
        df_itens = pd.read_csv(self.data_path / itens_filename, sep=',', decimal='.', parse_dates=['DATA EMISSÃO'],
                               dayfirst=False)

        df_cabecalho['VALOR NOTA FISCAL'] = pd.to_numeric(df_cabecalho['VALOR NOTA FISCAL'], errors='coerce')
        df_itens['QUANTIDADE'] = pd.to_numeric(df_itens['QUANTIDADE'], errors='coerce')
        df_cabecalho.dropna(subset=['CHAVE DE ACESSO', 'VALOR NOTA FISCAL'], inplace=True)
        df_itens.dropna(subset=['CHAVE DE ACESSO', 'QUANTIDADE'], inplace=True)

        self.df_completo = pd.merge(df_cabecalho, df_itens, on='CHAVE DE ACESSO', how='left',
                                    suffixes=('_CAB', '_ITEM'))
        print(f"✅ Dados preparados. DataFrame final com {self.df_completo.shape[0]} linhas.")
        print("--- Fim da Etapa de Preparação ---")

    def run_task(self, question: str) -> str:
        """
        Executa a tarefa completa: prepara os dados e depois usa o agente LLM para responder a uma pergunta.
        """
        # Etapa 1: Preparar os dados de forma robusta
        self._prepare_data(
            zip_filename="202401_NFs.zip",
            cabecalho_filename="202401_NFs_Cabecalho.csv",
            itens_filename="202401_NFs_Itens.csv"
        )

        if self.df_completo is None:
            return "Erro: Falha ao carregar os dados. Não é possível continuar."

        # Etapa 2: Usar o agente LLM para a tarefa inteligente
        print("\n--- Iniciando Etapa de Análise (Agente LLM) ---")
        print(f"❓ Pergunta enviada ao agente: {question}")

        try:
            deps = QueryDeps(df=self.df_completo)
            response = self.query_agent.run_sync(question, deps=deps)
            final_answer = response.new_messages()[-1].parts[0].content
            print("--- Fim da Etapa de Análise ---")
            return final_answer
        except Exception as e:
            return f"❌ Erro durante a execução do agente de consulta: {str(e)}"