# file: tests/verify_api.py
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utils.config import get_llm_with_fallback, invoke_with_fallback
from langchain_core.messages import HumanMessage
import asyncio
from dotenv import load_dotenv

# Load env explicitly
load_dotenv("backend/.env")

async def test_llm():
    print("--- Testing LLM Connection ---")
    
    # Check keys
    groq_key = os.getenv("GROQ_API_KEY")
    print(f"GROQ_API_KEY present: {bool(groq_key)}")
    
    # Try to get Groq first (since it's usually fast and free)
    llm = get_llm_with_fallback(provider="groq")
    
    if not llm:
        print("Failed to initialize LLM.")
        return
        
    print(f"LLM Initialized: {type(llm).__name__}")
    
    try:
        messages = [HumanMessage(content="Hello! Are you working? Reply with 'Yes, I am online.'")]
        print("Sending request...")
        response = await invoke_with_fallback(llm, messages, provider="groq")
        print(f"Response: {response.content}")
        print("--- SUCCESS ---")
    except Exception as e:
        print(f"--- FAILED ---")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())
# end file
