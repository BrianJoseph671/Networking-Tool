from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

from ..models.database import (
    get_db, Prospect, ResearchData, Persona, OutreachMessage,
    OutreachAttempt, FollowUp, ResearchSourceType, OutreachChannel,
    OutreachStatus
)
from ..agents import (
    LinkedInResearchAgent, GoogleResearchAgent, SocialMediaResearchAgent,
    AgglomerationAgent, MessageAgent, AnalyticsAgent
)
from ..utils import extract_text_from_pdf, is_valid_pdf

router = APIRouter(prefix="/api")


# Pydantic models for request/response
class ProspectCreate(BaseModel):
    name: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    location: Optional[str] = None


class ResearchDataCreate(BaseModel):
    source_type: str  # linkedin, google, social_media, manual
    raw_text: str


class MessageGenerationRequest(BaseModel):
    channel: str
    degree_of_connection: Optional[int] = None
    familiarity_level: str = "stranger"
    tone: str = "professional"
    custom_context: Optional[str] = None
    message_variant: str = "default"
    user_info: Optional[Dict[str, Any]] = None


class OutreachAttemptCreate(BaseModel):
    message_id: Optional[int] = None
    channel: str
    sent_at: Optional[datetime] = None


class OutreachAttemptUpdate(BaseModel):
    status: Optional[str] = None
    received_response: Optional[bool] = None
    response_text: Optional[str] = None
    response_sentiment: Optional[str] = None
    replied_at: Optional[datetime] = None


# ============== PROSPECT ENDPOINTS ==============

@router.post("/prospects", status_code=status.HTTP_201_CREATED)
async def create_prospect(prospect: ProspectCreate, db: Session = Depends(get_db)):
    """Create a new prospect"""
    try:
        db_prospect = Prospect(**prospect.dict())
        db.add(db_prospect)
        db.commit()
        db.refresh(db_prospect)

        return {
            "id": db_prospect.id,
            "name": db_prospect.name,
            "email": db_prospect.email,
            "created_at": db_prospect.created_at
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create prospect: {str(e)}")


@router.get("/prospects")
async def list_prospects(db: Session = Depends(get_db)):
    """List all prospects"""
    prospects = db.query(Prospect).order_by(Prospect.created_at.desc()).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "email": p.email,
            "current_company": p.current_company,
            "current_title": p.current_title,
            "has_persona": p.persona is not None,
            "outreach_count": len(p.outreach_attempts),
            "created_at": p.created_at
        }
        for p in prospects
    ]


@router.get("/prospects/{prospect_id}")
async def get_prospect(prospect_id: int, db: Session = Depends(get_db)):
    """Get detailed prospect information"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()

    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    return {
        "id": prospect.id,
        "name": prospect.name,
        "email": prospect.email,
        "linkedin_url": prospect.linkedin_url,
        "twitter_handle": prospect.twitter_handle,
        "current_company": prospect.current_company,
        "current_title": prospect.current_title,
        "location": prospect.location,
        "persona": {
            "summary": prospect.persona.summary,
            "expertise_areas": prospect.persona.expertise_areas,
            "personality_traits": prospect.persona.personality_traits,
            "communication_style": prospect.persona.communication_style,
            "confidence_score": prospect.persona.confidence_score
        } if prospect.persona else None,
        "research_data_count": len(prospect.research_data),
        "messages_count": len(prospect.messages),
        "outreach_count": len(prospect.outreach_attempts),
        "created_at": prospect.created_at
    }


# ============== RESEARCH DATA ENDPOINTS ==============

@router.post("/prospects/{prospect_id}/research")
async def add_research_data(
    prospect_id: int,
    research: ResearchDataCreate,
    db: Session = Depends(get_db)
):
    """Add research data for a prospect and process it with appropriate agent"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    try:
        # Map source type to enum
        source_type_map = {
            "linkedin": ResearchSourceType.LINKEDIN,
            "google": ResearchSourceType.GOOGLE,
            "social_media": ResearchSourceType.SOCIAL_MEDIA,
            "manual": ResearchSourceType.MANUAL
        }

        source_type = source_type_map.get(research.source_type.lower())
        if not source_type:
            raise HTTPException(status_code=400, detail="Invalid source type")

        # Process with appropriate agent
        structured_data = {}

        if source_type == ResearchSourceType.LINKEDIN:
            agent = LinkedInResearchAgent()
            response = await agent.process(research.raw_text)
            if response.success:
                structured_data = response.data

        elif source_type == ResearchSourceType.GOOGLE:
            agent = GoogleResearchAgent()
            response = await agent.process(research.raw_text)
            if response.success:
                structured_data = response.data

        elif source_type == ResearchSourceType.SOCIAL_MEDIA:
            agent = SocialMediaResearchAgent()
            response = await agent.process(research.raw_text)
            if response.success:
                structured_data = response.data

        # Create research data record
        research_data = ResearchData(
            prospect_id=prospect_id,
            source_type=source_type,
            raw_text=research.raw_text,
            work_history=json.dumps(structured_data.get("work_history", [])),
            education=json.dumps(structured_data.get("education", [])),
            skills=json.dumps(structured_data.get("skills", [])),
            projects=json.dumps(structured_data.get("projects", [])),
            interests=json.dumps(structured_data.get("interests", [])),
            publications=json.dumps(structured_data.get("publications", []))
        )

        db.add(research_data)
        db.commit()
        db.refresh(research_data)

        return {
            "id": research_data.id,
            "source_type": research_data.source_type.value,
            "structured_data": structured_data,
            "collected_at": research_data.collected_at
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process research: {str(e)}")


@router.post("/prospects/{prospect_id}/linkedin-pdf")
async def upload_linkedin_pdf(
    prospect_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload LinkedIn PDF, extract data, and automatically generate persona"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    try:
        # Read PDF file
        pdf_bytes = await file.read()

        # Validate PDF
        if not is_valid_pdf(pdf_bytes):
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        # Extract text from PDF
        try:
            raw_text = extract_text_from_pdf(pdf_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")

        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="PDF appears to be empty or unreadable")

        # Process with LinkedIn agent
        agent = LinkedInResearchAgent()
        response = await agent.process(raw_text)

        if not response.success:
            raise HTTPException(status_code=500, detail=f"Failed to process LinkedIn data: {response.error}")

        structured_data = response.data

        # Store research data
        research_data = ResearchData(
            prospect_id=prospect_id,
            source_type=ResearchSourceType.LINKEDIN,
            raw_text=raw_text,
            work_history=json.dumps(structured_data.get("work_history", [])),
            education=json.dumps(structured_data.get("education", [])),
            skills=json.dumps(structured_data.get("skills", [])),
            projects=json.dumps(structured_data.get("projects", [])),
            interests=json.dumps(structured_data.get("interests", [])),
            publications=json.dumps(structured_data.get("publications", []))
        )

        db.add(research_data)
        db.commit()
        db.refresh(research_data)

        # Automatically generate persona
        linkedin_data = {
            "work_history": structured_data.get("work_history", []),
            "education": structured_data.get("education", []),
            "skills": structured_data.get("skills", []),
            "projects": structured_data.get("projects", []),
            "interests": structured_data.get("interests", [])
        }

        # Generate persona
        persona_agent = AgglomerationAgent()
        persona_response = await persona_agent.process(
            prospect_name=prospect.name,
            linkedin_data=linkedin_data
        )

        if not persona_response.success:
            # Research was saved but persona generation failed
            return {
                "research_id": research_data.id,
                "structured_data": structured_data,
                "persona_generated": False,
                "persona_error": persona_response.error,
                "message": "LinkedIn data extracted successfully, but persona generation failed"
            }

        persona_data = persona_response.data

        # Create or update persona
        if prospect.persona:
            persona = prospect.persona
            persona.summary = persona_data.get("summary")
            persona.career_trajectory = persona_data.get("career_trajectory")
            persona.expertise_areas = json.dumps(persona_data.get("expertise_areas", []))
            persona.notable_achievements = json.dumps(persona_data.get("notable_achievements", []))
            persona.personality_traits = json.dumps(persona_data.get("personality_traits", []))
            persona.communication_style = persona_data.get("communication_style")
            persona.interests_hobbies = json.dumps(persona_data.get("interests_hobbies", []))
            persona.values = json.dumps(persona_data.get("values", []))
            persona.connection_strategy = persona_data.get("connection_strategy")
            persona.conversation_starters = json.dumps(persona_data.get("conversation_starters", []))
            persona.common_ground = json.dumps(persona_data.get("common_ground", []))
            persona.confidence_score = persona_data.get("confidence_score", 0.5)
            persona.updated_at = datetime.utcnow()
        else:
            persona = Persona(
                prospect_id=prospect_id,
                summary=persona_data.get("summary"),
                career_trajectory=persona_data.get("career_trajectory"),
                expertise_areas=json.dumps(persona_data.get("expertise_areas", [])),
                notable_achievements=json.dumps(persona_data.get("notable_achievements", [])),
                personality_traits=json.dumps(persona_data.get("personality_traits", [])),
                communication_style=persona_data.get("communication_style"),
                interests_hobbies=json.dumps(persona_data.get("interests_hobbies", [])),
                values=json.dumps(persona_data.get("values", [])),
                connection_strategy=persona_data.get("connection_strategy"),
                conversation_starters=json.dumps(persona_data.get("conversation_starters", [])),
                common_ground=json.dumps(persona_data.get("common_ground", [])),
                confidence_score=persona_data.get("confidence_score", 0.5)
            )
            db.add(persona)

        db.commit()
        db.refresh(persona)

        return {
            "research_id": research_data.id,
            "structured_data": structured_data,
            "persona_generated": True,
            "persona": {
                "id": persona.id,
                "summary": persona.summary,
                "confidence_score": persona.confidence_score
            },
            "message": "LinkedIn PDF processed and persona generated successfully!"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


# ============== PERSONA ENDPOINTS ==============

@router.post("/prospects/{prospect_id}/persona")
async def generate_persona(prospect_id: int, db: Session = Depends(get_db)):
    """Generate or update persona for a prospect"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    try:
        # Gather all research data
        linkedin_data = None
        google_data = None
        social_media_data = None

        for research in prospect.research_data:
            data = {
                "work_history": json.loads(research.work_history) if research.work_history else [],
                "education": json.loads(research.education) if research.education else [],
                "skills": json.loads(research.skills) if research.skills else [],
                "projects": json.loads(research.projects) if research.projects else [],
                "interests": json.loads(research.interests) if research.interests else []
            }

            if research.source_type == ResearchSourceType.LINKEDIN:
                linkedin_data = data
            elif research.source_type == ResearchSourceType.GOOGLE:
                google_data = data
            elif research.source_type == ResearchSourceType.SOCIAL_MEDIA:
                social_media_data = data

        # Generate persona
        agent = AgglomerationAgent()
        response = await agent.process(
            prospect_name=prospect.name,
            linkedin_data=linkedin_data,
            google_data=google_data,
            social_media_data=social_media_data
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        persona_data = response.data

        # Create or update persona
        if prospect.persona:
            persona = prospect.persona
            persona.summary = persona_data.get("summary")
            persona.career_trajectory = persona_data.get("career_trajectory")
            persona.expertise_areas = json.dumps(persona_data.get("expertise_areas", []))
            persona.notable_achievements = json.dumps(persona_data.get("notable_achievements", []))
            persona.personality_traits = json.dumps(persona_data.get("personality_traits", []))
            persona.communication_style = persona_data.get("communication_style")
            persona.interests_hobbies = json.dumps(persona_data.get("interests_hobbies", []))
            persona.values = json.dumps(persona_data.get("values", []))
            persona.connection_strategy = persona_data.get("connection_strategy")
            persona.conversation_starters = json.dumps(persona_data.get("conversation_starters", []))
            persona.common_ground = json.dumps(persona_data.get("common_ground", []))
            persona.confidence_score = persona_data.get("confidence_score", 0.5)
            persona.updated_at = datetime.utcnow()
        else:
            persona = Persona(
                prospect_id=prospect_id,
                summary=persona_data.get("summary"),
                career_trajectory=persona_data.get("career_trajectory"),
                expertise_areas=json.dumps(persona_data.get("expertise_areas", [])),
                notable_achievements=json.dumps(persona_data.get("notable_achievements", [])),
                personality_traits=json.dumps(persona_data.get("personality_traits", [])),
                communication_style=persona_data.get("communication_style"),
                interests_hobbies=json.dumps(persona_data.get("interests_hobbies", [])),
                values=json.dumps(persona_data.get("values", [])),
                connection_strategy=persona_data.get("connection_strategy"),
                conversation_starters=json.dumps(persona_data.get("conversation_starters", [])),
                common_ground=json.dumps(persona_data.get("common_ground", [])),
                confidence_score=persona_data.get("confidence_score", 0.5)
            )
            db.add(persona)

        db.commit()
        db.refresh(persona)

        return {
            "id": persona.id,
            "summary": persona.summary,
            "career_trajectory": persona.career_trajectory,
            "expertise_areas": json.loads(persona.expertise_areas) if persona.expertise_areas else [],
            "personality_traits": json.loads(persona.personality_traits) if persona.personality_traits else [],
            "communication_style": persona.communication_style,
            "connection_strategy": persona.connection_strategy,
            "confidence_score": persona.confidence_score,
            "generated_at": persona.generated_at
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate persona: {str(e)}")


@router.get("/prospects/{prospect_id}/persona")
async def get_persona(prospect_id: int, db: Session = Depends(get_db)):
    """Get persona for a prospect"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    if not prospect.persona:
        raise HTTPException(status_code=404, detail="Persona not generated yet")

    persona = prospect.persona

    return {
        "id": persona.id,
        "summary": persona.summary,
        "career_trajectory": persona.career_trajectory,
        "expertise_areas": json.loads(persona.expertise_areas) if persona.expertise_areas else [],
        "notable_achievements": json.loads(persona.notable_achievements) if persona.notable_achievements else [],
        "personality_traits": json.loads(persona.personality_traits) if persona.personality_traits else [],
        "communication_style": persona.communication_style,
        "interests_hobbies": json.loads(persona.interests_hobbies) if persona.interests_hobbies else [],
        "values": json.loads(persona.values) if persona.values else [],
        "connection_strategy": persona.connection_strategy,
        "conversation_starters": json.loads(persona.conversation_starters) if persona.conversation_starters else [],
        "common_ground": json.loads(persona.common_ground) if persona.common_ground else [],
        "confidence_score": persona.confidence_score,
        "generated_at": persona.generated_at,
        "updated_at": persona.updated_at
    }


# ============== MESSAGE GENERATION ENDPOINTS ==============

@router.post("/prospects/{prospect_id}/message")
async def generate_message(
    prospect_id: int,
    request: MessageGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate a personalized outreach message"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    if not prospect.persona:
        raise HTTPException(status_code=400, detail="Persona must be generated first")

    try:
        # Parse persona data
        persona_data = {
            "summary": prospect.persona.summary,
            "career_trajectory": prospect.persona.career_trajectory,
            "expertise_areas": json.loads(prospect.persona.expertise_areas) if prospect.persona.expertise_areas else [],
            "personality_traits": json.loads(prospect.persona.personality_traits) if prospect.persona.personality_traits else [],
            "communication_style": prospect.persona.communication_style,
            "interests_hobbies": json.loads(prospect.persona.interests_hobbies) if prospect.persona.interests_hobbies else [],
            "connection_strategy": prospect.persona.connection_strategy,
            "conversation_starters": json.loads(prospect.persona.conversation_starters) if prospect.persona.conversation_starters else []
        }

        # Generate message
        agent = MessageAgent()
        response = await agent.process(
            prospect_name=prospect.name,
            persona=persona_data,
            channel=request.channel,
            degree_of_connection=request.degree_of_connection,
            familiarity_level=request.familiarity_level,
            tone=request.tone,
            custom_context=request.custom_context,
            message_variant=request.message_variant,
            user_info=request.user_info
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        message_data = response.data

        # Map channel string to enum
        channel_map = {
            "linkedin": OutreachChannel.LINKEDIN,
            "email": OutreachChannel.EMAIL,
            "twitter": OutreachChannel.TWITTER,
            "facebook": OutreachChannel.FACEBOOK
        }
        channel_enum = channel_map.get(request.channel.lower(), OutreachChannel.OTHER)

        # Save message to database
        message = OutreachMessage(
            prospect_id=prospect_id,
            subject=message_data.get("subject"),
            body=message_data.get("body"),
            channel=channel_enum,
            degree_of_connection=request.degree_of_connection,
            familiarity_level=request.familiarity_level,
            tone=request.tone,
            message_variant=request.message_variant,
            is_draft=True
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return {
            "id": message.id,
            "subject": message.subject,
            "body": message.body,
            "channel": message.channel.value,
            "tone": message.tone,
            "rationale": message_data.get("rationale"),
            "key_personalization": message_data.get("key_personalization", []),
            "estimated_effectiveness": message_data.get("estimated_effectiveness"),
            "generated_at": message.generated_at
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate message: {str(e)}")


@router.get("/prospects/{prospect_id}/messages")
async def get_messages(prospect_id: int, db: Session = Depends(get_db)):
    """Get all messages for a prospect"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    messages = db.query(OutreachMessage).filter(
        OutreachMessage.prospect_id == prospect_id
    ).order_by(OutreachMessage.generated_at.desc()).all()

    return [
        {
            "id": m.id,
            "subject": m.subject,
            "body": m.body,
            "channel": m.channel.value,
            "tone": m.tone,
            "message_variant": m.message_variant,
            "is_draft": m.is_draft,
            "generated_at": m.generated_at
        }
        for m in messages
    ]


# ============== OUTREACH TRACKING ENDPOINTS ==============

@router.post("/prospects/{prospect_id}/outreach")
async def log_outreach(
    prospect_id: int,
    outreach: OutreachAttemptCreate,
    db: Session = Depends(get_db)
):
    """Log an outreach attempt"""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    try:
        # Map channel and status
        channel_map = {
            "linkedin": OutreachChannel.LINKEDIN,
            "email": OutreachChannel.EMAIL,
            "twitter": OutreachChannel.TWITTER,
            "facebook": OutreachChannel.FACEBOOK
        }
        channel_enum = channel_map.get(outreach.channel.lower(), OutreachChannel.OTHER)

        attempt = OutreachAttempt(
            prospect_id=prospect_id,
            message_id=outreach.message_id,
            channel=channel_enum,
            status=OutreachStatus.SENT,
            sent_at=outreach.sent_at or datetime.utcnow()
        )

        db.add(attempt)

        # Mark message as not draft if message_id provided
        if outreach.message_id:
            message = db.query(OutreachMessage).filter(OutreachMessage.id == outreach.message_id).first()
            if message:
                message.is_draft = False

        db.commit()
        db.refresh(attempt)

        return {
            "id": attempt.id,
            "prospect_id": attempt.prospect_id,
            "channel": attempt.channel.value,
            "status": attempt.status.value,
            "sent_at": attempt.sent_at
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to log outreach: {str(e)}")


@router.patch("/outreach/{attempt_id}")
async def update_outreach(
    attempt_id: int,
    update: OutreachAttemptUpdate,
    db: Session = Depends(get_db)
):
    """Update an outreach attempt (e.g., mark as replied)"""
    attempt = db.query(OutreachAttempt).filter(OutreachAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Outreach attempt not found")

    try:
        if update.status:
            status_map = {
                "sent": OutreachStatus.SENT,
                "replied": OutreachStatus.REPLIED,
                "no_response": OutreachStatus.NO_RESPONSE,
                "bounced": OutreachStatus.BOUNCED
            }
            attempt.status = status_map.get(update.status.lower(), OutreachStatus.SENT)

        if update.received_response is not None:
            attempt.received_response = update.received_response

        if update.response_text:
            attempt.response_text = update.response_text

        if update.response_sentiment:
            attempt.response_sentiment = update.response_sentiment

        if update.replied_at:
            attempt.replied_at = update.replied_at

        attempt.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(attempt)

        return {
            "id": attempt.id,
            "status": attempt.status.value,
            "received_response": attempt.received_response,
            "replied_at": attempt.replied_at
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update outreach: {str(e)}")


@router.get("/outreach")
async def list_outreach(db: Session = Depends(get_db)):
    """List all outreach attempts"""
    attempts = db.query(OutreachAttempt).order_by(OutreachAttempt.sent_at.desc()).all()

    return [
        {
            "id": a.id,
            "prospect_id": a.prospect_id,
            "prospect_name": a.prospect.name,
            "channel": a.channel.value,
            "status": a.status.value,
            "received_response": a.received_response,
            "sent_at": a.sent_at,
            "replied_at": a.replied_at
        }
        for a in attempts
    ]


# ============== ANALYTICS ENDPOINTS ==============

@router.get("/analytics/performance")
async def get_analytics(db: Session = Depends(get_db)):
    """Get overall performance analytics"""
    try:
        attempts = db.query(OutreachAttempt).all()

        # Prepare data for analytics agent
        outreach_data = [
            {
                "id": a.id,
                "prospect_id": a.prospect_id,
                "prospect_name": a.prospect.name,
                "channel": a.channel.value,
                "status": a.status.value,
                "received_response": a.received_response,
                "sent_at": a.sent_at.isoformat() if a.sent_at else None,
                "replied_at": a.replied_at.isoformat() if a.replied_at else None,
                "response_sentiment": a.response_sentiment,
                "tone": a.message.tone if a.message else None,
                "message_variant": a.message.message_variant if a.message else None
            }
            for a in attempts if a.sent_at
        ]

        if not outreach_data:
            return {
                "message": "No outreach data available yet",
                "overall_metrics": {
                    "total_sent": 0,
                    "response_rate": 0.0
                }
            }

        agent = AnalyticsAgent()
        response = await agent.analyze_overall_performance(outreach_data)

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@router.get("/analytics/follow-ups")
async def get_follow_ups(db: Session = Depends(get_db)):
    """Get prospects that need follow-ups"""
    try:
        from ..config import config

        attempts = db.query(OutreachAttempt).all()

        outreach_data = [
            {
                "prospect_id": a.prospect_id,
                "prospect_name": a.prospect.name,
                "channel": a.channel.value,
                "status": a.status.value,
                "received_response": a.received_response,
                "sent_at": a.sent_at,
                "replied_at": a.replied_at
            }
            for a in attempts
        ]

        agent = AnalyticsAgent()
        response = agent.calculate_follow_ups_needed(
            outreach_data,
            follow_up_days=config.FOLLOW_UP_DAYS
        )

        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)

        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Follow-up calculation failed: {str(e)}")


# ============== HEALTH CHECK ==============

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
