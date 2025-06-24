# agent_analyst/orchestrator_agent.py (versão corrigida)

from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry
import pandas as pd
from pathlib import Path
import zipfile
import nest_asyncio

nest_asyncio.apply()


@dataclass
class QueryDeps:
    df_cabecalho: pd.DataFrame
    df_itens: pd.DataFrame


class OrchestratorAgent:
    def __init__(self, model_name: str = 'groq:gemma2-9b-it'):
        self.data_path = Path("data")
        self.df_cabecalho = None
        self.df_itens = None
        self.is_data_prepared = False

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

        4. **Sempre use a ferramenta safe_cross_query para executar consultas**

        **EXEMPLOS CORRETOS:**
        - "Quantas notas fiscais?" → safe_cross_query("len(df_cabecalho)")
        - "Valor total?" → safe_cross_query("df_cabecalho['VALOR NOTA FISCAL'].sum()")
        - "Produto mais vendido?" → safe_cross_query("df_itens['DESCRIÇÃO DO PRODUTO/SERVIÇO'].value_counts().head(1)")

        Sempre responda em Português do Brasil e seja preciso com os números.
        """

        self.query_agent = Agent(
            model=model_name,
            system_prompt=self.base_system_prompt,
            deps_type=QueryDeps,
            retries=4
        )

        # Registrar a tool corretamente
        self.query_agent.tool(self.safe_cross_query)

    @staticmethod
    def safe_cross_query(ctx: RunContext[QueryDeps], query: str) -> str:
        """
        Executa consultas seguras nos DataFrames de notas fiscais.

        Args:
            ctx: Contexto com os DataFrames
            query: Código Python para executar
        """
        try:
            print(f"🔍 Executando consulta: {query}")

            df_cabecalho = ctx.deps.df_cabecalho
            df_itens = ctx.deps.df_itens

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

            raise ModelRetry(f"{error_details}{suggestion_text}") from e

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

        # Carregar DataFrame do cabeçalho
        print("📄 Carregando dados do cabeçalho...")
        self.df_cabecalho = pd.read_csv(
            path_cabecalho,
            sep=',',
            decimal='.',
            dtype={'CHAVE DE ACESSO': str},
            parse_dates=['DATA EMISSÃO']
        )

        # Carregar DataFrame dos itens
        print("📋 Carregando dados dos itens...")
        self.df_itens = pd.read_csv(
            path_itens,
            sep=',',
            decimal='.',
            dtype={'CHAVE DE ACESSO': str},
            parse_dates=['DATA EMISSÃO']
        )

        # Validar dados carregados
        self._validate_data()

        self.is_data_prepared = True
        print("✅ Dados preparados com sucesso!")

    def _validate_data(self):
        """Valida a integridade dos dados carregados"""
        print("\n🔍 Validando integridade dos dados:")

        # Verificar se os DataFrames foram carregados
        if self.df_cabecalho is None or self.df_itens is None:
            raise ValueError("Erro: DataFrames não foram carregados corretamente")

        # Estatísticas básicas
        total_notas = len(self.df_cabecalho)
        total_itens = len(self.df_itens)
        chaves_unicas_cab = self.df_cabecalho['CHAVE DE ACESSO'].nunique()
        chaves_unicas_itens = self.df_itens['CHAVE DE ACESSO'].nunique()

        print(f"📊 Estatísticas dos dados:")
        print(f"   • Total de notas fiscais (cabeçalho): {total_notas}")
        print(f"   • Total de itens: {total_itens}")
        print(f"   • Chaves únicas no cabeçalho: {chaves_unicas_cab}")
        print(f"   • Chaves únicas nos itens: {chaves_unicas_itens}")

        # Validações críticas
        if total_notas != chaves_unicas_cab:
            raise ValueError(
                f"ERRO: Duplicatas no cabeçalho! Linhas: {total_notas}, Chaves únicas: {chaves_unicas_cab}")

        # Verificar se esperamos 100 notas conforme mencionado
        if total_notas != 100:
            print(f"⚠️ AVISO: Esperado 100 notas, encontrado {total_notas}")

        # Verificar integridade referencial
        chaves_orfas = ~self.df_itens['CHAVE DE ACESSO'].isin(self.df_cabecalho['CHAVE DE ACESSO'])
        if chaves_orfas.any():
            total_orfas = chaves_orfas.sum()
            print(f"⚠️ AVISO: {total_orfas} itens sem nota fiscal correspondente no cabeçalho")

        print("✅ Validação concluída")

    def run_task(self, question: str) -> str:
        """
        Executa uma tarefa/pergunta sobre os dados das notas fiscais

        Args:
            question: Pergunta em linguagem natural

        Returns:
            str: Resposta da análise
        """
        try:
            # Preparar dados se necessário
            if not self.is_data_prepared:
                self._prepare_data(
                    zip_filename="202401_NFs.zip",
                    cabecalho_filename="202401_NFs_Cabecalho.csv",
                    itens_filename="202401_NFs_Itens.csv"
                )

            # Verificar se os dados estão disponíveis
            if self.df_cabecalho is None or self.df_itens is None:
                return "❌ Erro: Dados não foram carregados corretamente. Verifique os arquivos."

            print(f"\n🎯 Processando pergunta: '{question}'")

            # Criar dependências para o agente
            deps = QueryDeps(
                df_cabecalho=self.df_cabecalho,
                df_itens=self.df_itens
            )

            # Executar consulta via agente
            response = self.query_agent.run_sync(question, deps=deps)

            # Extrair a resposta final
            final_response = response.new_messages()[-1].parts[0].content

            return final_response

        except Exception as e:
            error_msg = f"❌ Erro ao processar a pergunta: {str(e)}"
            print(error_msg)
            return error_msg

    def get_data_summary(self) -> str:
        """Retorna um resumo dos dados carregados"""
        if not self.is_data_prepared:
            return "Dados ainda não foram preparados."

        summary = f"""
📈 **Resumo dos Dados Carregados:**

🧾 **Cabeçalho das Notas:**
   • Total de notas fiscais: {len(self.df_cabecalho)}
   • Período: {self.df_cabecalho['DATA EMISSÃO'].min()} a {self.df_cabecalho['DATA EMISSÃO'].max()}
   • Valor total: R$ {self.df_cabecalho['VALOR NOTA FISCAL'].sum():,.2f}

📋 **Itens das Notas:**
   • Total de itens: {len(self.df_itens)}
   • Produtos únicos: {self.df_itens['DESCRIÇÃO DO PRODUTO/SERVIÇO'].nunique()}

🔗 **Integridade:**
   • Chaves no cabeçalho: {self.df_cabecalho['CHAVE DE ACESSO'].nunique()}
   • Chaves nos itens: {self.df_itens['CHAVE DE ACESSO'].nunique()}
"""
        return summary