import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import Dict, Any


# Nota: A biblioteca 'pytesseract' requer que o Tesseract-OCR esteja instalado no sistema.
# Consulte a documentação para instalar no seu SO: https://github.com/tesseract-ocr/tesseract

def _run_ocr_on_page(page):
    """Converte uma página de PDF em imagem e executa OCR."""
    zoom = 2  # Aumenta a resolução para melhorar a precisão do OCR
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    img_data = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_data))

    # Executa OCR em português
    return pytesseract.image_to_string(image, lang='por')


def parse_pdf_to_structured_data(file_path: str) -> Dict[str, Any]:
    """
    Extrai texto de um PDF, usando OCR como fallback, e o parseia
    em uma estrutura de dados similar à extração de XML.
    """
    full_text = ""
    try:
        doc = fitz.open(file_path)

        # 1. Tenta extrair texto diretamente
        for page in doc:
            full_text += page.get_text("text")

        # 2. Se o texto for muito curto (sinal de PDF escaneado), usa OCR
        if len(full_text.strip()) < 100:
            print("⚠️ PDF com pouco texto, tentando OCR...")
            full_text = ""
            for page in doc:
                full_text += _run_ocr_on_page(page)

    except Exception as e:
        return {"erro": f"Falha ao ler o arquivo PDF: {str(e)}"}

    if not full_text:
        return {"erro": "Não foi possível extrair nenhum texto do PDF."}

    # 3. Usa Regex para encontrar os campos-chave no texto extraído
    # Expressões regulares aprimoradas para encontrar os dados
    patterns = {
        'chave_acesso': r'\b(\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4})\b',
        'numero_nf': r'(?:NFC-e|NF-e|NOTA FISCAL)\s*n°\s*(\d+)',
        'valor_total': r'(?:VALOR TOTAL|Valor a pagar)\s*R\$\s*([\d\.,]+)',
        'emitente_nome': r'CNPJ:\s*\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\s*([A-Z\s\d&/]+)',
        'emitente_cnpj': r'CNPJ:\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})',
        'cfop': r'\b(\d{4})\b'  # Encontra o primeiro código de 4 dígitos que pode ser um CFOP
    }

    parsed_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            # Limpa e formata o resultado
            value = match.group(1).strip().replace('\n', ' ')
            if key == 'valor_total':
                parsed_data[key] = float(value.replace('.', '').replace(',', '.'))
            elif key == 'chave_acesso':
                parsed_data[key] = re.sub(r'\s', '', value)
            else:
                parsed_data[key] = value
        else:
            parsed_data[key] = None

    # Monta a estrutura final para ser compatível com o resto do sistema
    # Esta é uma simplificação; um parser mais complexo poderia extrair todos os itens.
    cabecalho = {
        'chave_acesso': parsed_data.get('chave_acesso', 'N/A'),
        'numero_nf': parsed_data.get('numero_nf', 'N/A'),
        'data_emissao': 'N/A (Extrair de PDF é complexo)',
        'valor_total': parsed_data.get('valor_total', 0.0),
        'emitente_nome': parsed_data.get('emitente_nome', 'N/A'),
        'emitente_cnpj': parsed_data.get('emitente_cnpj', 'N/A'),
        'emitente_cnae': None,  # CNAE raramente está visível no DANFE PDF
    }

    itens = [{
        'descricao': 'Item extraído de PDF (descrição genérica)',
        'cfop': parsed_data.get('cfop', None),
        'valor_produto': parsed_data.get('valor_total', 0.0)  # Simplificação
    }]

    if not itens[0]['cfop']:
        return {"erro": "Não foi possível extrair o CFOP do PDF."}

    return {"cabecalho": cabecalho, "itens": itens}
