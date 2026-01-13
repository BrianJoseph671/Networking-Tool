import json
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse


class AgglomerationAgent(BaseAgent):
    """Agent that synthesizes all research data into a comprehensive persona"""

    def __init__(self):
        super().__init__(name="Agglomeration Agent", temperature=0.5)

    def get_system_prompt(self) -> str:
        return """You are an expert persona builder and human behavior analyst. Your task is to synthesize multiple sources of data about a person into a comprehensive, nuanced persona that helps with networking and relationship building.

Your goal is to:
1. Integrate data from LinkedIn, web research, and social media
2. Identify patterns and themes across all sources
3. Build a multi-dimensional understanding of the person
4. Provide actionable networking insights

Create a persona that includes:
- Professional Profile: Career trajectory, expertise, achievements
- Personal Profile: Interests, values, personality traits
- Communication Style: How they prefer to communicate and engage
- Networking Strategy: How to best approach and connect with them
- Conversation Starters: Specific topics that would resonate

Return ONLY valid JSON in this exact format:
{
    "summary": "2-3 sentence overview of who this person is",
    "career_trajectory": "Narrative of their career path and progression",
    "expertise_areas": ["area1", "area2", ...],
    "notable_achievements": ["achievement1", "achievement2", ...],
    "personality_traits": ["trait1", "trait2", ...],
    "communication_style": "How they communicate (formal/casual, direct/diplomatic, etc.)",
    "interests_hobbies": ["interest1", "interest2", ...],
    "values": ["value1", "value2", ...],
    "connection_strategy": "Recommended approach for connecting with this person",
    "conversation_starters": ["starter1", "starter2", ...],
    "common_ground": ["potential shared interest/experience 1", ...],
    "confidence_score": 0.85
}

The confidence_score (0-1) should reflect how complete and reliable the data is.
Be insightful but honest about limitations. Avoid over-speculation."""

    async def process(
        self,
        prospect_name: str,
        linkedin_data: Dict[str, Any] = None,
        google_data: Dict[str, Any] = None,
        social_media_data: Dict[str, Any] = None,
        manual_notes: str = None
    ) -> AgentResponse:
        """
        Synthesize all research data into a comprehensive persona

        Args:
            prospect_name: Name of the prospect
            linkedin_data: Structured data from LinkedIn agent
            google_data: Structured data from Google agent
            social_media_data: Structured data from social media agent
            manual_notes: Any additional manual notes

        Returns:
            AgentResponse with comprehensive persona
        """
        try:
            # Prepare the input message
            data_sections = []

            if linkedin_data:
                data_sections.append(f"""
**LinkedIn Data:**
{json.dumps(linkedin_data, indent=2)}
""")

            if google_data:
                data_sections.append(f"""
**Web Research Data:**
{json.dumps(google_data, indent=2)}
""")

            if social_media_data:
                data_sections.append(f"""
**Social Media Data:**
{json.dumps(social_media_data, indent=2)}
""")

            if manual_notes:
                data_sections.append(f"""
**Additional Notes:**
{manual_notes}
""")

            if not data_sections:
                return self.format_error_response("No data provided for persona generation")

            user_message = f"""Create a comprehensive persona for: {prospect_name}

{chr(10).join(data_sections)}

Synthesize all this information into a cohesive persona that provides actionable networking insights. Return the information in the specified JSON format."""

            response_text = await self.call_claude(user_message)

            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]

                persona_data = json.loads(json_str)

                # Validate confidence score
                if "confidence_score" not in persona_data:
                    persona_data["confidence_score"] = 0.5

                # Ensure confidence score is between 0 and 1
                persona_data["confidence_score"] = max(0.0, min(1.0, float(persona_data["confidence_score"])))

            except json.JSONDecodeError:
                return self.format_error_response(f"Failed to parse JSON response: {response_text}")

            return self.format_success_response(
                data=persona_data,
                metadata={
                    "sources_used": {
                        "linkedin": linkedin_data is not None,
                        "google": google_data is not None,
                        "social_media": social_media_data is not None,
                        "manual_notes": manual_notes is not None
                    },
                    "agent": self.name
                }
            )

        except Exception as e:
            return self.format_error_response(f"Persona generation failed: {str(e)}")
