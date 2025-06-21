Auditor Fiscal Inteligente (AFI)

Grupo: Anna_Milene_Jonatas

Integrantes: Anna Luiza Gomes, Millene Gomes e Jonatas Cavalcanti

## Descrição do Projeto
O "Auditor Fiscal Inteligente" (AFI) é uma solução de agente autônomo projetada para transformar a gestão e conformidade fiscal de médias e grandes empresas. Utilizando o poder de Modelos de Linguagem Grandes (LLMs) como o Google Gemini e a estruturação de dados com Pydantic, o AFI automatiza a análise de documentos fiscais, identificando erros, inconsistências e riscos fiscais em tempo real.
O objetivo é converter a área fiscal de um centro de custo reativo para um núcleo de inteligência proativa, reduzindo passivos fiscais e otimizando processos.

## Funcionalidades Chave (Simuladas nesta PoC)
* Análise Estruturada: Recebe dados de notas fiscais (simulados a partir de XML/OCR).
* Auditoria Contínua: Valida cálculos, impostos (ICMS, IPI, PIS, COFINS) e consistência dos dados.
* Geração de Inteligência Acionável: Retorna um diagnóstico claro com status, pontos de atenção e sugestões de correção.
* Resumo Executivo: Fornece uma síntese da análise para gestores e diretores.

## Estrutura do Projeto

```
grupo_i2a2/
├── .env                  # Arquivo para configurar variáveis de ambiente (ex: API Key)
├── .gitignore            # Ignora arquivos sensíveis e desnecessários do Git
├── README.md             # Este arquivo
├── requirements.txt      # Lista de dependências do projeto
|
├── auditor/              # Pacote Python contendo a lógica do agente
│   ├── __init__.py       # Torna 'auditor' um módulo importável
│   └── agent.py          # Define os modelos Pydantic e a configuração do agente AFI
|
└── main.py               # Ponto de entrada: orquestra a execução da análise
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





