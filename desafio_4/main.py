import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from ferramentas.ferramentas_planilha import processar_calculo_vr_completo


def main():
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("--- ERRO CRÍTICO: Chave GROQ_API_KEY não encontrada. ---")
        return

    print("Chave da API Groq carregada. Iniciando a automação...")
    print("=" * 60)

    llm = ChatGroq(
        temperature=0,
        model_name="llama3-70b-8192",
        api_key=groq_api_key
    )

    ferramentas = [processar_calculo_vr_completo]
    tool_names = [tool.name for tool in ferramentas]

    # Template do agente ReAct
    template = """Você é um assistente especializado em cálculo de VR (Vale Refeição). 
Você tem acesso às seguintes ferramentas:

{tools}

Use o seguinte formato:

Question: a pergunta de input que você deve responder
Thought: você deve sempre pensar no que fazer
Action: a ação a ser tomada, deve ser uma das [{tool_names}]
Action Input: formato JSON com os parâmetros necessários
Observation: o resultado da ação
... (este Thought/Action/Action Input/Observation pode se repetir N vezes)
Thought: Agora sei a resposta final
Final Answer: a resposta final para a pergunta original

IMPORTANTE: Para Action Input, use sempre formato JSON válido.
Exemplo correto: {{"mes": 5, "ano": 2025}}

Comece!

Question: {input}
Thought:{agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template)

    # Criar o agente
    agent = create_react_agent(llm, ferramentas, prompt)

    # Criar o executor do agente
    agent_executor = AgentExecutor(
        agent=agent,
        tools=ferramentas,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3,
        early_stopping_method="generate"
    )

    tarefa_principal = "Execute o processo completo de cálculo de VR para o mês 5 de 2025."
    print(f"\n--- Executando Tarefa Principal: {tarefa_principal} ---")

    try:
        # Executar o agente
        resultado = agent_executor.invoke({"input": tarefa_principal})

        print("\n\n--- RESULTADO FINAL DA EXECUÇÃO ---")
        print(resultado["output"])
        print("-" * 60)

    except Exception as e:
        print(f"Erro durante execução do agente: {e}")
        print("-" * 60)

        # Fallback: tentar executar diretamente se o agente falhar
        print("Tentando execução direta como fallback...")
        try:
            # Usar invoke em vez de chamada direta
            resultado_direto = processar_calculo_vr_completo.invoke({"mes": 5, "ano": 2025})
            print("\n--- RESULTADO DA EXECUÇÃO DIRETA ---")
            print(resultado_direto)
        except Exception as e2:
            print(f"Erro na execução direta: {e2}")


if __name__ == "__main__":
    main()