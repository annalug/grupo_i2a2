# agent_analyst/generico_agent.py_
from .base_agent import BaseAgent
from typing import Dict, List

class GenericoAgent(BaseAgent):
    """Agente genérico para Comércio e Serviços."""

    def __init__(self, ramo_empresa: str, data_dir: str = "data"):
        super().__init__(data_dir)
        self.ramo_empresa = ramo_empresa
        self.ramo_config = self._carregar_json(self.data_dir / "ramos_atividade.json").get(ramo_empresa, {})

    def analisar_documento(self, cfop: str, dados_documento: Dict) -> Dict:
        """
        Realiza a análise fiscal genérica.
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
            implicacoes.append(f"Atenção aos impostos específicos do ramo {self.ramo_empresa}: {', '.join(impostos)}.")
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
        """Gera alertas específicos para o ramo."""
        alertas = []
        if self.ramo_empresa == 'comercio' and cfop == '5.405':
            alertas.append("ALERTA COMÉRCIO: Venda de mercadoria com ICMS-ST. Assegurar que o imposto foi retido anteriormente.")
        elif self.ramo_empresa == 'servicos' and cfop.startswith(('5.9', '6.9')):
            alertas.append("ALERTA SERVIÇOS: Verificar retenção de impostos (IRRF, CSRF) na fonte.")
        return alertas
