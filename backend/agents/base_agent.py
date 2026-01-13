from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import anthropic
from ..config import config


@dataclass
class AgentResponse:
    """Standardized response from agents"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(
        self,
        name: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        self.name = name
        self.model = model or config.DEFAULT_MODEL
        self.temperature = temperature if temperature is not None else config.TEMPERATURE
        self.max_tokens = max_tokens or config.MAX_TOKENS

        # Initialize Anthropic client
        if not config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment variables")

        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass

    @abstractmethod
    async def process(self, **kwargs) -> AgentResponse:
        """Main processing method - must be implemented by subclasses"""
        pass

    async def call_claude(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call Claude API with the given message

        Args:
            user_message: The user message to send
            system_prompt: Optional system prompt override
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override

        Returns:
            The text response from Claude
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                system=system_prompt or self.get_system_prompt(),
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract text from response
            return response.content[0].text

        except Exception as e:
            raise Exception(f"Error calling Claude API: {str(e)}")

    def format_error_response(self, error: str) -> AgentResponse:
        """Helper to format error responses"""
        return AgentResponse(
            success=False,
            data={},
            error=error
        )

    def format_success_response(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Helper to format success responses"""
        return AgentResponse(
            success=True,
            data=data,
            metadata=metadata
        )
