"""
OpenRouter API Service
Handles communication with OpenRouter (OpenAI-compatible API)
Supports both streaming and standard completions
"""

import os
import json
import httpx
from typing import AsyncGenerator, Optional
from api.utils.logger import logger


class OpenRouterService:
    """Service for interacting with OpenRouter API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
        self.site_url = os.getenv("SITE_URL", "https://mum-mentor.com")
        self.site_name = os.getenv("SITE_NAME", "Mum Mentor")
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set in environment variables")
    
    def _get_headers(self) -> dict:
        """Generate headers for OpenRouter API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
            "Content-Type": "application/json"
        }
    
    async def stream_chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from OpenRouter
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
        
        Yields:
            str: Content chunks from the AI response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        url = f"{self.base_url}/chat/completions"
        
        try:
            logger.info(f"Starting streaming request to OpenRouter | model={self.model} | messages={len(messages)}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=self._get_headers(),
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                logger.info("Stream completed")
                                break
                            
                            try:
                                data = json.loads(data_str)
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content")
                                
                                if content:
                                    yield content
                                    
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse streaming chunk: {data_str}")
                                continue
                                
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error streaming from OpenRouter: {str(e)}")
            raise
    
    async def get_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Get a standard (non-streaming) chat completion from OpenRouter
        Used for summarization and title generation
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
        
        Returns:
            str: The complete AI response content
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        url = f"{self.base_url}/chat/completions"
        
        try:
            logger.info(f"Requesting completion from OpenRouter | model={self.model} | messages={len(messages)}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                logger.info(f"Received completion | length={len(content)} chars")
                return content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting completion from OpenRouter: {str(e)}")
            raise
    
    async def generate_summary(self, conversation_history: str) -> str:
        """
        Generate a summary of the conversation history
        
        Args:
            conversation_history: Full conversation text
        
        Returns:
            str: Summarized conversation context
        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes conversations concisely while preserving key information and context."
            },
            {
                "role": "user",
                "content": f"Summarize the following conversation history into a concise paragraph to serve as context for future messages. Preserve important details, topics, and user preferences:\n\n{conversation_history}"
            }
        ]
        
        return await self.get_completion(messages, temperature=0.3, max_tokens=500)
    
    async def generate_title(self, first_message: str) -> str:
        """
        Generate a short title for the conversation
        
        Args:
            first_message: The first user message in the conversation
        
        Returns:
            str: A 3-5 word title
        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that generates short, descriptive titles for conversations. \
                Respond with only the title, 3-5 words maximum, no punctuation."
            },
            {
                "role": "user",
                "content": f"Generate a short, 3-5 word title for a conversation that starts with: '{first_message}'"
            }
        ]
        
        title = await self.get_completion(messages, temperature=0.5, max_tokens=20)
        return title.strip().replace('"', '').replace("'", "")[:50]  # Clean and limit length
