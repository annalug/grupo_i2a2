import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd

# Configurar caminhos
sys.path.insert(0, str(Path(__file__).parent))
from agent_analyst.data_agent import DataAnalyzer

def main():
    # Configuração inicial
    load_dotenv()
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("Configure GROQ_API_KEY no arquivo .env")

    os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
    os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'

    # Inicializar analisador
    analyzer = DataAnalyzer(model_name='groq:gemma2-9b-it')

    try:
        # Carregar dados
        df_cabecalho, df_itens = analyzer.load_data()
        df_completo = pd.merge(
            df_cabecalho,
            df_itens,
            on='CHAVE DE ACESSO',
            how='left',
            suffixes=('_CAB', '_ITEM')
        )

        # Perguntas de exemplo
        perguntas = [
            "Quais são as colunas disponíveis nos dados?",
            "Quantas notas fiscais existem no total?",
            "Qual é o fornecedor com maior valor total em notas fiscais?",
            "Qual é o produto mais frequente nas notas?",
            "Qual o valor total de notas para o estado de SP?",
            "Existem notas com valor superior a 100.000? Se sim, quantas?"
        ]

        for pergunta in perguntas:
            print(f"\n❓ Pergunta: {pergunta}")
            resposta = analyzer.ask_question(df_completo, pergunta)
            print(f"💡 Resposta:\n{resposta}")
            print("─" * 50)

    except Exception as e:
        print(f"❌ Erro fatal: {str(e)}")

if __name__ == "__main__":
    main()