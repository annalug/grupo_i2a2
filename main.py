# main.py

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Configurar caminhos
sys.path.insert(0, str(Path(__file__).parent))
# Importa o novo agente orquestrador
from agent_analyst.orchestrator_agent import OrchestratorAgent


def main():
    # Configuração inicial
    load_dotenv()
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("Configure GROQ_API_KEY no arquivo .env")

    os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
    os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'

    # Inicializar o agente orquestrador robusto
    agent = OrchestratorAgent(model_name='groq:gemma2-9b-it')

    # Lista de perguntas para fazer ao agente
    perguntas = [
        "Qual é o fornecedor (RAZÃO SOCIAL EMITENTE) com o maior valor total em notas fiscais (VALOR NOTA FISCAL)? Mostre o nome e o valor.",
        "Quantas notas fiscais únicas existem no total?",
        "Qual o valor total de notas para o estado de 'SP' (UF DESTINATÁRIO)?",
        "Qual o produto (DESCRIÇÃO DO PRODUTO/SERVIÇO) mais vendido em quantidade (QUANTIDADE)?"
    ]

    try:
        for pergunta in perguntas:
            print(f"\n🎯 Executando tarefa para a pergunta: \"{pergunta}\"")
            print("=" * 60)

            # O método run_task agora faz tudo: prepara os dados e responde à pergunta
            resposta_final = agent.run_task(pergunta)

            print("\n✅ Tarefa Concluída!")
            print(f"💡 Resposta Final do Agente:\n{resposta_final}")
            print("─" * 60)

    except Exception as e:
        print(f"❌ Erro fatal no script principal: {str(e)}")


if __name__ == "__main__":
    main()