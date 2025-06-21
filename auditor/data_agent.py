import os
import pandas as pd
from pydantic_ai.pandas import PandasAgent
from pydantic_ai.llm_providers import GoogleProvider


class DataAnalysisAgent:
    def __init__(self, df_list: list[pd.DataFrame], df_names: list[str]):
        """
        Inicializa o Agente de Análise de Dados.

        Args:
            df_list (list[pd.DataFrame]): Uma lista de dataframes pandas para analisar.
            df_names (list[str]): Uma lista com os nomes dos dataframes, na mesma ordem.
        """
        if not df_list:
            raise ValueError("A lista de dataframes não pode ser vazia.")

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi encontrada.")

        # O PandasAgent é especializado em interagir com dataframes
        # Ele recebe uma lista de dataframes para poder fazer joins e análises complexas
        self.agent = PandasAgent(
            df_list,
            provider=GoogleProvider(api_key=api_key, model='gemini-1.5-flash'),
            llm_options={"temperature": 0},  # Temperatura 0 para respostas mais determinísticas (código)
            description=f"""
            Você é um agente especialista em análise de dados com a biblioteca pandas.
            Você tem acesso a {len(df_list)} dataframes: {', '.join(df_names)}.
            O dataframe '{df_names[0]}' contém os cabeçalhos das notas fiscais.
            O dataframe '{df_names[1]}' contém os itens de cada nota fiscal.
            Ambos podem ser ligados pela coluna 'CHAVE DE ACESSO'.
            Sua tarefa é responder perguntas sobre esses dados gerando e executando código pandas.
            """
        )

    def load_data(data_path: str) -> pd.DataFrame:
        """
        Carrega um arquivo CSV para um dataframe pandas, tratando possíveis erros.
        """
        try:
            # Especifica o separador e o decimal conforme a descrição do problema
            return pd.read_csv(data_path, sep=',', decimal='.')
        except FileNotFoundError:
            print(f"Erro: Arquivo não encontrado em '{data_path}'")
            return None

    def run_query(self, question: str) -> any:
        """
        Executa uma pergunta (query) e retorna a resposta do agente.
        """
        print(f"\n💬 Pergunta: '{question}'")
        print("🤖 Gerando e executando código pandas para responder... Aguarde.")

        try:
            response = self.agent.run(question)
            print("✅ Resposta encontrada!")
            return response
        except Exception as e:
            print(f"❌ Ocorreu um erro ao processar a pergunta: {e}")
            return None