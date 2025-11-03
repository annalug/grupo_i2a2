import xml.etree.ElementTree as ET
from typing import Dict, Any

# --- NOVO IMPORT MODULAR ---
from tools.pdf_parser import parse_pdf_to_structured_data

NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

def extract_from_xml(file_path: str) -> Dict[str, Any]:
    """Extrai dados de um arquivo XML de NF-e, incluindo o CNAE."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        infNFe = root.find('.//nfe:infNFe', NS)
        if infNFe is None:
            return {"erro": "Estrutura do XML da NF-e não encontrada."}

        ide = infNFe.find('nfe:ide', NS)
        emit = infNFe.find('nfe:emit', NS)
        dest = infNFe.find('nfe:dest', NS)
        total = infNFe.find('nfe:total/nfe:ICMSTot', NS)

        header_data = {
            'chave_acesso': infNFe.attrib.get('Id', '').replace('NFe', ''),
            'numero_nf': ide.findtext('nfe:nNF', namespaces=NS),
            'data_emissao': ide.findtext('nfe:dhEmi', namespaces=NS),
            'valor_total': float(total.findtext('nfe:vNF', default=0, namespaces=NS)),
            'emitente_nome': emit.findtext('nfe:xNome', namespaces=NS),
            'emitente_cnpj': emit.findtext('nfe:CNPJ', namespaces=NS),
            'emitente_cnae': emit.findtext('nfe:CNAE', namespaces=NS), # Importante para detecção de ramo
            'destinatario_nome': dest.findtext('nfe:xNome', namespaces=NS),
            'destinatario_cpf_cnpj': dest.findtext('nfe:CPF', namespaces=NS) or dest.findtext('nfe:CNPJ', namespaces=NS),
        }

        items_data = []
        for det in infNFe.findall('nfe:det', NS):
            prod = det.find('nfe:prod', NS)
            item = {
                'numero_item': det.attrib.get('nItem'),
                'codigo_produto': prod.findtext('nfe:cProd', namespaces=NS),
                'descricao': prod.findtext('nfe:xProd', namespaces=NS),
                'cfop': prod.findtext('nfe:CFOP', namespaces=NS),
                'quantidade': float(prod.findtext('nfe:qCom', default=0, namespaces=NS)),
                'valor_unitario': float(prod.findtext('nfe:vUnCom', default=0, namespaces=NS)),
                'valor_produto': float(prod.findtext('nfe:vProd', default=0, namespaces=NS)),
            }
            items_data.append(item)

        return {"cabecalho": header_data, "itens": items_data}

    except Exception as e:
        return {"erro": f"Falha ao processar o XML: {str(e)}"}

# --- FUNÇÃO ATUALIZADA ---
def extract_data_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Função de fachada que chama o parser de PDF dedicado.
    Mantém a interface do extrator consistente.
    """
    print("🚀 Iniciando extração de dados do PDF...")
    return parse_pdf_to_structured_data(file_path)