 #agent_analyst/automotivo_agent.py_
from .base_agent import BaseAgent
from typing import Dict, List

class AutomotivoAgent(BaseAgent):
    """Agente especialista para o Setor Automotivo."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        self.ramo_config = self._carregar_json(self.data_dir / "ramos_atividade.json").get("automotivo", {})

    def analisar_documento(self, cfop: str, dados_documento: Dict) -> Dict:
        """
        Realiza a análise fiscal específica para o setor automotivo.
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
            implicacoes.append(f"Atenção aos impostos específicos do setor automotivo: {', '.join(impostos)}.")
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
        """Gera alertas específicos para o setor automotivo."""
        alertas = []
        # Exemplo de validação de peças e serviços
        if cfop in ["5.401", "5.403", "6.401", "6.403"]:
            alertas.append("ALERTA AUTOMOTIVO: Operação com ICMS-ST. Conferir se o item é peça automotiva e se o MVA está correto.")

        # Validação de códigos de peças (simulação)
        for item in dados_documento.get("itens", []):
            if "pneu" in item.get("descricao", "").lower() and item.get("codigo_produto") is None:
                 alertas.append(f"ALERTA AUTOMOTIVO: Item '{item.get('descricao')}' sem código de produto. Verificar cadastro.")

        return alertas