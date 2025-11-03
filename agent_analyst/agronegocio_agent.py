# agent_analyst/agronegocio_agent.py_
from .base_agent import BaseAgent
from typing import Dict, List

class AgronegocioAgent(BaseAgent):
    """Agente especialista para o ramo do Agronegócio."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        self.ramo_config = self._carregar_json(self.data_dir / "ramos_atividade.json").get("agronegocio", {})

    def analisar_documento(self, cfop: str, dados_documento: Dict) -> Dict:
        """
        Realiza a análise fiscal específica para o agronegócio.
        """
        return {
            "implicacoes_fiscais": self._analisar_implicacoes_fiscais(),
            "recomendacoes_arquivamento": self._gerar_recomendacoes(),
            "alertas_especificos": self._gerar_alertas_setoriais(cfop)
        }

    def _analisar_implicacoes_fiscais(self) -> List[str]:
        """Analisa implicações fiscais com base na configuração do ramo."""
        implicacoes = []
        impostos = self.ramo_config.get("impostos_especificos", [])
        particularidades = self.ramo_config.get("particularidades", [])

        if impostos:
            implicacoes.append(f"Atenção aos impostos específicos do agronegócio: {', '.join(impostos)}.")
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

    def _gerar_alertas_setoriais(self, cfop: str) -> List[str]:
        """Gera alertas específicos para o agronegócio."""
        alertas = []
        if cfop.startswith(("5.", "6.")):
            alertas.append("ALERTA AGRO: Verificar o cálculo do FUNRURAL para esta operação de venda.")
        if cfop in ["1.101", "2.101", "5.101", "6.101"]:
            alertas.append("INFO AGRO: Operação com grãos. Verificar se há isenção ou diferimento de ICMS aplicável.")
        return alertas