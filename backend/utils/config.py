# file: backend/utils/config.py
"""LLM configuration with automatic multi-provider fallback."""
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from typing import List, Optional, Any
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Ollama models (Local)
OLLAMA_MODELS = [
    "qwen2.5:7b"
]

# Groq models in priority order
GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "openai/gpt-oss-120b",
    "gemma2-9b-it",
    "llama-3.3-70b-versatile"  # Moved to bottom due to rate limit
]

# OpenRouter models (Free tier & Low cost)
OPENROUTER_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "mistralai/mistral-nemo:free",
    "microsoft/phi-3-mini-128k-instruct:free"
]

# Hugging Face models (Free Inference API)
HUGGINGFACE_MODELS = [
    "google/flan-t5-large",
    "google/flan-t5-base",
    "google/flan-t5-small"
]

# Track current provider
_current_provider = "ollama"
_current_model_index = 0

def get_llm_with_fallback(provider: str = "ollama", model_index: int = 0, temperature: float = 0):
    """Get LLM instance for the specified provider."""
    
    if provider == "ollama":
        if model_index >= len(OLLAMA_MODELS):
            return None
        model = OLLAMA_MODELS[model_index]
        logger.info(f"[LLM] Using Ollama model: {model}")
        return ChatOllama(
            model=model,
            temperature=temperature,
        )

    elif provider == "groq":
        if model_index >= len(GROQ_MODELS):
            return None
        model = GROQ_MODELS[model_index]
        logger.info(f"[LLM] Using Groq model: {model}")
        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=Config.GROQ_API_KEY
        )
    
    elif provider == "openrouter":
        if model_index >= len(OPENROUTER_MODELS):
            return None
        model = OPENROUTER_MODELS[model_index]
        
        try:
            from langchain_openai import ChatOpenAI
            api_key = Config.OPENROUTER_API_KEY
            if not api_key:
                logger.warning("[LLM] OpenRouter API key not found")
                return None
            
            logger.info(f"[LLM] Using OpenRouter model: {model}")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1"
            )
        except ImportError:
            logger.warning("[LLM] langchain-openai not installed")
            return None
    
    elif provider == "huggingface":
        if model_index >= len(HUGGINGFACE_MODELS):
            return None
        model = HUGGINGFACE_MODELS[model_index]
        
        try:
            from langchain_huggingface import HuggingFaceEndpoint
            api_key = Config.HUGGINGFACE_API_KEY
            if not api_key:
                logger.warning("[LLM] Hugging Face API key not found")
                return None
            
            logger.info(f"[LLM] Using Hugging Face model: {model}")
            return HuggingFaceEndpoint(
                repo_id=model,
                temperature=temperature,
                huggingfacehub_api_token=api_key
            )
        except ImportError:
            logger.warning("[LLM] langchain-huggingface not installed")
            return None
    
    return None

class MockChatLLM:
    """Fallback mock LLM when all providers are exhausted."""
    def __init__(self):
        self.model_name = "mock-fallback"
    
    async def ainvoke(self, messages):
        from langchain_core.messages import AIMessage
        return AIMessage(content="**System Notice:** All AI providers are currently at capacity. Please try again in a few minutes.")

async def invoke_with_fallback(llm: Any, messages, provider: str = "ollama", model_index: int = 0):
    """
    Invoke LLM with automatic multi-provider fallback.
    """
    global _current_provider, _current_model_index
    
    if isinstance(llm, MockChatLLM):
        return await llm.ainvoke(messages)

    try:
        result = await llm.ainvoke(messages)
        _current_provider = provider
        _current_model_index = model_index
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        print(f"!!! LLM ERROR ({provider}, index {model_index}): {error_msg}")
        
        # 1. Try next model in CURRENT provider
        if provider == "ollama":
            if model_index < len(OLLAMA_MODELS) - 1:
                print(f"[LLM DEBUG] Switching to Ollama model index {model_index + 1}: {OLLAMA_MODELS[model_index + 1]}")
                return await invoke_with_fallback(get_llm_with_fallback("ollama", model_index + 1), messages, "ollama", model_index + 1)
        elif provider == "groq":
            if model_index < len(GROQ_MODELS) - 1:
                print(f"[LLM DEBUG] Switching to Groq model index {model_index + 1}: {GROQ_MODELS[model_index + 1]}")
                return await invoke_with_fallback(get_llm_with_fallback("groq", model_index + 1), messages, "groq", model_index + 1)
        elif provider == "openrouter":
            if model_index < len(OPENROUTER_MODELS) - 1:
                print(f"[LLM DEBUG] Switching to OpenRouter model index {model_index + 1}: {OPENROUTER_MODELS[model_index + 1]}")
                return await invoke_with_fallback(get_llm_with_fallback("openrouter", model_index + 1), messages, "openrouter", model_index + 1)
        elif provider == "huggingface":
            if model_index < len(HUGGINGFACE_MODELS) - 1:
                print(f"[LLM DEBUG] Switching to HuggingFace model index {model_index + 1}: {HUGGINGFACE_MODELS[model_index + 1]}")
                return await invoke_with_fallback(get_llm_with_fallback("huggingface", model_index + 1), messages, "huggingface", model_index + 1)

        # 2. Switch Provider (Ollama -> Groq -> OpenRouter -> Hugging Face -> Mock)
        if provider == "ollama":
            logger.error("[LLM] Ollama exhausted. Switching to Groq...")
            return await invoke_with_fallback(get_llm_with_fallback("groq", 0), messages, "groq", 0)

        if provider == "groq":
            logger.error("[LLM] Groq exhausted. Switching to OpenRouter...")
            return await invoke_with_fallback(get_llm_with_fallback("openrouter", 0), messages, "openrouter", 0)
            
        if provider == "openrouter":
            logger.error("[LLM] OpenRouter exhausted. Switching to Hugging Face...")
            return await invoke_with_fallback(get_llm_with_fallback("huggingface", 0), messages, "huggingface", 0)
            
        # 3. Final Fallback
        logger.error("[LLM] All providers exhausted. Using Safe Mode.")
        return await MockChatLLM().ainvoke(messages)

def reset_model_index():
    """Reset to primary provider."""
    global _current_provider, _current_model_index
    _current_provider = "ollama"
    _current_model_index = 0
    logger.info("[LLM] Reset to Ollama primary model")
# end file
