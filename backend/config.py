import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/networking.db")

    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # Agent Configuration
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "claude-3-5-sonnet-20241022")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4096))
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

    # Analytics
    FOLLOW_UP_DAYS = int(os.getenv("FOLLOW_UP_DAYS", 3))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required. Please set it in .env file.")


config = Config()
