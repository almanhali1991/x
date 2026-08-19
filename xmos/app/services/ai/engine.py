"""
AI Engine - Core AI processing unit for XMOS
Handles model selection, prompt engineering, and response processing
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AIEngine:
    """
    Central AI engine for processing all AI-related tasks
    Supports multiple LLM providers and manages context windows
    """
    
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.provider = provider
        self.model = model or self._get_default_model(provider)
        self.api_key = self._get_api_key(provider)
        self.context_window = self._get_context_window()
        self.temperature = 0.7
        self.max_tokens = 2048
        
    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider"""
        models = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-sonnet-20240229",
            "google": "gemini-pro",
            "local": "llama-3-70b"
        }
        return models.get(provider, "gpt-4-turbo-preview")
    
    def _get_api_key(self, provider: str) -> str:
        """Retrieve API key from environment"""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY"
        }
        env_var = key_map.get(provider, "OPENAI_API_KEY")
        api_key = os.getenv(env_var)
        if not api_key:
            logger.warning(f"API key not found for {provider}")
        return api_key or ""
    
    def _get_context_window(self) -> int:
        """Get context window size for current model"""
        windows = {
            "gpt-4-turbo-preview": 128000,
            "gpt-4": 8192,
            "claude-3-sonnet-20240229": 200000,
            "gemini-pro": 32768,
            "llama-3-70b": 8192
        }
        return windows.get(self.model, 8192)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using the configured AI model
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with generated text and metadata
        """
        temp = temperature or self.temperature
        tokens = max_tokens or self.max_tokens
        
        # Simulate AI generation (implement actual API calls based on provider)
        response = {
            "text": f"[AI Generated Content based on: {prompt[:50]}...]",
            "model": self.model,
            "provider": self.provider,
            "tokens_used": len(prompt.split()) + 100,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "temperature": temp,
                "max_tokens": tokens,
                "context_window": self.context_window
            }
        }
        
        logger.info(f"Generated content using {self.model}")
        return response
    
    async def analyze(
        self,
        content: str,
        analysis_type: str = "sentiment",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze content using AI
        
        Args:
            content: Content to analyze
            analysis_type: Type of analysis (sentiment, topics, entities, etc.)
            
        Returns:
            Analysis results
        """
        prompt = f"Analyze the following content for {analysis_type}: {content}"
        
        result = await self.generate(prompt, system_prompt=f"You are an expert at {analysis_type} analysis.")
        
        return {
            "analysis_type": analysis_type,
            "content_length": len(content),
            "result": result["text"],
            "confidence": 0.92,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Multi-turn conversation with context
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            AI response with conversation history
        """
        # Process conversation maintaining context
        system_message = next((m for m in messages if m["role"] == "system"), None)
        user_messages = [m for m in messages if m["role"] == "user"]
        
        if not user_messages:
            return {"error": "No user messages provided"}
        
        last_prompt = user_messages[-1]["content"]
        response = await self.generate(
            last_prompt,
            system_prompt=system_message["content"] if system_message else None,
            **kwargs
        )
        
        return {
            "response": response["text"],
            "conversation_id": kwargs.get("conversation_id", "default"),
            "message_count": len(messages),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def can_fit_in_context(self, existing_tokens: int, new_text: str) -> bool:
        """Check if new text fits within context window"""
        new_tokens = self.estimate_tokens(new_text)
        return (existing_tokens + new_tokens) < (self.context_window * 0.9)  # Leave 10% buffer
