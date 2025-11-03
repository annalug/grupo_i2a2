# agent_analyst/industria_agent.py_
from .base_agent import BaseAgent
from typing import Dict, List

class IndustriaAgent(BaseAgent):
    """Agente especialista para o ramo da Indústria."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        self.ramo_config = self._carregar_json(self.data_dir / "ramos_atividade.json").get("industria", {})

    def analisar_documento(self, cfop: str, dados_documento: Dict) -> Dict:
        """
        Realiza a análise fiscal específica para a indústria.
        """
        return {
            "implicacoes_fiscais": self._analisar_implicacoes_fiscais(),
            "recomendacoes_arquivamento": self._gerar_recomendacoes(),
            "alertas_especificos": self._gerar_alertas_setoriais(cfop, dados_documento)
        }

    def _analisar_implicacoes_fiscais(self) -> List[str]:
        """Analisa implicações fiscais com base na configuração do ramo."""
        implicacoes = []
        impostos = self.ramo_config.get("impostos_especificos", [])
        particularidades = self.ramo_config.get("particularidades", [])

        if impostos:
            implicacoes.append(f"Atenção aos impostos específicos da indústria: {', '.join(impostos)}.")
        if particularidades:
            implicacoes.extend(particularidades)

        return implicacoes or ["Verificar legislação tributária padrão para a operação."]

    def _gerar_recomendacoes(self) -> List[str]:
        """Gera recomendações de arquivamento."""
        recomendacoes = ["Arquivar digitalmente o arquivo XML original."]
        documentos = self.ramo_config.get("documentos_obrigatorios", [])
        if documentos:
            recomendacoes.append(f"Anexar os seguintes documentos de suporte: {', '.join(documentos)}.")
        return recomendacoes

    def _gerar_alertas_setoriais(self, cfop: str, dados_documento: Dict) -> List[str]:
        """Gera alertas específicos para a indústria."""
        alertas = []
        if cfop in ['5.401', '5.403', '5.405', '6.401', '6.403', '6.404']:
            alertas.append("ALERTA INDÚSTRIA: Operação com Substituição Tributária (ICMS-ST). Conferir base de cálculo e MVA.")

        # Exemplo de insumo para custo de produção
        if cfop.startswith(('1.', '2.')) and any("matéria-prima" in item.get("descricao", "").lower() for item in dados_documento.get("itens", [])):
            alertas.append("INFO INDÚSTRIA: Documento de entrada de matéria-prima. Insumo para cálculo de custo de produção.")

        return alertas
