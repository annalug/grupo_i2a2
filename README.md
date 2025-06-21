Auditor Fiscal Inteligente (AFI)

Grupo: Anna_Milene_Jonatas

Integrantes: Anna Luiza Gomes, Millene Gomes e Jonatas Cavalcanti

## Descrição do Projeto

## Estrutura do Projeto

```
grupo_i2a2/
├── .env                  # Arquivo para a chave de API
├── .gitignore
├── README.md             # NOVO README para este projeto
├── requirements.txt      # Dependências atualizadas
|
├── data/                 # Pasta para armazenar os arquivos CSV
│   ├── 202401_NFs_Cabecalho.csv
│   └── 202401_NFs_Itens.csv
│
├── agent_analyst/
│   ├── __init__.py
│   └── data_agent.py     # Lógica do agente de análise de dados
│
└── main.py               # Script principal para interagir com o agente
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
GOOGLE_API_KEY="SUA_CHAVE_DE_API_SUPER_SECRETA_VAI_AQUI"
```

## Executando a Simulação
```
python main.py
```





