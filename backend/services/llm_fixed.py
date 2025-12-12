"""LLM provider abstraction - supports both Anthropic Claude and Google Gemini."""
from typing import List, Dict, Any
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def get_llm(temperature: float = 0):
    """
    Get the configured LLM instance.

    Supports both Anthropic Claude and Google Gemini.

    Args:
        temperature: Temperature for response generation

    Returns:
        LLM instance compatible with LangChain
    """
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        logger.info("Using Anthropic Claude")
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model="claude-3-5-sonnet-20241022",
            temperature=temperature
        )

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage, SystemMessage

        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")

        logger.info(f"Using Google Gemini ({settings.gemini_model})")

        # Create base LLM
        base_llm = ChatGoogleGenerativeAI(
            google_api_key=settings.google_api_key,
            model=settings.gemini_model,
            temperature=temperature
        )

        # Wrapper to fix "contents is not specified" error
        class GeminiWrapper:
            """Wrapper that ensures proper message formatting for Gemini."""

            def __init__(self, llm):
                self.llm = llm

            def invoke(self, messages):
                """Convert all SystemMessage to HumanMessage for Gemini compatibility."""
                converted = []
                for msg in messages:
                    if isinstance(msg, SystemMessage):
                        # Gemini doesn't handle SystemMessage well, convert to HumanMessage
                        converted.append(HumanMessage(content=msg.content))
                    else:
                        converted.append(msg)

                # Ensure we have at least one message with content
                if not converted or not any(hasattr(m, 'content') and m.content for m in converted):
                    raise ValueError("No message content provided for Gemini")

                return self.llm.invoke(converted)

        return GeminiWrapper(base_llm)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Use 'anthropic' or 'gemini'")


def invoke_llm(messages: List[Any], temperature: float = 0) -> str:
    """
    Invoke the LLM with messages and return the response content.

    Args:
        messages: List of messages (SystemMessage, HumanMessage, etc.)
        temperature: Temperature for response generation

    Returns:
        Response content as string
    """
    llm = get_llm(temperature=temperature)
    response = llm.invoke(messages)
    return response.content
