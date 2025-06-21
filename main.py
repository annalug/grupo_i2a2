from dotenv import load_dotenv
from auditor.agent import criar_agente_afi, AnaliseFiscal


def apresentar_resultado(analise: AnaliseFiscal):
    """Função auxiliar para imprimir a análise de forma organizada."""
    print("\n--- ✅ Análise Fiscal Concluída ---")
    print(f"📄 ID do Documento: {analise.id_documento}")
    print(f"📊 Status Geral: {analise.status_geral.value}")

    print("\n❗ Pontos de Atenção Encontrados:")
    for ponto in analise.pontos_de_atencao:
        print(f"  - {ponto}")

    print("\n💡 Sugestões de Correção:")
    for sugestao in analise.sugestoes_correcao:
        print(f"  - {sugestao}")

    print("\n📈 Resumo Executivo:")
    print(f"  {analise.resumo_executivo}")
    print("---------------------------------")


def main():
    """
    Função principal que orquestra o processo de análise fiscal.
    """
    # 1. Carrega as variáveis de ambiente do arquivo .env
    load_dotenv()
    print("🤖 Iniciando o Auditor Fiscal Inteligente (AFI)...")

    # 2. Cria a instância do agente
    try:
        agente_afi = criar_agente_afi()
    except ValueError as e:
        print(f"❌ Erro de configuração: {e}")
        return

    # 3. Simula os dados de entrada (viriam de um XML/OCR em um caso real)
    dados_nota_fiscal = {
        "chave_nfe": "35240401234567890123456789012345678901234567",
        "itens": [
            {
                "descricao": "MONITOR LED 24 POLEGADAS FULLHD",
                "ncm": "85285200",
                "quantidade": 10.0,
                "valor_unitario": 150.00,
                "valor_total": 1550.00,  # ERRO PROPOSITAL! (10 * 150 = 1500)
                "impostos": {"icms": 180.00, "ipi": 75.00, "pis": 24.75, "cofins": 114.00}
            },
            {
                "descricao": "TECLADO MECANICO GAMER RGB",
                "ncm": "84716052",
                "quantidade": 5.0,
                "valor_unitario": 350.00,
                "valor_total": 1750.00,
                "impostos": {"icms": 210.00, "ipi": 87.50, "pis": 28.88, "cofins": 133.00}
            }
        ]
    }

    # 4. Executa a análise
    prompt_usuario = f"Analise os dados da seguinte nota fiscal e retorne sua avaliação: {dados_nota_fiscal}"

    try:
        print("🗣️  Enviando dados para análise... Aguarde.")
        resultado_analise = agente_afi.run_sync(prompt_usuario)
        apresentar_resultado(resultado_analise)
    except Exception as e:
        print(f"❌ Ocorreu um erro durante a chamada à API: {e}")


if __name__ == "__main__":
    main()