import pandas as pd
from typing import Dict, List
from pathlib import Path
import json
from .base_agent import BaseAgent


class CFOPClassifierAgent(BaseAgent):
    """
    Agente responsável por classificar documentos fiscais com base no CFOP,
    ramo de atividade e outras regras de negócio configuráveis.
    """

    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        self.cfop_data = None
        # Carrega as configurações a partir de arquivos JSON de forma robusta
        self.centros_custo = self._carregar_json(self.data_dir / "centros_custo.json", key='centros_custo')
        self.ramos_atividade = self._carregar_json(self.data_dir / "ramos_atividade.json")

    def carregar_dados_cfop(self, arquivo_cfop: str) -> bool:
        """
        Carrega os dados de CFOP a partir de um arquivo CSV ou JSON
        e aplica a normalização na coluna 'cfop'.
        """
        try:
            cfop_path = self.data_dir / arquivo_cfop
            if cfop_path.suffix == '.csv':
                self.cfop_data = pd.read_csv(cfop_path, dtype={'cfop': str})
            elif cfop_path.suffix == '.json':
                with open(cfop_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.cfop_data = pd.DataFrame(data, dtype=str)
            else:
                print(f"❌ Formato de arquivo não suportado: {arquivo_cfop}")
                return False

            # --- CORREÇÃO CRÍTICA ---
            # Normaliza toda a coluna 'cfop' do DataFrame para garantir correspondência.
            if 'cfop' in self.cfop_data.columns:
                self.cfop_data['cfop'] = self.cfop_data['cfop'].apply(self._normalize_cfop)
            # --- FIM DA CORREÇÃO ---

            print(f"✅ Dados CFOP carregados e normalizados: {len(self.cfop_data)} registros")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar dados CFOP: {e}")
            self.cfop_data = None
            return False

    def classificar_documento(self, cfop: str, ramo_empresa: str, dados_documento: Dict) -> Dict:
        """
        Classifica um documento fiscal com base no CFOP (normalizado), ramo de atividade e dados do documento.
        """
        if self.cfop_data is None:
            return {"erro": "A base de dados de CFOPs não está carregada."}

        # Normaliza o CFOP recebido do XML antes de fazer a busca.
        cfop_normalizado = self._normalize_cfop(cfop)

        cfop_info = self.cfop_data[self.cfop_data['cfop'] == cfop_normalizado]

        if cfop_info.empty:
            return {"erro": f"CFOP {cfop_normalizado} (originado de '{cfop}') não encontrado na base de dados."}

        cfop_info = cfop_info.iloc[0].to_dict()
        ramo_config = self.ramos_atividade.get(ramo_empresa, {})
        if not ramo_config:
            return {"erro": f"Ramo de atividade '{ramo_empresa}' não configurado no arquivo ramos_atividade.json."}

        classificacao = {
            'cfop_info': cfop_info,
            'ramo_empresa_detectado': ramo_config.get('nome', ramo_empresa),
            'centro_custo': self._determinar_centro_custo(cfop_normalizado, ramo_config),
            'tipo_documento': self._classificar_tipo_documento(cfop_normalizado, dados_documento),
            'implicacoes_fiscais': [], # Será preenchido pelo agente especializado
            'recomendacoes_arquivamento': [], # Será preenchido pelo agente especializado
            'alertas_especificos': [], # Será preenchido pelo agente especializado
        }
        return classificacao

    def _determinar_centro_custo(self, cfop: str, ramo_config: Dict) -> str:
        """Determina o centro de custo com base nas prioridades e regras do ramo."""
        centros_prioritarios = ramo_config.get('centros_custo_prioritarios', [])

        for centro_nome in centros_prioritarios:
            centro_config = self.centros_custo.get(centro_nome, {})
            if cfop in centro_config.get('cfops_associados', []):
                return centro_config.get('nome', 'Não encontrado')

        # Lógica de fallback baseada no primeiro dígito do CFOP
        primeiro_digito = cfop[0]
        if primeiro_digito in ['1', '2', '3']:
            return 'Compras / Suprimentos'
        elif primeiro_digito in ['5', '6', '7']:
            return 'Comercial / Vendas'

        return 'Administrativo'

    def _classificar_tipo_documento(self, cfop: str, dados_documento: Dict) -> str:
        """Classifica o tipo de documento (Compra, Venda, Serviço, etc.)."""
        primeiro_digito = cfop[0]
        # Pega a descrição do primeiro item para análise
        descricao_item = dados_documento.get('itens', [{}])[0].get('descricao', '').lower()

        if "serviço" in descricao_item or cfop in ["5.933", "6.933", "7.933"]:
            return 'Prestação de Serviço'

        if primeiro_digito in ['1', '2', '3']:
            return 'Compra / Entrada'
        elif primeiro_digito in ['5', '6', '7']:
            return 'Venda / Saída'

        return 'Operação não comercial'