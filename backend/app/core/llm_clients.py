"""
LLM Client implementations for different providers
"""

from typing import Optional, Dict, Any, AsyncGenerator, List
import os
from enum import Enum
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import LLMResult
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import AsyncCallbackHandler

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MOCK = "mock"  # For testing


class StreamingCallback(AsyncCallbackHandler):
    """Custom callback handler for streaming responses"""
    
    def __init__(self):
        self.tokens = []
        
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when a new token is generated"""
        self.tokens.append(token)


def create_llm_client(
    provider: LLMProvider,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    streaming: bool = False,
    **kwargs
) -> BaseChatModel:
    """
    Factory function to create LangChain LLM clients
    
    Args:
        provider: LLM provider to use
        api_key: API key (or from environment)
        model: Model name
        temperature: Temperature for generation
        streaming: Enable streaming
        **kwargs: Additional provider-specific arguments
        
    Returns:
        LangChain chat model instance
    """
    
    if provider == LLMProvider.OPENAI:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("Please install langchain-openai: pip install langchain-openai")
        
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        return ChatOpenAI(
            api_key=api_key,
            model=model or "gpt-4-turbo-preview",
            temperature=temperature,
            streaming=streaming,
            **kwargs
        )
    
    elif provider == LLMProvider.ANTHROPIC:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError("Please install langchain-anthropic: pip install langchain-anthropic")
        
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key required")
        
        return ChatAnthropic(
            anthropic_api_key=api_key,
            model=model or "claude-3-opus-20240229",
            temperature=temperature,
            streaming=streaming,
            **kwargs
        )
    
    elif provider == LLMProvider.GOOGLE:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError("Please install langchain-google-genai: pip install langchain-google-genai")
        
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key required")
        
        return ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=model or "gemini-pro",
            temperature=temperature,
            streaming=streaming,
            convert_system_message_to_human=True,  # Gemini doesn't support system messages
            **kwargs
        )
    
    elif provider == LLMProvider.MOCK:
        from langchain_community.llms.fake import FakeListLLM
        
        # Use FakeListLLM for testing
        responses = [
            "Mock response for testing purposes",
            "Another mock response",
            "Third mock response"
        ]
        return FakeListLLM(responses=responses)
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


class LangChainLLMClient:
    """
    Wrapper class for LangChain LLM clients with our interface
    """
    
    def __init__(
        self,
        provider: LLMProvider,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        streaming: bool = False,
        **kwargs
    ):
        """
        Initialize LangChain LLM client
        
        Args:
            provider: LLM provider to use
            api_key: API key
            model: Model name
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            streaming: Enable streaming
            **kwargs: Additional provider-specific arguments
        """
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.streaming = streaming
        
        # Create the LangChain model
        self.llm = create_llm_client(
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=temperature,
            streaming=streaming,
            max_tokens=max_tokens,
            **kwargs
        )
        
        logger.info(f"Initialized {provider.value} LLM client (model: {model or 'default'})")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from the LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            **kwargs: Additional generation arguments
            
        Returns:
            Generated text response
        """
        # Build messages
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        # Override temperature if provided
        if temperature is not None:
            self.llm.temperature = temperature
        
        try:
            # Generate response
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content
            
        except Exception as e:
            logger.error(f"{self.provider.value} generation error: {e}")
            raise
        finally:
            # Reset temperature
            if temperature is not None:
                self.llm.temperature = self.temperature
    
    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            **kwargs: Additional generation arguments
            
        Yields:
            Generated text chunks
        """
        if not self.streaming:
            # If streaming not enabled, just yield the full response
            response = await self.generate(prompt, system_prompt, temperature, **kwargs)
            yield response
            return
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        # Override temperature if provided
        if temperature is not None:
            self.llm.temperature = temperature
        
        try:
            # Stream response
            async for chunk in self.llm.astream(messages, **kwargs):
                if chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            logger.error(f"{self.provider.value} streaming error: {e}")
            raise
        finally:
            # Reset temperature
            if temperature is not None:
                self.llm.temperature = self.temperature
    
    def get_model_name(self) -> str:
        """Get the model name being used"""
        if hasattr(self.llm, 'model_name'):
            return self.llm.model_name
        elif hasattr(self.llm, 'model'):
            return self.llm.model
        else:
            return "unknown"
    
    def get_token_count(self, text: str) -> int:
        """
        Get token count for text (if supported)
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count or -1 if not supported
        """
        try:
            if hasattr(self.llm, 'get_num_tokens'):
                return self.llm.get_num_tokens(text)
            elif hasattr(self.llm, 'get_token_ids'):
                return len(self.llm.get_token_ids(text))
            else:
                # Rough estimate: 1 token per 4 characters
                return len(text) // 4
        except:
            return -1