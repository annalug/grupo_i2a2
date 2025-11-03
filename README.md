🤖 Analisador e Classificador Inteligente de Documentos Fiscais 

Este projeto foi aprimorado para incorporar uma arquitetura de Agentes Especializados, permitindo uma classificação, categorização e análise fiscal customizada por ramo de atividade, conforme as especificações de negócio.

✨ Funcionalidades Aprimoradas

O sistema agora utiliza uma arquitetura de agentes que orquestra a extração de dados, a classificação base e a análise setorial especializada.

Funcionalidade:

* Classificação Automática - Determina o tipo de documento (Compra, Venda, Serviço) e sugere o centro de custo.
* Detecção de Ramo - Identifica o setor da empresa (Indústria, Comércio, Agronegócio, etc.) via CNAE.
* Análise Setorial Customizada - Fornece implicações fiscais, alertas e recomendações específicas para o ramo detectado.
* Customização Setorial - Trata ramos de atividade específicos (órgãos públicos, terceiro setor) e adapta-se a mudanças legais.
* Organização de Arquivos - Processa e move notas fiscais para uma estrutura organizada.
* Dashboard Interativo - Interface web para análise individual e processamento em lote.
* Crawler de CFOPs - Busca e atualiza a base de dados de CFOPs do CONFAZ.


🏗️ Estrutura do Projeto

A arquitetura é modular, separando as responsabilidades de extração de dados, classificação e orquestração do fluxo.

````
grupo_i2a2/
├── dashboard.py                  # 🚀 Interface principal com Streamlit
├── README.md                     # Este arquivo
├── requirements.txt              # Dependências Python
│
├── data/
│   ├── notas/                    # 📂 PASTA DE ENTRADA para processamento em lote
│   ├── centros_custo.json        # ⚙️ Configurações de Centros de Custo
│   ├── ramos_atividade.json      # ⚙️ Configurações de Ramo de Atividade
│   └── cnae_ramo_map.json        # ⚙️ Mapeamento CNAE -> Ramo (NOVO)
│
├── output/
│   └── ...                       # 🗂️ PASTAS DE SAÍDA
│
├── agent_analyst/                # 🧠 Módulo dos agentes
│   ├── base_agent.py             # 💡 Classe base com utilitários (NOVO)
│   ├── orchestrator_agent.py     # 🤖 Orquestra o fluxo de trabalho (ATUALIZADO)
│   ├── cfop_classifier_agent.py  # 🧠 Lógica de classificação base (ATUALIZADO)
│   ├── agronegocio_agent.py      # 🧑‍🌾 Agente especialista Agronegócio (NOVO)
│   ├── automotivo_agent.py       # 🚗 Agente especialista Setor Automotivo (NOVO)
│   ├── industria_agent.py        # 🏭 Agente especialista Indústria (NOVO)
│   ├── generico_agent.py         # 🛒 Agente especialista Comércio/Serviços (NOVO)
│   └── customizacao_agent.py     # ⚖️ Agente para setores específicos e mudanças legais (NOVO)
│
└── tools/                        # 🛠️ Ferramentas de suporte
    ├── crawler.py                # 🕸️ Crawler para dados de CFOP
    ├── data_extractor.py         # 🔍 Módulo que decide entre parser XML ou PDF
    └── pdf_parser.py             # 📄 Módulo de extração de dados de PDF (com OCR)
````

🚀 Como Executar o Projeto

Siga os passos abaixo para configurar e executar o agente em sua máquina local.
Pré-requisitos

* Python 3.10+

* Git

* Tesseract-OCR Engine: Essencial para o processamento de PDFs.
````
        Linux (Debian/Ubuntu): sudo apt install tesseract-ocr tesseract-ocr-por

        Windows: Baixe e instale a partir do instalador oficial.

        macOS: brew install tesseract
````

Passo a Passo da Instalação

1. Clone o Repositório
````
git clone <URL_DO_SEU_REPOSITORIO>
cd grupo_i2a2
````

2. Crie e Ative um Ambiente Virtual
````
# Crie o ambiente
python -m venv .venv

# Ative o ambiente
# Windows:
# .\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
````

3. Instale as Dependências Python
````
pip install -r requirements.txt
````

4. Atualize a Base de Dados de CFOPs
````
python tools/crawler.py
````

Como Utilizar:

1. Para Processamento em Lote:

* Crie a pasta data/notas/ se ela não existir.

* Coloque quantos arquivos .xml e .pdf desejar dentro dela.

* Execute o Dashboard e, na barra lateral, clique no botão "Organizar Notas em Lote".

2. Para Análise Individual:

* Execute o Dashboard e use a área de upload na página principal para enviar um único arquivo .xml ou .pdf.
  
## 📝 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

Você é livre para usar, modificar e distribuir este software sob os termos da licença MIT.