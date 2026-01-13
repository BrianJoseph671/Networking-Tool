from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
import enum

Base = declarative_base()


class ResearchSourceType(enum.Enum):
    LINKEDIN = "linkedin"
    GOOGLE = "google"
    SOCIAL_MEDIA = "social_media"
    MANUAL = "manual"


class OutreachChannel(enum.Enum):
    LINKEDIN = "linkedin"
    EMAIL = "email"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    OTHER = "other"


class OutreachStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    REPLIED = "replied"
    NO_RESPONSE = "no_response"
    BOUNCED = "bounced"


class Prospect(Base):
    """Main table for people we want to network with"""
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    twitter_handle = Column(String(100), nullable=True)

    # Basic info (manually entered or parsed)
    current_company = Column(String(255), nullable=True)
    current_title = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    research_data = relationship("ResearchData", back_populates="prospect", cascade="all, delete-orphan")
    persona = relationship("Persona", back_populates="prospect", uselist=False, cascade="all, delete-orphan")
    messages = relationship("OutreachMessage", back_populates="prospect", cascade="all, delete-orphan")
    outreach_attempts = relationship("OutreachAttempt", back_populates="prospect", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="prospect", cascade="all, delete-orphan")


class ResearchData(Base):
    """Raw research data collected by research agents"""
    __tablename__ = "research_data"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False)
    source_type = Column(Enum(ResearchSourceType), nullable=False)

    # Structured data fields
    work_history = Column(Text, nullable=True)  # JSON string
    education = Column(Text, nullable=True)      # JSON string
    skills = Column(Text, nullable=True)         # Comma-separated or JSON
    projects = Column(Text, nullable=True)       # JSON string
    interests = Column(Text, nullable=True)      # JSON string
    publications = Column(Text, nullable=True)   # JSON string

    # Raw text data
    raw_text = Column(Text, nullable=True)

    # Metadata
    collected_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prospect = relationship("Prospect", back_populates="research_data")


class Persona(Base):
    """Agglomerated persona built from all research data"""
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False, unique=True)

    # Persona summary
    summary = Column(Text, nullable=True)

    # Professional profile
    career_trajectory = Column(Text, nullable=True)
    expertise_areas = Column(Text, nullable=True)
    notable_achievements = Column(Text, nullable=True)

    # Personal traits
    personality_traits = Column(Text, nullable=True)
    communication_style = Column(Text, nullable=True)
    interests_hobbies = Column(Text, nullable=True)
    values = Column(Text, nullable=True)

    # Networking insights
    connection_strategy = Column(Text, nullable=True)
    conversation_starters = Column(Text, nullable=True)
    common_ground = Column(Text, nullable=True)

    # Metadata
    confidence_score = Column(Float, nullable=True)  # 0-1 score of how complete the persona is
    generated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prospect = relationship("Prospect", back_populates="persona")


class OutreachMessage(Base):
    """Generated outreach messages"""
    __tablename__ = "outreach_messages"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False)

    # Message content
    subject = Column(String(500), nullable=True)  # For email
    body = Column(Text, nullable=False)

    # Generation parameters
    channel = Column(Enum(OutreachChannel), nullable=False)
    degree_of_connection = Column(Integer, nullable=True)  # 1st, 2nd, 3rd degree
    familiarity_level = Column(String(50), nullable=True)  # stranger, acquaintance, colleague, friend
    tone = Column(String(50), nullable=True)  # professional, casual, warm, direct
    message_variant = Column(String(50), nullable=True)  # For A/B testing (variant_a, variant_b, etc.)

    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    is_draft = Column(Boolean, default=True)

    # Relationships
    prospect = relationship("Prospect", back_populates="messages")
    outreach_attempt = relationship("OutreachAttempt", back_populates="message", uselist=False)


class OutreachAttempt(Base):
    """Tracking of actual outreach attempts"""
    __tablename__ = "outreach_attempts"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("outreach_messages.id"), nullable=True)

    # Attempt details
    channel = Column(Enum(OutreachChannel), nullable=False)
    status = Column(Enum(OutreachStatus), nullable=False, default=OutreachStatus.SENT)

    # Timestamps
    sent_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)

    # Response tracking
    received_response = Column(Boolean, default=False)
    response_text = Column(Text, nullable=True)
    response_sentiment = Column(String(50), nullable=True)  # positive, neutral, negative

    # Analytics
    open_count = Column(Integer, default=0)  # If tracking email opens
    click_count = Column(Integer, default=0)  # If tracking link clicks

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prospect = relationship("Prospect", back_populates="outreach_attempts")
    message = relationship("OutreachMessage", back_populates="outreach_attempt")


class FollowUp(Base):
    """Scheduled follow-ups and reminders"""
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"), nullable=False)

    # Follow-up details
    scheduled_date = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=True)  # no_response, check_in, etc.
    notes = Column(Text, nullable=True)

    # Status
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    snoozed_until = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prospect = relationship("Prospect", back_populates="follow_ups")


# Database setup functions
_engine = None
_SessionLocal = None


def init_db(database_url: str = "sqlite:///./data/networking.db"):
    """Initialize the database"""
    global _engine, _SessionLocal

    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    # Create all tables
    Base.metadata.create_all(bind=_engine)

    return _engine


def get_db() -> Session:
    """Get database session"""
    if _SessionLocal is None:
        raise Exception("Database not initialized. Call init_db() first.")

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
