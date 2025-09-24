# dashboard.py (versão corrigida)

import streamlit as st

from pathlib import Path
from dotenv import load_dotenv
import os
import sys

# Configurar caminhos para importar o agente
sys.path.insert(0, str(Path(__file__).parent))
from agent_analyst.orchestrator_agent import OrchestratorAgent

# --- Configuração da Página e Carregamento de Recursos ---

st.set_page_config(
    page_title="Agente de Análise de Notas Fiscais",
    page_icon="🤖",
    layout="centered"
)

# Carregar variáveis de ambiente
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    st.error("❌ A chave GROQ_API_KEY não foi encontrada. Configure-a no seu arquivo .env.")
    st.stop()

os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'


# --- Inicialização do Agente ---

@st.cache_resource
def initialize_agent():
    try:
        agent = OrchestratorAgent(model_name='llama3-70b-8192')  # Usando o modelo recomendado

        # Carrega os dados antes do teste
        agent._prepare_data(
            zip_filename="202401_NFs.zip",
            cabecalho_filename="202401_NFs_Cabecalho.csv",
            itens_filename="202401_NFs_Itens.csv"
        )

        test_response = agent.run_task("Quantas colunas tem o cabeçalho?")

        if "❌" in test_response:
            raise Exception(f"Falha na inicialização: {test_response}")

        return agent
    except Exception as e:
        raise Exception(f"Erro ao inicializar agente: {str(e)}")


# Inicializar o agente
try:
    with st.spinner("🔄 Preparando o ambiente do agente... Isso pode levar alguns momentos."):
        agent = initialize_agent()

    # Mostrar resumo dos dados carregados
    if hasattr(agent, 'get_data_summary'):
        with st.expander("📊 Resumo dos Dados Carregados", expanded=False):
            st.markdown(agent.get_data_summary())

    st.success("✅ Agente pronto para análise!")

except Exception as e:
    st.error(f"❌ Falha ao inicializar o agente: {e}")
    st.info("💡 Verifique se os arquivos de dados estão na pasta 'data' e se a API key está configurada.")
    st.stop()

# --- Interface do Dashboard ---

st.title("🤖 Agente Interativo de Análise de NF-e")
st.markdown(
    """
    Faça perguntas em **linguagem natural** sobre os dados das notas fiscais eletrônicas. 
    O agente irá analisar os arquivos e gerar uma resposta detalhada para você.
    """
)

# Seção de exemplos expandida
with st.expander("💡 Exemplos de Perguntas", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 Análises Básicas:**")
        st.markdown("""
        - Quantas notas fiscais existem no total?
        - Qual é o valor total de todas as notas?
        - Quantos itens existem no total?
        - Quais são as colunas disponíveis?
        """)

        st.markdown("**🏢 Análises por Fornecedor:**")
        st.markdown("""
        - Qual fornecedor emitiu mais notas?
        - Qual o valor total por razão social?
        - Liste os top 5 fornecedores por valor
        """)

    with col2:
        st.markdown("**🏙️ Análises Geográficas:**")
        st.markdown("""
        - Quais os principais municípios emissores?
        - Qual o valor total por estado?
        - Liste as notas de São Paulo
        """)

        st.markdown("**📦 Análises de Produtos:**")
        st.markdown("""
        - Qual o produto mais vendido?
        - Qual item tem maior valor unitário?
        - Quantos produtos únicos existem?
        """)

# Botões de exemplo clicáveis
st.markdown("**🚀 Perguntas Rápidas:**")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 Total de Notas", use_container_width=True):
        st.session_state['quick_question'] = "Quantas notas fiscais existem no total?"

with col2:
    if st.button("💰 Valor Total", use_container_width=True):
        st.session_state['quick_question'] = "Qual é o valor total de todas as notas fiscais?"

with col3:
    if st.button("🏢 Top Fornecedores", use_container_width=True):
        st.session_state['quick_question'] = "Quais são os 5 fornecedores com maior valor total?"

with col4:
    if st.button("📦 Produtos", use_container_width=True):
        st.session_state['quick_question'] = "Quais são os 10 produtos mais vendidos em quantidade?"

# Inicializar o histórico do chat
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "👋 Olá! Estou pronto para analisar os dados das notas fiscais. Qual é a sua pergunta?"
    }]

# Processar pergunta rápida se foi clicada
if 'quick_question' in st.session_state:
    prompt = st.session_state.quick_question
    del st.session_state.quick_question

    # Adicionar ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Processar resposta
    with st.spinner("🧠 Analisando dados..."):
        response = agent.run_task(prompt)

    st.session_state.messages.append({"role": "assistant", "content": response})

# Exibir histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input("💬 Digite sua pergunta sobre as notas fiscais..."):

    # Adicionar mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gerar resposta do agente
    with st.chat_message("assistant"):
        with st.spinner("🤖 O agente está analisando os dados..."):
            try:
                response = agent.run_task(prompt)
                st.markdown(response)

                # Adicionar resposta ao histórico
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                error_msg = f"❌ Erro ao processar sua pergunta: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar com informações úteis
with st.sidebar:
    st.markdown("### 📋 Informações do Sistema")

    if st.button("🔄 Limpar Histórico", use_container_width=True):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "👋 Histórico limpo! Estou pronto para novas perguntas."
        }]
        st.rerun()

    st.markdown("---")
    st.markdown("### 🛠️ Dicas de Uso")
    st.markdown("""
    - **Seja específico**: "Valor total das notas de SP" é melhor que "valores"
    - **Use números**: "Top 5 fornecedores" em vez de "principais fornecedores" 
    - **Combine critérios**: "Produtos com valor acima de R$ 100"
    - **Explore relações**: "Fornecedores por município"
    """)

    st.markdown("---")
    st.markdown("### ⚡ Status")
    st.success("🟢 Agente Online")
    st.info(f"📊 Dados Carregados")

    if hasattr(agent, 'df_cabecalho') and agent.df_cabecalho is not None:
        st.metric("📄 Notas Fiscais", len(agent.df_cabecalho))
    if hasattr(agent, 'df_itens') and agent.df_itens is not None:
        st.metric("📦 Itens", len(agent.df_itens))
