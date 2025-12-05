# file: backend/agents/sql_agent.py
import pandas as pd
import sqlite3
from typing import Dict, Any
from backend.utils.logger import setup_logger
from backend.utils.config import get_llm_with_fallback, invoke_with_fallback
from langchain_core.messages import SystemMessage, HumanMessage

logger = setup_logger(__name__)

class SQLAgent:
    def __init__(self):
        self.llm = get_llm_with_fallback(provider="groq", model_index=0)

    def df_to_sqlite(self, df: pd.DataFrame, table_name: str = "dataset") -> sqlite3.Connection:
        """Load DataFrame into an in-memory SQLite database."""
        conn = sqlite3.connect(":memory:")
        df.to_sql(table_name, conn, index=False, if_exists="replace")
        return conn

    async def generate_sql(self, query: str, schema: Dict[str, str]) -> str:
        """Convert natural language to SQL."""
        prompt = f"""
        You are an expert SQL Data Analyst.
        Convert the user's natural language query into a valid SQL query for a SQLite database.
        The table name is 'dataset'.
        
        Schema:
        {schema}
        
        User Query: "{query}"
        
        Return ONLY the raw SQL query. Do not include markdown formatting or explanations.
        """
        
        messages = [
            SystemMessage(content="You are a SQL generator. Output only SQL."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = await invoke_with_fallback(self.llm, messages, provider="groq")
            sql = response.content.replace("```sql", "").replace("```", "").strip()
            return sql
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return ""

    async def execute_query(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Process a natural language query on the dataframe."""
        # 1. Infer schema for context
        schema = {col: str(df[col].dtype) for col in df.columns}
        
        # 2. Generate SQL
        sql_query = await self.generate_sql(query, schema)
        if not sql_query:
            return {"error": "Failed to generate SQL."}
            
        logger.info(f"Generated SQL: {sql_query}")
        
        # 3. Execute SQL
        conn = self.df_to_sqlite(df)
        try:
            result_df = pd.read_sql_query(sql_query, conn)
            return {
                "query": query,
                "sql": sql_query,
                "result": result_df.to_dict(orient="records"),
                "row_count": len(result_df)
            }
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {"error": str(e), "sql": sql_query}
        finally:
            conn.close()
# end file
