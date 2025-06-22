from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry
import pandas as pd
from typing import Tuple, List
from pathlib import Path
import nest_asyncio


nest_asyncio.apply()


@dataclass
class Deps:
    """Dependencies for the agent, containing the DataFrame to work with."""
    df: pd.DataFrame


class DataAnalyzer:
    def __init__(self, model_name: str = 'groq:gemma2-9b-it'):
        """Initialize the agent with the specified model."""
        self.agent = Agent(
            model=model_name,
            system_prompt="""Você é um assistente especializado em análise de dados de notas fiscais. 
            Você tem acesso a um DataFrame chamado 'df' que contém os dados combinados de cabeçalhos e itens.
            Para consultar os dados, sempre use 'df' como referência.
            Exemplos válidos:
            - Para contar notas: `len(df)`
            - Para ver colunas: `df.columns.tolist()`
            - Para filtrar: `df[df['VALOR NOTA FISCAL'] > 100000]`
            Responda em português e mostre o código usado quando aplicável.""",
            deps_type=Deps,
            retries=3,
        )
        self.agent.tool(self.df_query)

    @staticmethod
    def df_query(ctx: RunContext[Deps], query: str) -> str:
        """Executa consultas no DataFrame."""
        try:
            print(f'🔍 Executando consulta: {query}')
            # Adiciona verificação para garantir que estamos usando 'df'
            if not query.startswith('df.') and 'df[' not in query:
                query = f'df.{query}' if not query.startswith('(') else f'df{query}'

            # Executa a consulta de forma segura
            result = eval(query, {}, {'df': ctx.deps.df})
            return str(result)
        except Exception as e:
            raise ModelRetry(
                f'Erro na consulta "{query}": {str(e)}. Use a referência "df" e sintaxe pandas válida.') from e

    def load_data(self, base_path: str = "data") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Carrega e prepara os dados das notas fiscais."""
        try:
            path_cabecalho = Path(base_path) / "202401_NFs_Cabecalho.csv"
            path_itens = Path(base_path) / "202401_NFs_Itens.csv"

            # Carregar arquivos mantendo os nomes originais das colunas
            df_cabecalho = pd.read_csv(
                path_cabecalho,
                sep=',',
                decimal='.',
                parse_dates=['DATA EMISSÃO'],
                dayfirst=False
            )

            df_itens = pd.read_csv(
                path_itens,
                sep=',',
                decimal='.',
                parse_dates=['DATA EMISSÃO'],
                dayfirst=False
            )

            # Verificar colunas obrigatórias
            for col in ['CHAVE DE ACESSO', 'RAZÃO SOCIAL EMITENTE', 'VALOR NOTA FISCAL']:
                if col not in df_cabecalho.columns:
                    raise ValueError(f"Coluna obrigatória '{col}' não encontrada no cabeçalho")

            for col in ['CHAVE DE ACESSO', 'DESCRIÇÃO DO PRODUTO/SERVIÇO', 'QUANTIDADE']:
                if col not in df_itens.columns:
                    raise ValueError(f"Coluna obrigatória '{col}' não encontrada nos itens")

            # Converter colunas numéricas
            df_cabecalho['VALOR NOTA FISCAL'] = pd.to_numeric(df_cabecalho['VALOR NOTA FISCAL'], errors='coerce')
            df_itens['QUANTIDADE'] = pd.to_numeric(df_itens['QUANTIDADE'], errors='coerce')

            # Remover linhas inválidas
            df_cabecalho.dropna(subset=['CHAVE DE ACESSO', 'VALOR NOTA FISCAL'], inplace=True)
            df_itens.dropna(subset=['CHAVE DE ACESSO', 'QUANTIDADE'], inplace=True)

            print("✅ Dados carregados com sucesso:")
            print(f"- Cabeçalhos: {len(df_cabecalho)} notas fiscais")
            print(f"- Itens: {len(df_itens)} registros")

            return df_cabecalho, df_itens

        except Exception as e:
            raise ValueError(f"Erro ao carregar dados: {str(e)}") from e

    def ask_question(self, df: pd.DataFrame, question: str) -> str:
        """Faz uma pergunta sobre os dados."""
        try:
            deps = Deps(df=df)
            response = self.agent.run_sync(question, deps=deps)
            return response.new_messages()[-1].parts[0].content
        except Exception as e:
            return f"Erro ao processar pergunta: {str(e)}"