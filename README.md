Auditor Fiscal Inteligente (AFI)

Grupo: Anna_Milene_Jonatas

Integrantes: Anna Luiza Gomes, Millene Gomes e Jonatas Cavalcanti

## Descrição do Projeto
O "Auditor Fiscal Inteligente" (AFI) é uma solução de agente autônomo projetada para transformar a gestão e conformidade fiscal de médias e grandes empresas. Utilizando o poder de Modelos de Linguagem Grandes (LLMs) como o Google Gemini e a estruturação de dados com Pydantic, o AFI automatiza a análise de documentos fiscais, identificando erros, inconsistências e riscos fiscais em tempo real.
O objetivo é converter a área fiscal de um centro de custo reativo para um núcleo de inteligência proativa, reduzindo passivos fiscais e otimizando processos.

## Funcionalidades Chave (Simuladas nesta PoC)
Análise Estruturada: Recebe dados de notas fiscais (simulados a partir de XML/OCR).
Auditoria Contínua: Valida cálculos, impostos (ICMS, IPI, PIS, COFINS) e consistência dos dados.
Geração de Inteligência Acionável: Retorna um diagnóstico claro com status, pontos de atenção e sugestões de correção.
Resumo Executivo: Fornece uma síntese da análise para gestores e diretores.

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

