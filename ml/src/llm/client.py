"""
client.py -- LangChain Groq LLM Client initialization.

Loads GROQ_API_KEY from environment or .env file and instantiates ChatGroq.
If GROQ_API_KEY is missing, gracefully falls back to None so the application
can use the template-based explanation fallback without crashing.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


def get_llm_client(model="openai/gpt-oss-20b", temperature=0.2, max_tokens=1500):
    """
    Initialize and return ChatGroq LLM instance.

    Args:
        model:       Groq model identifier (default: "openai/gpt-oss-20b")
        temperature: Sampling temperature (default 0.2)
        max_tokens:  Max response tokens (default 1500)

    Returns:
        ChatGroq instance if GROQ_API_KEY is available, else None.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    return ChatGroq(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        groq_api_key=api_key,
    )


def evaluate_prompt_guard(prompt_text: str, model="meta-llama/llama-prompt-guard-2-22m") -> float:
    """
    Evaluate prompt injection/jailbreak score using meta-llama/llama-prompt-guard-2-22m.

    Args:
        prompt_text: Input text/prompt to classify
        model:       Groq Prompt Guard model ID

    Returns:
        float score (0.0 = safe, higher = suspicious/injection)
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return 0.0

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt_text}],
        )
        score_str = res.choices[0].message.content
        return float(score_str)
    except Exception:
        return 0.0
