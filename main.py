import os
import sys
from dotenv import load_dotenv
from agent_analyst.data_agent import DataAnalysisAgent


# Adiciona o diretório raiz do projeto ao path do Python para encontrar o módulo 'agent_analyst'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))



def main():
    """
    Função principal que carrega os dados e inicia a interação com o agente.
    """
    # 1. Carrega as variáveis de ambiente
    load_dotenv()
    print("🚀 Iniciando o Agente de Análise de Dados de Notas Fiscais...")

    # 2. Carrega os arquivos CSV para dataframes pandas
    path_cabecalho = "data/202401_NFs_Cabecalho.csv"
    path_itens = "data/202401_NFs_Itens.csv"

    # A chamada agora funciona porque load_data é um staticmethod
    df_cabecalho = DataAnalysisAgent.load_data(path_cabecalho)
    df_itens = DataAnalysisAgent.load_data(path_itens)

    if df_cabecalho is None or df_itens is None:
        print(" encerrando o programa.")
        return

    # 3. Cria a instância do agente com os dataframes carregados
    try:
        analyst = DataAnalysisAgent(
            df_list=[df_cabecalho, df_itens],
            df_names=["df_cabecalho", "df_itens"]
        )
    except ValueError as e:
        print(f"❌ Erro de configuração: {e}")
        return

    # 4. Lista de perguntas para o agente responder (conforme o escopo)
    perguntas = [
        "Qual é o fornecedor (RAZÃO SOCIAL EMITENTE) com o maior valor total de notas fiscais (VALOR NOTA FISCAL)?",
        "Qual item (DESCRIÇÃO DO PRODUTO/SERVIÇO) teve o maior volume total entregue (soma da QUANTIDADE)?",
        "Liste os 5 municípios emissores (MUNICÍPIO EMITENTE) com mais notas fiscais.",
        "Qual o valor total de notas emitidas para o estado (UF DESTINATÁRIO) de São Paulo (SP)?",
        "Existe alguma nota com valor superior a 100.000? Se sim, qual a sua chave de acesso e valor?"
    ]

    # 5. Loop para fazer as perguntas e imprimir as respostas
    for pergunta in perguntas:
        resposta = analyst.run_query(pergunta)
        if resposta is not None:
            print("--------------------------------------------------")
            print(f"📊 Resposta:\n{resposta}")
            print("--------------------------------------------------")

if __name__ == "__main__":
    main()