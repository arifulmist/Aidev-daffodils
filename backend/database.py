import json
from datetime import datetime
from typing import Generator
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.config import settings

# Engine configuration (works seamlessly on SQLite & PostgreSQL/Supabase)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), index=True, nullable=False)
    merchant_id = Column(String(50), index=True, nullable=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False, default="MERCHANT_PAYMENT")
    transaction_status = Column(String(50), nullable=False, default="SUCCESS")
    failure_code = Column(String(50), nullable=False, default="NONE")
    ground_truth_root_cause = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    events = relationship("TransactionEvent", back_populates="transaction", cascade="all, delete-orphan", order_by="TransactionEvent.timestamp")
    complaints = relationship("Complaint", back_populates="transaction")


class TransactionEvent(Base):
    __tablename__ = "transaction_events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(50), ForeignKey("transactions.transaction_id"), index=True, nullable=False)
    event_type = Column(String(80), nullable=False)
    event_status = Column(String(50), nullable=False, default="SUCCESS")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata_json = Column(Text, nullable=True, default="{}")

    transaction = relationship("Transaction", back_populates="events")

    @property
    def event_metadata(self):
        try:
            return json.loads(self.metadata_json or "{}")
        except Exception:
            return {}


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), index=True, nullable=False)
    transaction_id = Column(String(50), ForeignKey("transactions.transaction_id"), nullable=True, index=True)
    complaint_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="TRANSACTION_DISPUTE")
    status = Column(String(50), nullable=False, default="NEW")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    transaction = relationship("Transaction", back_populates="complaints")
    case = relationship("Case", back_populates="complaint", uselist=False)


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(50), primary_key=True, index=True)
    complaint_id = Column(String(50), ForeignKey("complaints.complaint_id"), unique=True, index=True)
    transaction_id = Column(String(50), nullable=True, index=True)
    root_cause = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    priority = Column(String(20), nullable=False, default="MEDIUM")
    assigned_team = Column(String(80), nullable=False, default="Reconciliation")
    recommendation = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="OPEN")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="case")
    resolution_records = relationship("ResolutionHistory", back_populates="case", cascade="all, delete-orphan")


class ResolutionHistory(Base):
    __tablename__ = "resolution_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), ForeignKey("cases.case_id"), index=True, nullable=False)
    predicted_root_cause = Column(String(100), nullable=False)
    actual_root_cause = Column(String(100), nullable=False)
    predicted_team = Column(String(80), nullable=False)
    actual_team = Column(String(80), nullable=False)
    operator_action = Column(String(50), nullable=False, default="ACCEPTED")
    resolved_by = Column(String(100), nullable=False, default="Ops_Officer")
    resolution_notes = Column(Text, nullable=True)
    is_feedback_approved = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    case = relationship("Case", back_populates="resolution_records")


class HistoricalCase(Base):
    __tablename__ = "historical_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_code = Column(String(50), unique=True, index=True)
    title = Column(String(200), nullable=False)
    scenario = Column(String(100), nullable=False)
    symptoms = Column(Text, nullable=False)
    root_cause = Column(String(100), nullable=False)
    resolution = Column(Text, nullable=False)
    assigned_team = Column(String(80), nullable=False)
    embedding_json = Column(Text, nullable=True)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
