from pathlib import Path
from typing import Dict, Any
import os
import shutil
from datetime import datetime

# Importa os extratores modulares. O orquestrador delega a tarefa de extração,
# mantendo seu próprio código focado no fluxo de trabalho.
from tools.data_extractor import extract_from_xml, extract_data_from_pdf
from agent_analyst.cfop_classifier_agent import CFOPClassifierAgent
from agent_analyst.agronegocio_agent import AgronegocioAgent
from agent_analyst.automotivo_agent import AutomotivoAgent
from agent_analyst.industria_agent import IndustriaAgent
from agent_analyst.generico_agent import GenericoAgent
from agent_analyst.customizacao_agent import CustomizacaoAgent


class OrchestratorAgent:
    """
    Agente Orquestrador.
    Sua principal responsabilidade é gerenciar o fluxo de processamento de um documento fiscal,
    seja individualmente ou em lote, coordenando a extração, inferência e classificação.
    """

    def __init__(self):
        """
        Inicializa o orquestrador, criando uma instância do agente classificador
        e carregando os dados de CFOP necessários para a operação.
        """
        self.classifier_agent = CFOPClassifierAgent(data_dir="data")
        # Carrega os dados do CFOP uma única vez na inicialização para otimizar o desempenho.
        self.classifier_agent.carregar_dados_cfop(self._get_latest_cfop_file())

        # Inicializa os agentes especializados
        self.agentes_especializados = {
            "agronegocio": AgronegocioAgent(data_dir="data"),
            "automotivo": AutomotivoAgent(data_dir="data"),
            "industria": IndustriaAgent(data_dir="data"),
            "customizacao": CustomizacaoAgent(data_dir="data"),
            "comercio": GenericoAgent(ramo_empresa="comercio", data_dir="data"),
            "servicos": GenericoAgent(ramo_empresa="servicos", data_dir="data"),
        }
        self.cnae_ramo_map = self.classifier_agent._carregar_json(Path("data/cnae_ramo_map.json"))

    def _get_latest_cfop_file(self) -> str:
        """
        Encontra o arquivo de dados CFOP mais recente gerado pelo crawler.
        Isso garante que a aplicação sempre use os dados mais atualizados.
        """
        data_dir = Path("data")
        # Procura por arquivos CSV, que é o formato preferencial para o pandas.
        cfop_files = list(data_dir.glob("cfop_confaz_*.csv"))
        if not cfop_files:
            # Lança um erro claro se os dados essenciais não existirem.
            raise FileNotFoundError(
                "Nenhum arquivo de dados CFOP (.csv) encontrado na pasta 'data'. "
                "Por favor, execute o 'tools/crawler.py' primeiro."
            )

        # Encontra o arquivo com a data de modificação mais recente.
        latest_file = max(cfop_files, key=lambda p: p.stat().st_mtime)
        return latest_file.name

    def _inferir_ramo_atividade(self, dados_extraidos: Dict) -> str:
        """
        Tenta inferir o ramo de atividade da empresa a partir dos dados do documento.
        Utiliza o CNAE como fonte primária e o CFOP como fallback.
        """
        cabecalho = dados_extraidos.get('cabecalho', {})
        cnae = cabecalho.get('emitente_cnae')

        # Estratégia 1: Usar o CNAE (o método mais confiável).
        if cnae and self.cnae_ramo_map:
            # Pega os 2 primeiros dígitos do CNAE
            cnae_prefix = cnae[:2]
            ramo_detectado = self.cnae_ramo_map.get(cnae_prefix)
            if ramo_detectado:
                print(f'✅ Ramo detectado via CNAE ({cnae_prefix}): {ramo_detectado}')
                return ramo_detectado

        # Estratégia 2: Usar o CFOP como pista (fallback).
        primeiro_item = dados_extraidos.get("itens", [{}])[0]
        cfop_str = primeiro_item.get("cfop", "")
        if cfop_str:
            cfop_normalizado = self.classifier_agent._normalize_cfop(cfop_str)
            for ramo, config in self.classifier_agent.ramos_atividade.items():
                cfops_comuns = config.get('cfops_entrada_comuns', []) + config.get('cfops_saida_comuns', [])
                if cfop_normalizado in cfops_comuns:
                    print(f'✅ Ramo detectado via CFOP ({cfop_normalizado}): {ramo}')
                    return ramo

        # Estratégia 3: Se nada funcionar, retorna o padrão definido no mapa.
        ramo_padrao = self.cnae_ramo_map.get("default", "comercio")
        print(f'⚠️ Não foi possível detectar o ramo via CNAE ou CFOP. Usando \'{ramo_padrao}\' como padrão.')
        return ramo_padrao

    def processar_documento(self, file_path: str) -> Dict[str, Any]:
        """
        Método que coordena o processamento de um ÚNICO documento fiscal.
        É utilizado pelo dashboard para análises individuais.
        """
        file_path_obj = Path(file_path)
        dados_extraidos = {}

        # Delega a extração ao módulo correto com base na extensão do arquivo.
        if file_path_obj.suffix.lower() == '.xml':
            dados_extraidos = extract_from_xml(file_path)
        elif file_path_obj.suffix.lower() == '.pdf':
            dados_extraidos = extract_data_from_pdf(file_path)
        else:
            return {"erro": f"Formato de arquivo '{file_path_obj.suffix}' não suportado. Use XML ou PDF."}

        # Se a extração falhou, propaga o erro para a interface.
        if "erro" in dados_extraidos:
            return dados_extraidos

        ramo_detectado = self._inferir_ramo_atividade(dados_extraidos)
        primeiro_item = dados_extraidos.get("itens", [{}])[0]
        cfop = primeiro_item.get("cfop")

        if not cfop:
            return {"erro": "Não foi possível encontrar um CFOP no documento para iniciar a classificação."}

        # 1. Classificação base (CFOP, Centro de Custo, Tipo Documento)
        resultado_classificacao = self.classifier_agent.classificar_documento(
            cfop=cfop,
            ramo_empresa=ramo_detectado,
            dados_documento=dados_extraidos
        )

        # 2. Análise setorial customizada pelo agente especializado
        agente_setorial = self.agentes_especializados.get(ramo_detectado)
        if agente_setorial:
            analise_setorial = agente_setorial.analisar_documento(
                cfop=cfop,
                dados_documento=dados_extraidos
            )
            # Mescla os resultados da classificação base com a análise setorial
            resultado_classificacao.update(analise_setorial)
        else:
            print(f'⚠️ Agente especializado para \'{ramo_detectado}\' não encontrado. Usando classificação base.')

        # 3. Análise de customização (setores específicos e mudanças legais)
        agente_customizacao = self.agentes_especializados.get("customizacao")
        analise_customizacao = agente_customizacao.analisar_setor_especifico(dados_extraidos)

        # Adiciona alertas de mudanças legais
        alertas_legais = agente_customizacao.tratar_mudancas_legais(cfop)

        # Mescla os resultados da customização
        resultado_classificacao['alertas_especificos'].extend(analise_customizacao['alertas_customizados'])
        resultado_classificacao['implicacoes_fiscais'].extend(analise_customizacao['implicacoes_customizadas'])
        resultado_classificacao['alertas_especificos'].extend(alertas_legais)
        resultado_classificacao['ramo_especifico_customizado'] = analise_customizacao['ramo_especifico_detectado']

        # Consolida os dados e a análise em um único objeto de resposta.
        return {
            "dados_do_documento": dados_extraidos,
            "analise_classificacao": resultado_classificacao
        }

    def processar_lote_notas(self) -> Dict[str, Any]:
        """
        Processa todos os arquivos .xml e .pdf da pasta 'data/notas',
        classifica-os e os copia para uma estrutura de pastas organizada em 'output/'.
        """
        input_path = Path("data/notas")
        output_path = Path("output")
        erros_path = output_path / "erros"

        if not input_path.exists():
            return {"erro": "A pasta 'data/notas' não foi encontrada. Crie-a e adicione seus arquivos."}

        output_path.mkdir(exist_ok=True)
        erros_path.mkdir(exist_ok=True)

        arquivos_para_processar = list(input_path.glob("*.xml")) + list(input_path.glob("*.pdf"))

        if not arquivos_para_processar:
            return {"info": "Nenhum arquivo .xml ou .pdf encontrado em 'data/notas' para processar."}

        sucesso_count = 0
        falha_count = 0

        print(f'🚀 Iniciando processamento em lote de {len(arquivos_para_processar)} arquivos...')

        for file in arquivos_para_processar:
            try:
                print(f'--- Processando: {file.name} ---')
                resultado = self.processar_documento(str(file))

                # Se houve erro na extração ou classificação, move para a pasta de erros.
                if "erro" in resultado or "erro" in resultado.get('analise_classificacao', {}):
                    erro_msg = resultado.get("erro") or resultado['analise_classificacao'].get("erro")
                    print(f'❌ Falha ao processar {file.name}: {erro_msg}. Arquivo mantido na pasta de entrada.')
                    falha_count += 1
                    continue

                # Determina a pasta de destino com base na classificação.
                analise = resultado['analise_classificacao']
                dados_doc = resultado['dados_do_documento']['cabecalho']

                ramo = analise.get('ramo_empresa_detectado', 'Ramo_Nao_Identificado').replace(" ", "_").capitalize()

                try:
                    data_emissao_str = dados_doc.get('data_emissao', '')
                    ano_mes = datetime.fromisoformat(data_emissao_str).strftime('%Y-%m')
                except (ValueError, TypeError):
                    ano_mes = "Sem_Data_Valida"

                destination_folder = output_path / ramo / ano_mes
                destination_folder.mkdir(parents=True, exist_ok=True)

                shutil.copy(str(file), destination_folder / file.name)
                print(f'✅ Sucesso! {file.name} copiado para {destination_folder}. Arquivo original mantido.')
                sucesso_count += 1

            except Exception as e:
                print(f'💥 Erro fatal ao processar {file.name}: {e}. Arquivo mantido na pasta de entrada.')
                falha_count += 1

        # Retorna um resumo da operação para ser exibido no dashboard.
        return {
            "sucesso": sucesso_count,
            "falhas": falha_count,
            "total": len(arquivos_para_processar),
            "output_path": str(output_path.resolve())
        }