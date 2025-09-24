Agente de Análise de Notas Fiscais com Gemini AI

Grupo: Anna_Milene_Jonatas

Integrantes: Anna Luiza Gomes, Millene Gomes e Jonatas Cavalcanti

## Descrição do Projeto

Funcionalidades:
* Processamento Automatizado de arquivos CSV contendo:

* Cabeçalhos de notas fiscais

* Itens detalhados de cada nota

* Análise Inteligente via Gemini AI para:

* Identificar fornecedores com maior volume

* Detectar itens mais transacionados

* Analisar padrões geográficos

* Flaggar transações relevantes

Integração Total com a API oficial do Google Gemini
## Estrutura do Projeto

```
grupo_i2a2/
├── .env                          # Configurações de ambiente
├── .gitignore                    # Arquivos ignorados pelo Git
├── README.md                     # Documentação do projeto
├── requirements.txt              # Dependências Python
├── dashboard.py                  # Interface Streamlit
│
├── data/                         # Dados das notas fiscais
│
└── agent_analyst/               # Módulo do agente
    ├── __init__.py
    └── orchestrator_agent.py    # Lógica principal do agente
```

## Como Executar o Projeto

Siga os passos abaixo para configurar e executar o agente em sua máquina local.

Pré-requisitos:
* Python 3.10+;
* pyenv (recomendado para gerenciamento de versões Python);
* Uma Chave de API do Google para acesso ao modelo Gemini;

## Passo a Passo da Instalação

1. Clone o Repositório

```
git clone <URL_DO_SEU_REPOSITORIO>
cd grupo_i2a2
```

2. Crie e Ative um Ambiente Virtual
```
# Crie o ambiente (ex: com python 3.10.4)
pyenv virtualenv 3.10.4 agent_project

# Ative o ambiente para esta pasta
pyenv local agent_project
```

3. Instale as Dependências
```
pip install -r requirements.txt
```

4. Configure sua Chave de API
Crie um arquivo chamado .env na raiz do projeto
```
# .env
GROQ_API_KEY="SUA_CHAVE_DE_API"
```
Certifique-se de que os arquivo .zip de dados esta na pasta /data
## Executando a Simulação
Como Utilizar:
* Configure sua chave API no arquivo .env

* Coloque seus arquivos CSV na pasta /data

* Execute o Dashboard Interativo

```
streamlit run dashboard.py
```
O sistema abrirá no navegador (geralmente http://localhost:8501).


🛠️ Tecnologias Utilizadas:

* 🐍 Python 3.10+ - Linguagem principal
* 🤖 PydanticAI - Framework para agentes de IA
* ⚡ Groq API - Modelos de linguagem rápidos
* 🎨 Streamlit - Interface web interativa
* 📊 Pandas - Processamento de dados
* 🔧 Python-dotenv - Gerenciamento de variáveis de ambiente

📊 Dados do Projeto
O sistema trabalha com 100 notas fiscais do período de janeiro/2024, contendo:

- Cabeçalho: Informações principais (emissor, valor, data, etc.)
- Itens: Produtos detalhados de cada nota fiscal
- Relacionamento: Ligação via "CHAVE DE ACESSO"


