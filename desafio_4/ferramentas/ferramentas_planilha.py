import os
import pandas as pd
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
import numpy as np


class VRCalculationInput(BaseModel):
    """Input schema para o cálculo de VR."""
    mes: int = Field(description="Mês para o cálculo (1-12)")
    ano: int = Field(description="Ano para o cálculo")


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa e padroniza os nomes das colunas de um DataFrame."""
    cols = df.columns
    new_cols = [col.strip().replace(' ', '_').replace('.', '').lower() for col in cols]
    df.columns = new_cols
    return df


def _consolidar_e_limpar_bases() -> Dict[str, Any]:
    """Etapa 1: Carrega, limpa, prepara e junta todas as planilhas base."""
    try:
        dd = 'dados'
        df_ativos = _normalize_column_names(pd.read_excel(os.path.join(dd, 'ATIVOS.xlsx')))
        df_admissao = _normalize_column_names(pd.read_excel(os.path.join(dd, 'ADMISSÃO ABRIL.xlsx')))
        df_ferias = _normalize_column_names(pd.read_excel(os.path.join(dd, 'FÉRIAS.xlsx')))
        df_desligados = _normalize_column_names(pd.read_excel(os.path.join(dd, 'DESLIGADOS.xlsx')))
        df_sindicato_valor_raw = pd.read_excel(os.path.join(dd, 'Base sindicato x valor.xlsx'))
        df_sindicato_valor_raw.columns = ['estado', 'valor']
        df_sindicato_valor = _normalize_column_names(df_sindicato_valor_raw)
        df_dias_uteis = pd.read_excel(os.path.join(dd, 'Base dias uteis.xlsx'), header=1)
        df_dias_uteis.columns = ['sindicato', 'dias_uteis_base']
        df_dias_uteis = _normalize_column_names(df_dias_uteis)
        df_ativos['sindicato'] = df_ativos['sindicato'].str.strip()
        df_dias_uteis['sindicato'] = df_dias_uteis['sindicato'].str.strip()
        df_sindicato_valor['estado'] = df_sindicato_valor['estado'].str.strip()
        state_map = {'Paraná': 'PR', 'Rio de Janeiro': 'RJ', 'Rio Grande do Sul': 'RS', 'São Paulo': 'SP'}
        df_sindicato_valor['estado_sigla'] = df_sindicato_valor['estado'].map(state_map)
        base = pd.merge(df_ativos, df_admissao[['matricula', 'admissão']], on='matricula', how='left')
        base = pd.merge(base, df_ferias[['matricula', 'dias_de_férias']], on='matricula', how='left')
        base = pd.merge(base, df_desligados, on='matricula', how='left')
        base['dias_de_férias'].fillna(0, inplace=True)
        base = pd.merge(base, df_dias_uteis, on='sindicato', how='left')
        base['estado_ext'] = base['sindicato'].str.extract(r'\b(SP|RS|PR|RJ)\b', expand=False)
        base = pd.merge(base, df_sindicato_valor, left_on='estado_ext', right_on='estado_sigla', how='left')
        return {'status': 'sucesso', 'dataframe': base}
    except Exception as e:
        return {'status': 'erro', 'mensagem': f"Erro na Etapa 1 (Consolidação): {e}"}

def _validar_dados(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Etapa 1.5: Valida a integridade dos dados consolidados antes do cálculo.

    Verifica inconsistências como datas inválidas, campos essenciais faltantes,
    mapeamentos ausentes (sindicato sem valor) e valores ilógicos (férias negativas).

    Args:
        df: O DataFrame consolidado contendo dados de ativos, admissões, férias, etc.

    Returns:
        Um dicionário contendo:
        - 'status': 'sucesso' se nenhum problema foi encontrado, 'aviso' caso contrário.
        - 'dataframe': O DataFrame original, inalterado.
        - 'logs': Uma lista de strings descrevendo cada problema de validação encontrado.
    """
    logs_validacao: List[str] = []

    # --- Validação 1: Datas inconsistentes ou "quebradas" ---
    # Verifica se as colunas de data podem ser convertidas para o formato datetime.
    datas_admissao_invalidas = df[pd.to_datetime(df['admissão'], errors='coerce').isna()]
    if not datas_admissao_invalidas.empty:
        for index, row in datas_admissao_invalidas.iterrows():
            logs_validacao.append(
                f"[AVISO] Matrícula {row['matricula']}: A data de admissão ('{row['admissão']}') é inválida ou está em branco."
            )

    # A data de demissão pode ser opcional (NaN), então só validamos as que existem e são inválidas.
    demissoes_com_data = df[df['data_demissão'].notna()]
    datas_demissao_invalidas = demissoes_com_data[pd.to_datetime(demissoes_com_data['data_demissão'], errors='coerce').isna()]
    if not datas_demissao_invalidas.empty:
        for index, row in datas_demissao_invalidas.iterrows():
            logs_validacao.append(
                f"[AVISO] Matrícula {row['matricula']}: A data de demissão ('{row['data_demissão']}') é inválida."
            )

    # --- Validação 2: Mapeamentos essenciais ausentes ---
    # Verifica se algum colaborador ficou sem 'dias_uteis_base' ou 'valor' de VR após o merge.
    # Isso geralmente indica um erro de digitação no nome do sindicato ou um sindicato não cadastrado.
    sem_dias_uteis = df[df['dias_uteis_base'].isna()]
    if not sem_dias_uteis.empty:
        sindicatos_afetados = sem_dias_uteis['sindicato'].unique()
        logs_validacao.append(
            f"[ERRO] Sindicatos sem 'dias úteis' cadastrados: {list(sindicatos_afetados)}. "
            f"Colaboradores afetados: {sem_dias_uteis['matricula'].tolist()}"
        )

    sem_valor_vr = df[df['valor'].isna()]
    if not sem_valor_vr.empty:
        sindicatos_afetados = sem_valor_vr['sindicato'].unique()
        logs_validacao.append(
            f"[ERRO] Sindicatos sem 'valor de VR' cadastrado: {list(sindicatos_afetados)}. "
            f"Colaboradores afetados: {sem_valor_vr['matricula'].tolist()}"
        )

    # --- Validação 3: Valores numéricos ilógicos ---
    # Verifica se há dias de férias negativos, o que não faz sentido.
    ferias_negativas = df[df['dias_de_férias'] < 0]
    if not ferias_negativas.empty:
        for index, row in ferias_negativas.iterrows():
            logs_validacao.append(
                f"[AVISO] Matrícula {row['matricula']}: Número de dias de férias é negativo ({row['dias_de_férias']})."
            )

    # --- Conclusão da Validação ---
    if logs_validacao:
        status = 'aviso'
        print("\n--- RELATÓRIO DE VALIDAÇÃO DE DADOS ---")
        for log in logs_validacao:
            print(log)
        print("----------------------------------------\n")
    else:
        status = 'sucesso'
        print("\n--- Validação de dados concluída. Nenhum problema encontrado. ---\n")

    return {'status': status, 'dataframe': df, 'logs': logs_validacao}

def _aplicar_exclusoes(df: pd.DataFrame) -> Dict[str, Any]:
    """Etapa 2: Remove matriculas de estagiários, aprendizes e afastados."""
    try:
        dd = 'dados'
        df_estagio = _normalize_column_names(pd.read_excel(os.path.join(dd, 'ESTÁGIO.xlsx')))
        df_aprendiz = _normalize_column_names(pd.read_excel(os.path.join(dd, 'APRENDIZ.xlsx')))
        df_afastados = _normalize_column_names(pd.read_excel(os.path.join(dd, 'AFASTAMENTOS.xlsx')))
        matriculas_excluir = set(
            df_estagio['matricula'].tolist() + df_aprendiz['matricula'].tolist() + df_afastados['matricula'].tolist())
        df_filtrado = df[~df['matricula'].isin(matriculas_excluir)]
        return {'status': 'sucesso', 'dataframe': df_filtrado}
    except Exception as e:
        return {'status': 'erro', 'mensagem': f"Erro na Etapa 2 (Exclusões): {e}"}


def _calcular_dias_pagaveis(df: pd.DataFrame, mes: int, ano: int) -> Dict[str, Any]:
    """Etapa 3: Calcula os dias a serem pagos com base nas regras de negócio."""
    try:
        df['data_admissão'] = pd.to_datetime(df['admissão'], errors='coerce')
        df['data_demissão'] = pd.to_datetime(df['data_demissão'], errors='coerce')
        df['dias_pagaveis'] = df['dias_uteis_base']
        df['dias_pagaveis'] -= df['dias_de_férias']
        for i, row in df.iterrows():
            if pd.notna(row['data_demissão']) and row['comunicado_de_desligamento'] == 'OK' and row[
                'data_demissão'].day <= 15:
                df.loc[i, 'dias_pagaveis'] = 0
                continue
            if pd.notna(row['data_admissão']) and row['data_admissão'].month == mes and row[
                'data_admissão'].year == ano:
                data_fim_mes = (datetime(ano, mes, 1) + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
                dias_uteis_reais = np.busday_count(row['data_admissão'].date(),
                                                   (data_fim_mes + pd.DateOffset(days=1)).date())
                df.loc[i, 'dias_pagaveis'] = dias_uteis_reais - row['dias_de_férias']
        df['dias_pagaveis'] = df['dias_pagaveis'].clip(lower=0)
        return {'status': 'sucesso', 'dataframe': df}
    except Exception as e:
        return {'status': 'erro', 'mensagem': f"Erro na Etapa 3 (Cálculo de Dias): {e}"}


def _calcular_valores_finais(df: pd.DataFrame) -> Dict[str, Any]:
    """Etapa 4: Calcula os valores financeiros finais."""
    try:
        df['valor_total_vr'] = df['dias_pagaveis'] * df['valor']
        df['custo_empresa_80'] = df['valor_total_vr'] * 0.80
        df['desconto_colaborador_20'] = df['valor_total_vr'] * 0.20
        return {'status': 'sucesso', 'dataframe': df}
    except Exception as e:
        return {'status': 'erro', 'mensagem': f"Erro na Etapa 4 (Cálculo de Valores): {e}"}


def _gerar_planilha_final(df: pd.DataFrame, mes: int, ano: int) -> Dict[str, Any]:
    """
    Etapa 5: Gera a planilha de saída final com base no modelo especificado.

    A planilha contém duas abas:
    1.  'VR Mensal MM-AAAA': Detalhamento por colaborador, espelhando o layout final.
    2.  'Resumo Totalizador': Soma dos valores totais para facilitar a conferência.

    Args:
        df: O DataFrame final, já com todos os cálculos de valores realizados.
        mes: O mês de competência do cálculo.
        ano: O ano de competência do cálculo.

    Returns:
        Um dicionário com o status da operação e uma mensagem para o usuário.
    """
    try:
        # --- Preparação do DataFrame para o Layout Final ---
        df_final = df.copy()

        # Adicionar colunas que não existem no DataFrame original, mas são necessárias no output
        df_final['Competência'] = f"{mes:02d}/{ano}"
        df_final['OBS GERAL'] = ''  # Coluna de observações, vazia por padrão
        df_final['Admissão'] = pd.to_datetime(df_final['admissão'], errors='coerce').dt.strftime('%d/%m/%Y')

        # Mapeamento explícito das colunas do DataFrame para as colunas da planilha final
        mapeamento_colunas = {
            'matricula': 'Matrícula',
            'Admissão': 'Admissão',
            'sindicato': 'Sindicato do Colaborador',
            'Competência': 'Competência',
            'dias_pagaveis': 'Dias',
            'valor': 'VALOR DIÁRIO VR',
            'valor_total_vr': 'TOTAL',
            'custo_empresa_80': 'Custo empresa',
            'desconto_colaborador_20': 'Desconto profissional',
            'OBS GERAL': 'OBS GERAL'
        }

        # Garantir que todas as colunas necessárias existam antes de prosseguir
        colunas_fonte = list(mapeamento_colunas.keys())
        for col in colunas_fonte:
            if col not in df_final.columns:
                return {'status': 'erro',
                        'mensagem': f"Erro Crítico: A coluna fonte '{col}' não foi encontrada no DataFrame."}

        # Selecionar, ordenar e renomear as colunas
        df_layout_final = df_final[colunas_fonte].rename(columns=mapeamento_colunas)

        # --- Geração da Aba de Resumo ---
        total_vr = df_layout_final['TOTAL'].sum()
        total_custo_empresa = df_layout_final['Custo empresa'].sum()
        total_desconto = df_layout_final['Desconto profissional'].sum()

        dados_resumo = {
            'Descrição': ['Valor Total a Pagar (VR)', 'Custo Total para a Empresa (80%)',
                          'Desconto Total dos Colaboradores (20%)'],
            'Valor Total (R$)': [total_vr, total_custo_empresa, total_desconto]
        }
        df_resumo = pd.DataFrame(dados_resumo)

        # --- Geração do Arquivo Excel ---
        nome_arquivo = f'VR_Mensal_{mes:02d}_{ano}_FINAL.xlsx'
        caminho_saida = os.path.join('dados', nome_arquivo)

        with pd.ExcelWriter(caminho_saida, engine='xlsxwriter') as writer:
            nome_aba_detalhe = f'VR Mensal {mes:02d}-{ano}'
            df_layout_final.to_excel(writer, sheet_name=nome_aba_detalhe, index=False)
            df_resumo.to_excel(writer, sheet_name='Resumo Totalizador', index=False)

            # --- Formatação da Planilha ---
            workbook = writer.book
            worksheet_detalhe = writer.sheets[nome_aba_detalhe]
            worksheet_resumo = writer.sheets['Resumo Totalizador']

            # Formatos de célula
            formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00'})
            formato_centralizado = workbook.add_format({'align': 'center'})

            # Aplicar formatação na aba de detalhes
            worksheet_detalhe.set_column('A:A', 12, formato_centralizado)  # Matrícula
            worksheet_detalhe.set_column('B:B', 12, formato_centralizado)  # Admissão
            worksheet_detalhe.set_column('C:C', 45)  # Sindicato
            worksheet_detalhe.set_column('D:D', 12, formato_centralizado)  # Competência
            worksheet_detalhe.set_column('E:E', 8, formato_centralizado)  # Dias
            worksheet_detalhe.set_column('F:H', 18, formato_moeda)  # Colunas de valor
            worksheet_detalhe.set_column('I:I', 22, formato_moeda)  # Colunas de valor
            worksheet_detalhe.set_column('J:J', 20)  # OBS GERAL

            # Aplicar formatação na aba de resumo
            worksheet_resumo.set_column('A:A', 40)
            worksheet_resumo.set_column('B:B', 25, formato_moeda)

        return {'status': 'sucesso', 'mensagem': f'Planilha final gerada com sucesso em: {caminho_saida}'}

    except Exception as e:
        return {'status': 'erro', 'mensagem': f"Erro na Etapa 5 (Geração da Planilha Final): {e}"}


class ProcessarCalculoVRTool(BaseTool):
    """
    Ferramenta para processar o cálculo completo de VR.
    """
    name: str = "processar_calculo_vr_completo"
    description: str = """
    Executa o processo completo de cálculo de VR para um determinado mês e ano.
    Esta ferramenta consolida as bases, aplica exclusões, calcula dias e valores,
    e gera a planilha final de uma só vez.

    Use esta ferramenta quando precisar calcular o VR mensal.
    """
    args_schema: type = VRCalculationInput

    def _run(self, mes: int, ano: int) -> str:
        """Executa o cálculo de VR."""
        print(f"\n--- INICIANDO PROCESSAMENTO COMPLETO PARA {mes}/{ano} ---")

        etapa1 = _consolidar_e_limpar_bases()
        if etapa1['status'] == 'erro':
            return etapa1['mensagem']
        df = etapa1['dataframe']

        etapa2 = _aplicar_exclusoes(df)
        if etapa2['status'] == 'erro':
            return etapa2['mensagem']
        df = etapa2['dataframe']

        etapa3 = _calcular_dias_pagaveis(df, mes, ano)
        if etapa3['status'] == 'erro':
            return etapa3['mensagem']
        df = etapa3['dataframe']

        etapa4 = _calcular_valores_finais(df)
        if etapa4['status'] == 'erro':
            return etapa4['mensagem']
        df = etapa4['dataframe']

        resultado_final = _gerar_planilha_final(df, mes, ano)
        print("--- PROCESSAMENTO COMPLETO CONCLUÍDO ---")

        return resultado_final['mensagem']


# Instância da ferramenta para ser usada no agente
processar_calculo_vr_completo = ProcessarCalculoVRTool()