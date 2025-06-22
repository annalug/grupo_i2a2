import os
import pandas as pd
from typing import List, Optional
import google.generativeai as genai


class DataAnalysisAgent:
    def __init__(self, df_list: List[pd.DataFrame], df_names: List[str]):
        """
        Versão atualizada para usar a API oficial do Gemini sem thinking_config
        """
        if not df_list:
            raise ValueError("A lista de dataframes não pode ser vazia.")

        # Configuração do cliente Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Variável GEMINI_API_KEY não encontrada no .env")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.df_list = df_list
        self.df_names = df_names
        self._prepare_data_context()

    def _prepare_data_context(self):
        """Prepara um resumo dos dataframes para incluir no contexto"""
        self.data_context = "\n".join(
            f"- {name}: {len(df)} linhas, {len(df.columns)} colunas. Colunas: {', '.join(df.columns)}"
            for name, df in zip(self.df_names, self.df_list)
        )

    @staticmethod
    def load_data(path: str) -> Optional[pd.DataFrame]:
        """Carrega dados com tratamento robusto de erros"""
        try:
            df = pd.read_csv(path, sep=',', decimal='.')
            print(f"✅ Dados carregados: {path}")
            return df
        except Exception as e:
            print(f"❌ Erro ao carregar {path}: {str(e)}")
            return None

    def _generate_prompt(self, question: str) -> str:
        """Gera o prompt contextualizado com os dataframes"""
        return f"""
        Você é um analista de dados especializado em notas fiscais. 
        Você tem acesso aos seguintes dataframes:

        {self.data_context}

        Relacione os dataframes pela coluna 'CHAVE DE ACESSO' quando necessário.

        Responda a seguinte pergunta:
        {question}

        Forneça:
        1. Uma explicação clara
        2. O código pandas usado para obter a resposta (se aplicável)
        3. A resposta final formatada
        """

    def run_query(self, question: str) -> Optional[str]:
        """Executa consulta usando a API do Gemini"""
        try:
            prompt = self._generate_prompt(question)
            print(f"\n🔍 Processando: {question[:50]}...")

            response = self.model.generate_content(prompt)

            if not response.text:
                raise ValueError("Resposta vazia do Gemini")

            return response.text

        except Exception as e:
            print(f"❌ Erro na consulta: {str(e)}")
            return None