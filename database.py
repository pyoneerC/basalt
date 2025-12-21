"""
Database models for Basalt SaaS
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./basalt.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    company = Column(String(255))
    
    # Subscription
    tier = Column(String(50), default="free")  # free, pro, enterprise
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    
    # Limits
    monthly_limit = Column(Integer, default=10)  # Free tier: 10/month
    notarizations_this_month = Column(Integer, default=0)
    reset_date = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user")
    notarizations = relationship("Notarization", back_populates="user")


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), default="Default")
    
    # Permissions
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class Notarization(Base):
    __tablename__ = "notarizations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # File info
    original_filename = Column(String(255))
    file_type = Column(String(100))
    file_size = Column(Integer)  # bytes
    
    # Proof data
    ipfs_cid = Column(String(100), index=True)
    sha256_hash = Column(String(64))
    solana_tx = Column(String(100))
    
    # Status
    status = Column(String(50), default="completed")  # pending, completed, failed
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notarizations")


# Pricing tiers configuration
PRICING_TIERS = {
    "free": {
        "name": "Free",
        "price": 0,
        "monthly_limit": 10,
        "features": [
            "10 notarizations/month",
            "C2PA signing",
            "IPFS storage",
            "Blockchain anchoring",
            "Verification pages",
        ],
        "api_access": False,
    },
    "pro": {
        "name": "Pro",
        "price": 29,
        "monthly_limit": 500,
        "features": [
            "500 notarizations/month",
            "Everything in Free",
            "REST API access",
            "API key management",
            "Priority support",
        ],
        "api_access": True,
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 299,
        "monthly_limit": 10000,
        "features": [
            "10,000 notarizations/month",
            "Everything in Pro",
            "Unlimited API keys",
            "Webhook integrations",
            "Dedicated support",
            "Custom SLA",
        ],
        "api_access": True,
    },
}


def init_db():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
