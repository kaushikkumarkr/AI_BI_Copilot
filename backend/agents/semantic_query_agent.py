# file: backend/agents/semantic_query_agent.py
import pandas as pd
from typing import Dict, Any
from backend.utils.logger import setup_logger
from backend.utils.config import get_llm_with_fallback, invoke_with_fallback
from langchain_core.messages import SystemMessage, HumanMessage

logger = setup_logger(__name__)

class SemanticQueryAgent:
    def __init__(self):
        self.llm = get_llm_with_fallback(provider="groq", model_index=0)

    async def answer_query(self, df: pd.DataFrame, query: str, context: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Answer 'Why' and 'How' questions using the dataset context.
        """
        # Prepare context (summary stats) to fit in context window
        # We don't pass the whole DF, just a summary
        summary = df.describe(include='all').to_markdown()
        head = df.head(5).to_markdown()
        
        prompt = f"""
        You are a Senior Business Intelligence Analyst.
        Answer the user's question based on the dataset preview and statistics provided below.
        
        User Question: "{query}"
        
        Dataset Preview:
        {head}
        
        Dataset Statistics:
        {summary}
        
        Additional Context:
        {context if context else 'None'}
        
        Provide a clear, concise, and data-driven explanation. 
        If you cannot answer based on the data, state that clearly.
        """
        
        messages = [
            SystemMessage(content="You are a helpful BI Analyst."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = await invoke_with_fallback(self.llm, messages, provider="groq")
            return {
                "query": query,
                "answer": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Semantic query failed: {e}")
            return {"error": str(e), "status": "failed"}
# end file
