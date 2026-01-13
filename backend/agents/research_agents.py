import json
from typing import Dict, Any
from .base_agent import BaseAgent, AgentResponse


class LinkedInResearchAgent(BaseAgent):
    """Agent for processing LinkedIn profile data"""

    def __init__(self):
        super().__init__(name="LinkedIn Research Agent", temperature=0.3)

    def get_system_prompt(self) -> str:
        return """You are a LinkedIn profile research specialist. Your task is to analyze LinkedIn profile information and extract structured data.

Extract and structure the following information:
1. Work History: Current and previous positions with companies, titles, dates, and key responsibilities
2. Education: Schools, degrees, graduation years, relevant coursework
3. Skills: Technical and soft skills listed on the profile
4. Projects: Notable projects, side projects, or portfolio items
5. Certifications: Professional certifications and licenses
6. Recommendations: Key themes from recommendations (if available)

Return ONLY valid JSON in this exact format:
{
    "work_history": [
        {"company": "...", "title": "...", "start_date": "...", "end_date": "...", "description": "...", "duration_years": 0.0}
    ],
    "education": [
        {"school": "...", "degree": "...", "field": "...", "graduation_year": "...", "details": "..."}
    ],
    "skills": ["skill1", "skill2", ...],
    "projects": [
        {"name": "...", "description": "...", "url": "..."}
    ],
    "certifications": ["cert1", "cert2", ...],
    "key_themes": ["theme1", "theme2", ...]
}

Be thorough but concise. If information is not available, use empty arrays/null values."""

    async def process(self, raw_data: str) -> AgentResponse:
        """
        Process LinkedIn profile data

        Args:
            raw_data: Raw text from LinkedIn profile (manually entered or pasted)

        Returns:
            AgentResponse with structured LinkedIn data
        """
        try:
            user_message = f"""Analyze this LinkedIn profile data and extract structured information:

{raw_data}

Return the information in the specified JSON format."""

            response_text = await self.call_claude(user_message)

            # Parse JSON response
            try:
                # Find JSON in the response (it might be wrapped in markdown code blocks)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]

                structured_data = json.loads(json_str)
            except json.JSONDecodeError:
                return self.format_error_response(f"Failed to parse JSON response: {response_text}")

            return self.format_success_response(
                data=structured_data,
                metadata={"source": "linkedin", "agent": self.name}
            )

        except Exception as e:
            return self.format_error_response(f"LinkedIn research failed: {str(e)}")


class GoogleResearchAgent(BaseAgent):
    """Agent for processing Google search / web research data"""

    def __init__(self):
        super().__init__(name="Google Research Agent", temperature=0.3)

    def get_system_prompt(self) -> str:
        return """You are a web research specialist. Your task is to analyze information from Google searches, personal websites, blogs, and other web sources about a person.

Extract and structure the following information:
1. Publications: Articles, blog posts, papers authored
2. Projects: Open source projects, side projects, startups
3. Speaking Engagements: Conferences, podcasts, webinars
4. Online Presence: Personal website, blog, GitHub, portfolio
5. Media Mentions: News articles, interviews, press releases
6. Expertise Areas: Topics they write/speak about frequently

Return ONLY valid JSON in this exact format:
{
    "publications": [
        {"title": "...", "url": "...", "date": "...", "summary": "..."}
    ],
    "projects": [
        {"name": "...", "description": "...", "url": "...", "technologies": [...]}
    ],
    "speaking": [
        {"event": "...", "topic": "...", "date": "...", "url": "..."}
    ],
    "online_presence": {
        "website": "...",
        "blog": "...",
        "github": "...",
        "other": [...]
    },
    "media_mentions": [
        {"title": "...", "source": "...", "url": "...", "date": "..."}
    ],
    "expertise_areas": ["area1", "area2", ...]
}

Be thorough but concise. If information is not available, use empty arrays/null values."""

    async def process(self, raw_data: str) -> AgentResponse:
        """
        Process Google/web research data

        Args:
            raw_data: Raw text from web research (manually entered findings)

        Returns:
            AgentResponse with structured web research data
        """
        try:
            user_message = f"""Analyze this web research data about a person and extract structured information:

{raw_data}

Return the information in the specified JSON format."""

            response_text = await self.call_claude(user_message)

            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]

                structured_data = json.loads(json_str)
            except json.JSONDecodeError:
                return self.format_error_response(f"Failed to parse JSON response: {response_text}")

            return self.format_success_response(
                data=structured_data,
                metadata={"source": "google", "agent": self.name}
            )

        except Exception as e:
            return self.format_error_response(f"Google research failed: {str(e)}")


class SocialMediaResearchAgent(BaseAgent):
    """Agent for processing social media data (Twitter, Facebook, etc.)"""

    def __init__(self):
        super().__init__(name="Social Media Research Agent", temperature=0.3)

    def get_system_prompt(self) -> str:
        return """You are a social media analysis specialist. Your task is to analyze social media content to understand a person's interests, personality, and communication style.

Extract and structure the following information:
1. Interests: Topics they post about, share, or engage with
2. Content Themes: Main themes in their posts/tweets
3. Engagement Style: How they interact (shares, comments, debates)
4. Personality Indicators: Tone, humor, formality level
5. Values & Causes: Social causes, values they advocate for
6. Network: Types of people/organizations they follow or interact with

Return ONLY valid JSON in this exact format:
{
    "interests": ["interest1", "interest2", ...],
    "content_themes": ["theme1", "theme2", ...],
    "engagement_style": "...",
    "personality_indicators": {
        "tone": "...",
        "humor_level": "...",
        "formality": "...",
        "traits": ["trait1", "trait2", ...]
    },
    "values_causes": ["value1", "cause1", ...],
    "network_types": ["type1", "type2", ...],
    "communication_preferences": "..."
}

Be insightful but avoid over-speculation. Base conclusions on observable patterns."""

    async def process(self, raw_data: str) -> AgentResponse:
        """
        Process social media data

        Args:
            raw_data: Raw text from social media (manually entered posts/profile info)

        Returns:
            AgentResponse with structured social media insights
        """
        try:
            user_message = f"""Analyze this social media data about a person and extract insights:

{raw_data}

Return the information in the specified JSON format."""

            response_text = await self.call_claude(user_message)

            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]

                structured_data = json.loads(json_str)
            except json.JSONDecodeError:
                return self.format_error_response(f"Failed to parse JSON response: {response_text}")

            return self.format_success_response(
                data=structured_data,
                metadata={"source": "social_media", "agent": self.name}
            )

        except Exception as e:
            return self.format_error_response(f"Social media research failed: {str(e)}")
