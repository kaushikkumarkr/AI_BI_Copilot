# file: backend/agents/data_interpreter.py
import pandas as pd
import json
from typing import Dict, Any, List
from backend.utils.logger import setup_logger
from backend.utils.config import get_llm_with_fallback, invoke_with_fallback
from langchain_core.messages import SystemMessage, HumanMessage

logger = setup_logger(__name__)

class DataInterpreter:
    def __init__(self):
        self.llm = get_llm_with_fallback(provider="groq", model_index=0)

    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from CSV or Excel."""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format")
            logger.info(f"Loaded dataset with shape: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def infer_schema(self, df: pd.DataFrame) -> Dict[str, str]:
        """Infer data types for each column."""
        schema = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if "int" in dtype:
                schema[col] = "Integer"
            elif "float" in dtype:
                schema[col] = "Float"
            elif "datetime" in dtype:
                schema[col] = "Datetime"
            elif "object" in dtype:
                # Check if it's actually a date
                try:
                    pd.to_datetime(df[col])
                    schema[col] = "Datetime"
                except:
                    schema[col] = "Categorical/Text"
            else:
                schema[col] = "Unknown"
        return schema

    async def summarize_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a semantic summary of the dataset using LLM."""
        schema = self.infer_schema(df)
        preview = df.head(5).to_markdown()
        stats = df.describe().to_markdown()
        
        prompt = f"""
        You are a Data Scientist. Analyze this dataset preview and schema.
        
        Schema:
        {json.dumps(schema, indent=2)}
        
        Preview:
        {preview}
        
        Statistics:
        {stats}
        
        Provide a structured JSON summary with:
        1. 'description': Brief overview of what this data represents.
        2. 'key_entities': Main business entities found (e.g., Customers, Orders).
        3. 'potential_analyses': List of 3-5 recommended analyses.
        
        Return ONLY valid JSON.
        """
        
        messages = [
            SystemMessage(content="You are a helpful Data Interpreter Agent."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = await invoke_with_fallback(self.llm, messages, provider="groq")
            content = response.content
            # Basic cleanup to ensure JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            summary = json.loads(content.strip())
            return summary
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return {
                "description": "Could not generate summary.",
                "key_entities": [],
                "potential_analyses": []
            }

    def process(self, file_path: str) -> Dict[str, Any]:
        """Main entry point for the agent."""
        df = self.load_data(file_path)
        schema = self.infer_schema(df)
        
        # Basic stats
        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "schema": schema,
            "missing_values": df.isnull().sum().to_dict(),
            "columns_list": list(df.columns)
        }
        
        return {"df": df, "initial_summary": summary}
# end file
