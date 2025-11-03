# agent_analyst/customizacao_agent.py_
from .base_agent import BaseAgent
from typing import Dict, List

class CustomizacaoAgent(BaseAgent):
    """
    Agente responsável por lidar com a customização para ramos de atividade
    específicos (órgãos públicos, terceiro setor, etc.) e mudanças legais.
    """

    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        # Este agente pode carregar configurações adicionais ou regras de negócio complexas
        # Ex: self.regras_especificas = self._carregar_json(self.data_dir / "regras_especificas.json")

    def analisar_setor_especifico(self, dados_documento: Dict) -> Dict:
        """
        Analisa o documento para identificar se ele pertence a um setor de
        tratamento especial (órgãos públicos, terceiro setor, etc.) e aplica
        regras específicas.
        """
        alertas = []
        implicacoes = []
        ramo_especifico = "Padrão"

        # Exemplo de lógica para Órgãos Públicos (CNPJ começa com 00.394.460/...)
        cnpj_destinatario = dados_documento.get("cabecalho", {}).get("destinatario_cpf_cnpj")
        if cnpj_destinatario and cnpj_destinatario.startswith("00394460"): # CNPJ da União
            ramo_especifico = "Órgão Público"
            alertas.append("ALERTA SETOR PÚBLICO: Verificar regras de retenção de impostos federais (Lei 9.430/96).")
            implicacoes.append("Tratamento fiscal diferenciado (imunidade/isenção) pode ser aplicável.")

        # Exemplo de lógica para Terceiro Setor (simulação via CNAE)
        cnae_emitente = dados_documento.get("cabecalho", {}).get("emitente_cnae")
        if cnae_emitente and cnae_emitente.startswith("94"): # CNAE de Atividades de organizações associativas
            ramo_especifico = "Terceiro Setor"
            alertas.append("ALERTA TERCEIRO SETOR: Conferir se a entidade possui Certificado de Entidade Beneficente de Assistência Social (CEBAS).")
            implicacoes.append("Imunidade de impostos federais (IRPJ, CSLL, PIS, COFINS) pode ser aplicável.")

        return {
            "ramo_especifico_detectado": ramo_especifico,
            "alertas_customizados": alertas,
            "implicacoes_customizadas": implicacoes
        }

    def tratar_mudancas_legais(self, cfop: str) -> List[str]:
        """
        Simula a adaptação a mudanças legais. Na prática, isso seria um
        mecanismo de atualização de regras externas.
        """
        alertas = []
        # Simulação: Se o CFOP for de um tipo que recentemente teve mudança de alíquota
        if cfop == "5.405":
            alertas.append("ATENÇÃO LEGAL: CFOP 5.405 (Venda de mercadoria sujeita a ST) - Verificar a última atualização da MVA para o estado de destino (Portaria XYZ/2024).")
        return alertas