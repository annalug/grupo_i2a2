
import pandas as pd
from pathlib import Path
import zipfile
import nest_asyncio

from langchain_groq import ChatGroq
from langchain.tools import Tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


nest_asyncio.apply()


class OrchestratorAgent:
    def __init__(self, model_name: str = 'llama3-70b-8192'):  # Modelo válido da Groq
        self.data_path = Path("data")
        self.df_cabecalho = None
        self.df_itens = None
        self.is_data_prepared = False

        # Initialize the LangChain LLM with valid model
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=0,
            max_tokens=8192  # Ajustado para o novo modelo
        )

        self.base_system_prompt = """
        Você é um especialista em análise de dados de notas fiscais eletrônicas (NF-e).

        Você tem acesso a DOIS DataFrames principais:
        - **df_cabecalho**: Dados do cabeçalho das notas fiscais (uma linha por nota)
        - **df_itens**: Dados dos itens das notas fiscais (múltiplas linhas por nota)

        **REGRAS FUNDAMENTAIS:**

        1. **Para contar NOTAS FISCAIS únicamente:**
           - Use: `df_cabecalho.shape[0]` ou `len(df_cabecalho)`
           - NUNCA use df_itens para contar notas (contém itens, não notas)

        2. **Para valor total das notas:**
           - Use: `df_cabecalho['VALOR NOTA FISCAL'].sum()`

        3. **Para análises de itens:**
           - Use df_itens para produtos, quantidades, etc.
           - Combine com df_cabecalho via merge quando necessário

        4. **Sempre use a ferramenta safe_cross_query para executar consultas.**
           Para usar a ferramenta, chame `safe_cross_query("SEU CÓDIGO PYTHON AQUI")`.

        **EXEMPLOS CORRETOS DE USO DA FERRAMENTA:**
        - "Quantas notas fiscais?" → safe_cross_query("len(df_cabecalho)")
        - "Valor total?" → safe_cross_query("df_cabecalho['VALOR NOTA FISCAL'].sum()")
        - "Produto mais vendido?" → safe_cross_query("df_itens['DESCRIÇÃO DO PRODUTO/SERVIÇO'].value_counts().head(1)")

        Sempre responda em Português do Brasil e seja preciso com os números.
        """

        # Define the tool for LangChain
        # safe_cross_query is now an instance method so it can access self.df_cabecalho and self.df_itens
        tools = [
            Tool(
                name="safe_cross_query",
                func=self.safe_cross_query, # Bind method to instance
                description="""
                Executa consultas seguras nos DataFrames 'df_cabecalho' (dados do cabeçalho) 
                e 'df_itens' (dados dos itens).
                Forneça a string completa do código Python como entrada.
                Exemplo: safe_cross_query("len(df_cabecalho)")
                """
            )
        ]

        # Create the prompt template for the LangChain agent
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.base_system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True), # For conversation memory, if implemented
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"), # For tool calls and observations
        ])

        # Create the LangChain agent
        self.agent = create_tool_calling_agent(self.llm, tools, self.prompt)

        # Create the Agent Executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=True, # Set to True to see agent's thought process
            handle_parsing_errors=True # Allows agent to recover from parsing errors
        )


    # Removed @staticmethod as it now accesses self.df_cabecalho and self.df_itens
    def safe_cross_query(self, query: str) -> str:
        """
        Executa consultas seguras nos DataFrames de notas fiscais.

        Args:
            query: Código Python para executar
        """
        try:
            # Ensure dataframes are loaded before querying
            if self.df_cabecalho is None or self.df_itens is None:
                raise ValueError("DataFrames df_cabecalho ou df_itens não foram carregados. Chame _prepare_data primeiro.")

            print(f"🔍 Executando consulta: {query}")

            df_cabecalho = self.df_cabecalho
            df_itens = self.df_itens

            # Ambiente seguro para eval
            safe_globals = {
                '__builtins__': {},
                'df_cabecalho': df_cabecalho,
                'df_itens': df_itens,
                'pd': pd,
                'len': len,
                'sum': sum,
                'max': max,
                'min': min
            }

            # Executar a consulta
            resultado = eval(query, safe_globals, {})

            # Formatar resultado baseado no tipo
            if isinstance(resultado, pd.Series):
                if len(resultado) <= 10:
                    formatted_result = resultado.to_string()
                else:
                    formatted_result = f"{resultado.head(10).to_string()}\n... (mostrando apenas os primeiros 10)"
            elif isinstance(resultado, pd.DataFrame):
                if len(resultado) <= 20:
                    formatted_result = resultado.to_string(index=False)
                else:
                    formatted_result = f"{resultado.head(20).to_string(index=False)}\n... (mostrando apenas as primeiras 20 linhas)"
            else:
                formatted_result = str(resultado)

            return f"""📊 **Resultado da Consulta:**

{formatted_result}

💻 **Código executado:**
```python
{query}
```"""

        except Exception as e:
            error_details = f"Erro ao executar '{query}': {str(e)}"
            print(f"❌ {error_details}")

            # Sugestões de correção baseadas em erros comuns
            suggestions = []
            if "KeyError" in str(e):
                suggestions.append("Verifique se o nome da coluna está correto")
            if "AttributeError" in str(e):
                suggestions.append("Verifique se está usando o DataFrame correto (df_cabecalho ou df_itens)")

            suggestion_text = "\n🔧 Sugestões: " + "; ".join(suggestions) if suggestions else ""

            # Raise a standard Exception, which AgentExecutor will catch and pass as an observation
            raise ValueError(f"Tool execution failed: {error_details}{suggestion_text}") from e

    def _prepare_data(self, zip_filename: str, cabecalho_filename: str, itens_filename: str):
        """Prepara e carrega os dados das notas fiscais"""
        if self.is_data_prepared:
            return

        print("🔄 Preparando dados das notas fiscais...")

        # Caminhos dos arquivos
        zip_path = self.data_path / zip_filename
        path_cabecalho = self.data_path / cabecalho_filename
        path_itens = self.data_path / itens_filename

        # Descompactar se necessário
        if not path_cabecalho.exists() or not path_itens.exists():
            if not zip_path.exists():
                raise FileNotFoundError(f"Arquivo ZIP não encontrado: {zip_path}")

            print("📦 Descompactando arquivos...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.data_path)

        # Função auxiliar para detectar delimitador
        def detect_delimiter(file_path):
            with open(file_path, 'r') as f:
                first_line = f.readline()
            return ';' if ';' in first_line else ','

        try:
            # Carregar DataFrame do cabeçalho com tratamento robusto
            print("📄 Carregando dados do cabeçalho...")
            cab_delimiter = detect_delimiter(path_cabecalho)
            self.df_cabecalho = pd.read_csv(
                path_cabecalho,
                sep=cab_delimiter,
                decimal='.',
                dtype={'CHAVE DE ACESSO': str},
                parse_dates=['DATA EMISSÃO'],
                on_bad_lines='warn'  # Apenas avisa sobre linhas problemáticas
            )

            # Carregar DataFrame dos itens com tratamento robusto
            print("📋 Carregando dados dos itens...")
            itens_delimiter = detect_delimiter(path_itens)
            self.df_itens = pd.read_csv(
                path_itens,
                sep=itens_delimiter,
                decimal='.',
                dtype={'CHAVE DE ACESSO': str},
                parse_dates=['DATA EMISSÃO'],
                on_bad_lines='warn'
            )

            # Verificação básica dos dados
            if self.df_cabecalho.empty or self.df_itens.empty:
                raise ValueError("Um ou mais DataFrames foram carregados vazios")

            # Marcar dados como preparados
            self.is_data_prepared = True
            print(
                f"✅ Dados carregados com sucesso! Cabeçalho: {len(self.df_cabecalho)} notas, Itens: {len(self.df_itens)} registros")

        except Exception as e:
            print(f"❌ Erro ao carregar dados: {str(e)}")
            raise

    def run_task(self, user_input: str) -> str:
        """Método principal para executar tarefas do agente"""
        try:
            # Verifica se os dados estão carregados
            if not self.is_data_prepared:
                return "❌ Dados não carregados. Execute _prepare_data primeiro."

            # Processa a consulta
            result = self.agent_executor.invoke({"input": user_input})
            return result["output"]

        except Exception as e:
            error_msg = f"❌ Erro ao processar: {str(e)}"
            print(error_msg)
            return error_msg
