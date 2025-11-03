# tools/crawler.py
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import csv
import json
import urllib3
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path  # Importar a biblioteca Path

# Desabilitar warnings de SSL (apenas para desenvolvimento)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CFOPConfazCrawler:
    def __init__(self):
        self.urls = [
            "https://www.confaz.fazenda.gov.br/legislacao/ajustes/sinief/cfop_cvsn_70_vigente",
            "http://www.confaz.fazenda.gov.br/legislacao/ajustes/sinief/cfop_cvsn_70_vigente",  # HTTP como fallback
        ]

        # --- CORREÇÃO APLICADA AQUI ---
        # Constrói o caminho para a pasta 'data' de forma robusta.
        # 1. Pega o caminho do arquivo atual (__file__), que é '.../tools/crawler.py'
        # 2. .parent pega o diretório pai, que é a pasta '.../tools'
        # 3. .parent novamente sobe para o diretório raiz do projeto, que é '.../grupo_i2a2'
        # 4. / "data" anexa a pasta de dados.
        # O resultado final é o caminho absoluto e correto para '.../grupo_i2a2/data'
        project_root = Path(__file__).parent.parent
        self.data_dir = project_root / "data"
        os.makedirs(self.data_dir, exist_ok=True)
        # --- FIM DA CORREÇÃO ---

        # Configurar sessão com retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br'
        }

    def tentar_conexao_segura(self):
        """Tenta diferentes métodos de conexão"""
        estrategias = [
            {'verify': True},  # Tentativa padrão
            {'verify': False},  # Sem verificação SSL
        ]

        # Tentar caminhos de certificados comuns se os básicos falharem
        if Path('/etc/ssl/certs/ca-certificates.crt').exists():
            estrategias.append({'verify': '/etc/ssl/certs/ca-certificates.crt'})
        if Path('cacert.pem').exists():
            estrategias.append({'verify': 'cacert.pem'})

        for url in self.urls:
            for estrategia in estrategias:
                try:
                    print(f"🔗 Tentando {url} com verify={estrategia['verify']}...")
                    response = self.session.get(
                        url,
                        headers=self.headers,
                        timeout=30,
                        **estrategia
                    )
                    response.raise_for_status()
                    print(f"✅ Conexão bem-sucedida com {url}")
                    return response
                except Exception as e:
                    print(f"❌ Falha: {e}")
                    continue

        return None

    def extrair_cfop_confaz(self):
        try:
            print("🌐 Conectando ao CONFAZ...")
            response = self.tentar_conexao_segura()

            if not response:
                print("🚨 Todas as tentativas de conexão falharam.")
                return None

            print("📖 Parseando HTML...")
            soup = BeautifulSoup(response.content, 'html.parser')

            # Estratégias para encontrar o conteúdo
            seletores = [
                'div#content',
                'div.content',
                'div.texto',
                'div.A8-3RedacaoAnt',
                'div.main-content',
                'body'
            ]

            secao_principal = None
            for seletor in seletores:
                elemento = soup.select_one(seletor)
                if elemento and len(elemento.get_text(strip=True)) > 500:  # Heurística para pegar conteúdo relevante
                    secao_principal = elemento
                    print(f"✅ Encontrado conteúdo com seletor: {seletor}")
                    break

            if not secao_principal:
                secao_principal = soup
                print("⚠️ Seletor específico não encontrado, usando o corpo do HTML completo.")

            return self._parsear_cfops(secao_principal)

        except Exception as e:
            print(f"❌ Erro geral na extração: {e}")
            return None

    def _parsear_cfops(self, secao):
        cfops_dict = {}  # Usar um dicionário para evitar duplicatas de código

        # Padrão regex para encontrar códigos e descrições
        padrao_cfop = re.compile(r'(\d\.\d{3})\s*[-–—]\s*(.+?)(?=\s*\d\.\d{3}\s*[-–—]|$)', re.DOTALL)

        texto_completo = secao.get_text(separator=' ')
        matches = padrao_cfop.findall(texto_completo)

        print(f"🔍 Encontrados {len(matches)} possíveis CFOPs...")

        for codigo, descricao in matches:
            codigo = codigo.strip()

            # Limpeza avançada da descrição
            descricao_limpa = re.sub(r'\s+', ' ', descricao).strip()
            descricao_limpa = re.sub(r'Redação.*?(?=Classificam-se|$)', '', descricao_limpa, flags=re.IGNORECASE)
            descricao_limpa = re.sub(r'Classificam-se neste código.*?(?=\d\.\d{3}|$)', '', descricao_limpa,
                                     flags=re.IGNORECASE)
            descricao_limpa = descricao_limpa.strip()

            # Se o código já existe, só atualizamos se a nova descrição for maior (mais completa)
            if codigo not in cfops_dict or len(descricao_limpa) > len(cfops_dict[codigo]['descricao']):
                primeiro_digito = codigo[0]
                if primeiro_digito in ['1', '2', '3']:
                    tipo = 'Entrada'
                elif primeiro_digito in ['5', '6', '7']:
                    tipo = 'Saída'
                else:
                    tipo = 'Outro'

                cfops_dict[codigo] = {
                    'cfop': codigo,
                    'descricao': descricao_limpa,
                    'tipo_operacao': tipo,
                    'fonte': 'CONFAZ',
                    'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

        cfops = sorted(list(cfops_dict.values()), key=lambda x: [int(part) for part in x['cfop'].split('.')])

        print(f"✅ Processados {len(cfops)} CFOPs únicos.")
        return cfops

    def salvar_csv(self, cfops, filename=None):
        if not cfops: return None
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'cfop_confaz_{timestamp}.csv'

        filepath = self.data_dir / filename  # Usando Path para juntar caminhos

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['cfop', 'descricao', 'tipo_operacao', 'fonte', 'data_extracao']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cfops)

        print(f"💾 CSV salvo em: {filepath}")
        return filepath

    def salvar_json(self, cfops, filename=None):
        if not cfops: return None
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'cfop_confaz_{timestamp}.json'

        filepath = self.data_dir / filename  # Usando Path para juntar caminhos

        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(cfops, jsonfile, ensure_ascii=False, indent=2)

        print(f"💾 JSON salvo em: {filepath}")
        return filepath

    def mostrar_estatisticas(self, cfops):
        if not cfops:
            print("❌ Nenhum CFOP para exibir estatísticas.")
            return

        print(f"\n📊 ESTATÍSTICAS DA EXTRAÇÃO:")
        print(f"📋 Total de CFOPs únicos: {len(cfops)}")

        tipos = {}
        for cfop in cfops:
            tipo = cfop['tipo_operacao']
            tipos[tipo] = tipos.get(tipo, 0) + 1

        for tipo, quantidade in tipos.items():
            print(f"  {tipo}: {quantidade} CFOPs")

        print(f"\n📝 Primeiros 3 CFOPs:")
        for cfop in cfops[:3]:
            print(f"  {cfop['cfop']} - {cfop['descricao'][:70]}...")

        print(f"\n📝 Últimos 3 CFOPs:")
        for cfop in cfops[-3:]:
            print(f"  {cfop['cfop']} - {cfop['descricao'][:70]}...")


# Execução principal
def main():
    print("🚀 Iniciando extração de CFOPs do CONFAZ...")

    crawler = CFOPConfazCrawler()
    cfops = crawler.extrair_cfop_confaz()

    if cfops:
        crawler.mostrar_estatisticas(cfops)
        csv_file = crawler.salvar_csv(cfops)
        json_file = crawler.salvar_json(cfops)

        print(f"\n🎯 Extração concluída!")
        if csv_file and json_file:
            print(f"📁 Arquivos gerados na pasta 'data':")
            print(f"   - {Path(csv_file).name}")
            print(f"   - {Path(json_file).name}")
    else:
        print("❌ Falha completa na extração. Nenhum arquivo foi gerado.")


if __name__ == "__main__":
    main()