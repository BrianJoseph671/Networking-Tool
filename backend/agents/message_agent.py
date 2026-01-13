import json
from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResponse


class MessageAgent(BaseAgent):
    """Agent that generates personalized outreach messages"""

    def __init__(self):
        super().__init__(name="Message Generation Agent", temperature=0.7)

    def get_system_prompt(self) -> str:
        return """You are an expert networking and communication specialist. Your task is to craft personalized, authentic outreach messages that help build genuine professional connections.

Key principles:
1. Personalization: Reference specific details about the person
2. Authenticity: Sound genuine, not templated or salesy
3. Value: Make it clear why connecting would be mutually beneficial
4. Brevity: Respect their time - be concise
5. Action: Include a clear, low-pressure call to action

Adapt your message based on:
- Channel: LinkedIn (more professional), Email (flexible), Twitter (casual/brief)
- Connection Degree: 1st degree (warmer), 2nd degree (mention mutual), 3rd+ (more formal)
- Familiarity: Stranger (introduce yourself), Acquaintance (reference past interaction), Colleague (casual)
- Tone: Professional (formal business), Casual (friendly but respectful), Warm (enthusiastic), Direct (brief and to-point)

Return ONLY valid JSON in this exact format:
{
    "subject": "Email subject line (null for non-email channels)",
    "body": "The message body",
    "rationale": "Why this approach was chosen",
    "key_personalization": ["detail1", "detail2"],
    "estimated_effectiveness": 0.85
}

The estimated_effectiveness (0-1) reflects how well-matched the message is to the recipient."""

    async def process(
        self,
        prospect_name: str,
        persona: Dict[str, Any],
        channel: str,
        degree_of_connection: Optional[int] = None,
        familiarity_level: str = "stranger",
        tone: str = "professional",
        custom_context: Optional[str] = None,
        message_variant: str = "default",
        user_info: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Generate a personalized outreach message

        Args:
            prospect_name: Name of the person to reach out to
            persona: The persona data from agglomeration agent
            channel: Outreach channel (linkedin, email, twitter, etc.)
            degree_of_connection: 1st, 2nd, 3rd degree connection
            familiarity_level: stranger, acquaintance, colleague, friend
            tone: professional, casual, warm, direct
            custom_context: Additional context from user (e.g., "mention our mutual love of AI")
            message_variant: For A/B testing (variant_a, variant_b, etc.)
            user_info: Information about the sender (name, title, company, etc.)

        Returns:
            AgentResponse with generated message
        """
        try:
            # Prepare persona summary
            persona_summary = json.dumps(persona, indent=2)

            # Prepare user info
            user_context = ""
            if user_info:
                user_context = f"""
**About You (the sender):**
Name: {user_info.get('name', 'Not provided')}
Title: {user_info.get('title', 'Not provided')}
Company: {user_info.get('company', 'Not provided')}
Background: {user_info.get('background', 'Not provided')}
"""

            # Build the user message
            user_message = f"""Generate a personalized outreach message with these parameters:

**Recipient:** {prospect_name}

**Persona:**
{persona_summary}
{user_context}
**Message Parameters:**
- Channel: {channel}
- Connection Degree: {degree_of_connection or "Unknown"}
- Familiarity Level: {familiarity_level}
- Desired Tone: {tone}
- Message Variant: {message_variant}
"""

            if custom_context:
                user_message += f"\n**Additional Context:**\n{custom_context}\n"

            user_message += "\nReturn the message in the specified JSON format."

            response_text = await self.call_claude(user_message)

            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]

                message_data = json.loads(json_str)

                # Validate required fields
                if "body" not in message_data:
                    return self.format_error_response("Generated message missing 'body' field")

                # Set defaults for optional fields
                message_data.setdefault("subject", None)
                message_data.setdefault("rationale", "No rationale provided")
                message_data.setdefault("key_personalization", [])
                message_data.setdefault("estimated_effectiveness", 0.5)

                # Ensure estimated_effectiveness is between 0 and 1
                message_data["estimated_effectiveness"] = max(
                    0.0,
                    min(1.0, float(message_data["estimated_effectiveness"]))
                )

            except json.JSONDecodeError:
                return self.format_error_response(f"Failed to parse JSON response: {response_text}")

            return self.format_success_response(
                data=message_data,
                metadata={
                    "channel": channel,
                    "familiarity_level": familiarity_level,
                    "tone": tone,
                    "message_variant": message_variant,
                    "agent": self.name
                }
            )

        except Exception as e:
            return self.format_error_response(f"Message generation failed: {str(e)}")

    async def generate_variants(
        self,
        prospect_name: str,
        persona: Dict[str, Any],
        channel: str,
        num_variants: int = 3,
        **kwargs
    ) -> Dict[str, AgentResponse]:
        """
        Generate multiple message variants for A/B testing

        Args:
            prospect_name: Name of the person
            persona: Persona data
            channel: Outreach channel
            num_variants: Number of variants to generate
            **kwargs: Additional parameters for message generation

        Returns:
            Dictionary mapping variant names to AgentResponse objects
        """
        variants = {}
        variant_tones = ["professional", "casual", "warm", "direct"]

        for i in range(num_variants):
            variant_name = f"variant_{chr(97 + i)}"  # variant_a, variant_b, variant_c
            tone = variant_tones[i % len(variant_tones)]

            response = await self.process(
                prospect_name=prospect_name,
                persona=persona,
                channel=channel,
                tone=tone,
                message_variant=variant_name,
                **kwargs
            )

            variants[variant_name] = response

        return variants
