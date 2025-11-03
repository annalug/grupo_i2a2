import streamlit as st
import sys
from pathlib import Path
import os
import json

# Configuração da página
st.set_page_config(
    page_title="Analisador e Classificador de NF-e",
    page_icon="🤖",
    layout="wide"
)

# Configuração do path para importação
sys.path.insert(0, str(Path(__file__).parent))
from agent_analyst.orchestrator_agent import OrchestratorAgent


def formatar_resultado(resultado: dict):
    """
    Função dedicada a renderizar o dicionário de resultados na interface do Streamlit.
    """
    if "erro" in resultado:
        st.error(f"❌ **Erro no Processamento:** {resultado['erro']}")
        return

    dados_doc = resultado.get('dados_do_documento', {})
    analise = resultado.get('analise_classificacao', {})

    if "erro" in analise:
        st.error(f"❌ **Erro na Classificação:** {analise['erro']}")
        with st.expander("Ver dados extraídos do documento (JSON)"):
            st.json(dados_doc)
        return

    st.success("✅ Documento processado e classificado com sucesso!")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Dados do Documento")
        cabecalho = dados_doc.get('cabecalho', {})
        st.markdown(f"**NF-e:** `{cabecalho.get('numero_nf', 'N/A')}`")
        st.markdown(f"**Valor Total:** `R$ {cabecalho.get('valor_total', 0.0):,.2f}`")
        st.markdown(f"**Emissão:** `{cabecalho.get('data_emissao', 'N/A')}`")
        st.markdown(f"**Emitente:** `{cabecalho.get('emitente_nome', 'N/A')}`")
        st.markdown(f"**CNPJ Emitente:** `{cabecalho.get('emitente_cnpj', 'N/A')}`")

    with col2:
        st.subheader("📊 Classificação Automática")
        st.markdown(f"**Ramo de Atividade Detectado:** `{analise.get('ramo_empresa_detectado', 'Não identificado')}`")
        if analise.get('ramo_especifico_customizado') and analise['ramo_especifico_customizado'] != 'Padrão':
            st.markdown(f"**Setor Customizado:** `{analise['ramo_especifico_customizado']}`")
        st.markdown(f"**Tipo de Documento:** `{analise.get('tipo_documento', 'Não classificado')}`")
        st.markdown(f"**Centro de Custo Sugerido:** `{analise.get('centro_custo', 'Não definido')}`")

        cfop_info = analise.get('cfop_info', {})
        st.info(f"""
        **CFOP Identificado:** `{cfop_info.get('cfop', 'N/A')}`\n
        **Descrição:** {cfop_info.get('descricao', 'Descrição não encontrada.')}
        """)

    st.markdown("---")
    st.subheader("💡 Análise Detalhada e Recomendações")

    # Alertas
    st.markdown("**Alertas Setoriais e Legais:**")
    alertas = analise.get('alertas_especificos', [])
    if alertas:
        for alerta in alertas:
            st.warning(alerta)
    else:
        st.caption("Nenhum alerta específico foi gerado para esta operação.")

    # Implicações Fiscais
    st.markdown("**Implicações Fiscais (Específicas do Ramo):**")
    implicacoes = analise.get('implicacoes_fiscais', [])
    if implicacoes:
        for implicacao in implicacoes:
            st.info(implicacao)
    else:
        st.caption("Nenhuma implicação fiscal específica foi encontrada para esta operação.")

    # Recomendações
    st.markdown("**Recomendações de Ação e Arquivamento:**")
    recomendacoes = analise.get('recomendacoes_arquivamento', [])
    if recomendacoes:
        for rec in recomendacoes:
            st.success(rec)
    else:
        st.caption("Nenhuma recomendação específica foi gerada.")

    with st.expander("Ver dados completos da análise (formato JSON)"):
        st.json(resultado)


def main():
    """
    Função principal que estrutura e executa a aplicação Streamlit.
    """
    st.title("🤖 Analisador e Classificador de Notas Fiscais")

    try:
        if 'agent' not in st.session_state:
            with st.spinner("🚀 Inicializando agentes e carregando configurações..."):
                st.session_state.agent = OrchestratorAgent()

        agent = st.session_state.agent

        st.sidebar.title("⚙️ Ações")
        st.sidebar.header("Processamento em Lote")
        st.sidebar.info("Processe e organize todos os arquivos da pasta `data/notas/`.")

        if st.sidebar.button("Organizar Notas em Lote"):
            with st.spinner("⏳ Processando arquivos em lote... Isso pode levar alguns minutos."):
                resultado_lote = agent.processar_lote_notas()

            st.header("🏁 Resultado do Processamento em Lote")
            if "erro" in resultado_lote:
                st.error(resultado_lote["erro"])
            elif "info" in resultado_lote:
                st.info(resultado_lote["info"])
            else:
                # Mensagem de sucesso clara
                st.success("✅ Organização da Pasta Concluída com Sucesso!")
                st.markdown("---")

                # Tabela de Resumo
                st.subheader("Sumário da Classificação")
                col_total, col_sucesso, col_falha = st.columns(3)
                col_total.metric("Total de Arquivos", resultado_lote['total'])
                col_sucesso.metric("Processados com Sucesso", resultado_lote['sucesso'])
                col_falha.metric("Falhas (Mantidos na Entrada)", resultado_lote['falhas'])

                if resultado_lote['falhas'] > 0:
                    st.warning(
                        f"⚠️ **Atenção:** {resultado_lote['falhas']} arquivos falharam no processamento e foram mantidos na pasta de entrada (`data/notas/`). Verifique o console para detalhes dos erros."
                    )

                st.info(
                    f"Os arquivos classificados foram **copiados** para a estrutura de pastas em: `{resultado_lote['output_path']}`")
                st.caption("Os arquivos originais foram mantidos na pasta de entrada.")

        st.sidebar.markdown("---")

        st.header("Análise de Arquivo Individual")
        st.markdown("Faça o upload de um único arquivo **XML ou PDF** para uma análise detalhada.")

        uploaded_file = st.file_uploader(
            "Selecione o arquivo da NF-e",
            type=['xml', 'pdf'],
            help="Arraste e solte ou clique para selecionar o arquivo XML ou PDF da sua nota fiscal."
        )

        # --- LINHA CORRIGIDA ---
        # Verifica se um novo arquivo foi carregado antes de reprocessar.
        if uploaded_file is not None and uploaded_file != st.session_state.get('processed_file'):
            # --- FIM DA CORREÇÃO ---
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(exist_ok=True)
            file_path = upload_dir / uploaded_file.name

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner(f"🔍 Analisando o documento `{uploaded_file.name}`..."):
                resultado = agent.processar_documento(str(file_path))
                formatar_resultado(resultado)

            # Armazena a referência do arquivo processado para evitar reprocessamento
            st.session_state.processed_file = uploaded_file
            os.remove(file_path)

    except Exception as e:
        st.error(f"❌ Ocorreu um erro fatal na aplicação: {str(e)}")
        st.info("""
        💡 **Possíveis Soluções:**
        1.  Verifique se o `crawler.py` foi executado para gerar os dados de CFOP.
        2.  Confirme que os arquivos `ramos_atividade.json` e `centros_custo.json` existem.
        3.  Para processamento de PDF, certifique-se que o Tesseract-OCR está instalado.
        """)


if __name__ == "__main__":
    main()