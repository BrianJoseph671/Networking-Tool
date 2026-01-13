import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent, AgentResponse


class AnalyticsAgent(BaseAgent):
    """Agent that analyzes outreach performance and provides insights"""

    def __init__(self):
        super().__init__(name="Analytics Agent", temperature=0.3)

    def get_system_prompt(self) -> str:
        return """You are a data analyst and networking strategist. Your task is to analyze outreach performance data and provide actionable insights to improve networking effectiveness.

Your analysis should cover:
1. Performance Metrics: Response rates, engagement levels by channel/variant
2. Pattern Recognition: What's working and what's not
3. Recommendations: Specific, actionable suggestions for improvement
4. A/B Test Results: Statistical significance and winning variants
5. Follow-up Strategy: When and how to follow up

Be data-driven but practical. Focus on insights that can be acted upon.

Return ONLY valid JSON in the specified format based on the analysis type."""

    async def analyze_overall_performance(
        self,
        outreach_data: List[Dict[str, Any]]
    ) -> AgentResponse:
        """
        Analyze overall outreach performance

        Args:
            outreach_data: List of outreach attempts with their outcomes

        Returns:
            AgentResponse with performance insights
        """
        try:
            if not outreach_data:
                return self.format_error_response("No outreach data provided")

            # Prepare data summary
            data_summary = json.dumps(outreach_data, indent=2, default=str)

            user_message = f"""Analyze this outreach performance data and provide insights:

{data_summary}

Calculate and return in JSON format:
{{
    "overall_metrics": {{
        "total_sent": 0,
        "response_rate": 0.0,
        "avg_response_time_hours": 0.0,
        "positive_sentiment_rate": 0.0
    }},
    "performance_by_channel": {{
        "channel_name": {{"sent": 0, "response_rate": 0.0}}
    }},
    "performance_by_tone": {{
        "tone": {{"sent": 0, "response_rate": 0.0}}
    }},
    "top_insights": [
        "insight 1",
        "insight 2"
    ],
    "recommendations": [
        "recommendation 1",
        "recommendation 2"
    ]
}}"""

            response_text = await self.call_claude(user_message)

            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]

                analytics_data = json.loads(json_str)

            except json.JSONDecodeError:
                return self.format_error_response(f"Failed to parse JSON response: {response_text}")

            return self.format_success_response(
                data=analytics_data,
                metadata={"analysis_type": "overall_performance", "agent": self.name}
            )

        except Exception as e:
            return self.format_error_response(f"Analytics failed: {str(e)}")

    async def analyze_ab_test(
        self,
        variant_a_data: List[Dict[str, Any]],
        variant_b_data: List[Dict[str, Any]],
        variant_a_name: str = "Variant A",
        variant_b_name: str = "Variant B"
    ) -> AgentResponse:
        """
        Analyze A/B test results

        Args:
            variant_a_data: Outreach data for variant A
            variant_b_data: Outreach data for variant B
            variant_a_name: Name of variant A
            variant_b_name: Name of variant B

        Returns:
            AgentResponse with A/B test insights
        """
        try:
            if not variant_a_data or not variant_b_data:
                return self.format_error_response("Both variants need data for comparison")

            user_message = f"""Analyze this A/B test data and determine which variant performed better:

**{variant_a_name}:**
{json.dumps(variant_a_data, indent=2, default=str)}

**{variant_b_name}:**
{json.dumps(variant_b_data, indent=2, default=str)}

Return in JSON format:
{{
    "variant_a": {{
        "name": "{variant_a_name}",
        "sent": 0,
        "responses": 0,
        "response_rate": 0.0,
        "avg_response_time_hours": 0.0
    }},
    "variant_b": {{
        "name": "{variant_b_name}",
        "sent": 0,
        "responses": 0,
        "response_rate": 0.0,
        "avg_response_time_hours": 0.0
    }},
    "winner": "variant_a or variant_b or tie",
    "confidence": "high/medium/low",
    "key_differences": ["difference 1", "difference 2"],
    "recommendation": "Which variant to use and why"
}}"""

            response_text = await self.call_claude(user_message)

            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]

                ab_test_data = json.loads(json_str)

            except json.JSONDecodeError:
                return self.format_error_response(f"Failed to parse JSON response: {response_text}")

            return self.format_success_response(
                data=ab_test_data,
                metadata={"analysis_type": "ab_test", "agent": self.name}
            )

        except Exception as e:
            return self.format_error_response(f"A/B test analysis failed: {str(e)}")

    def calculate_follow_ups_needed(
        self,
        outreach_attempts: List[Dict[str, Any]],
        follow_up_days: int = 3
    ) -> AgentResponse:
        """
        Calculate which prospects need follow-ups (non-AI, rule-based)

        Args:
            outreach_attempts: List of outreach attempts
            follow_up_days: Number of days to wait before suggesting follow-up

        Returns:
            AgentResponse with follow-up recommendations
        """
        try:
            follow_ups_needed = []
            now = datetime.utcnow()

            for attempt in outreach_attempts:
                # Skip if already received response
                if attempt.get("received_response"):
                    continue

                # Skip if status is bounced or not sent
                if attempt.get("status") in ["bounced", "draft"]:
                    continue

                # Check if sent_at exists and enough time has passed
                sent_at = attempt.get("sent_at")
                if not sent_at:
                    continue

                # Parse sent_at if it's a string
                if isinstance(sent_at, str):
                    try:
                        sent_at = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
                    except:
                        continue
                elif not isinstance(sent_at, datetime):
                    continue

                # Calculate days since sent
                days_since_sent = (now - sent_at).days

                if days_since_sent >= follow_up_days:
                    follow_ups_needed.append({
                        "prospect_id": attempt.get("prospect_id"),
                        "prospect_name": attempt.get("prospect_name"),
                        "channel": attempt.get("channel"),
                        "days_since_sent": days_since_sent,
                        "original_sent_at": sent_at.isoformat(),
                        "reason": f"No response after {days_since_sent} days"
                    })

            return self.format_success_response(
                data={
                    "follow_ups_needed": follow_ups_needed,
                    "count": len(follow_ups_needed)
                },
                metadata={
                    "follow_up_threshold_days": follow_up_days,
                    "checked_at": now.isoformat()
                }
            )

        except Exception as e:
            return self.format_error_response(f"Follow-up calculation failed: {str(e)}")

    async def generate_follow_up_message(
        self,
        prospect_name: str,
        persona: Dict[str, Any],
        original_message: str,
        channel: str,
        days_since_sent: int
    ) -> AgentResponse:
        """
        Generate a follow-up message

        Args:
            prospect_name: Name of the prospect
            persona: Persona data
            original_message: The original message that was sent
            channel: Communication channel
            days_since_sent: Number of days since original message

        Returns:
            AgentResponse with follow-up message
        """
        try:
            user_message = f"""Generate a follow-up message with these details:

**Recipient:** {prospect_name}

**Persona Summary:**
{json.dumps(persona, indent=2)}

**Original Message (sent {days_since_sent} days ago):**
{original_message}

**Channel:** {channel}

Create a brief, friendly follow-up that:
1. Doesn't sound pushy or desperate
2. Adds new value or context
3. Makes it easy for them to respond
4. Acknowledges they might be busy

Return in JSON format:
{{
    "subject": "Subject line (null for non-email)",
    "body": "The follow-up message",
    "rationale": "Why this approach was chosen"
}}"""

            response_text = await self.call_claude(user_message)

            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]

                follow_up_data = json.loads(json_str)

            except json.JSONDecodeError:
                return self.format_error_response(f"Failed to parse JSON response: {response_text}")

            return self.format_success_response(
                data=follow_up_data,
                metadata={
                    "message_type": "follow_up",
                    "channel": channel,
                    "days_since_original": days_since_sent,
                    "agent": self.name
                }
            )

        except Exception as e:
            return self.format_error_response(f"Follow-up message generation failed: {str(e)}")
