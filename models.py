# ============================================
# DATABASE MODELS
# ============================================
# Database structure definitions

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Customer model
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    account_type = Column(String)
    kyc_status = Column(String)
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    
    transactions = relationship("Transaction", back_populates="customer")
    disputes = relationship("Dispute", back_populates="customer")

# Transaction model
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    merchant = Column(String)
    merchant_category = Column(String)
    transaction_date = Column(DateTime)
    posting_date = Column(DateTime)
    location = Column(String)
    status = Column(String)
    auth_method = Column(String)
    
    customer = relationship("Customer", back_populates="transactions")
    disputes = relationship("Dispute", back_populates="transaction")

# Dispute model
class Dispute(Base):
    __tablename__ = "disputes"
    
    id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    dispute_type = Column(String)
    customer_claim = Column(String)
    decision = Column(String)
    confidence_score = Column(Float)
    reasoning_summary = Column(String)
    action_taken = Column(String)
    refund_amount = Column(Float)
    customer_satisfied = Column(String)
    satisfaction_reason = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime)
    resolution_time_seconds = Column(Integer)
    
    customer = relationship("Customer", back_populates="disputes")
    transaction = relationship("Transaction", back_populates="disputes")
    evidence = relationship("CaseEvidence", back_populates="dispute")
    reasoning = relationship("CaseReasoning", back_populates="dispute")
    escalations = relationship("Escalation", back_populates="dispute")
    audit_trail = relationship("AuditTrail", back_populates="dispute")

# Case Evidence model
class CaseEvidence(Base):
    __tablename__ = "case_evidence"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    tool_name = Column(String)
    tool_output = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    
    dispute = relationship("Dispute", back_populates="evidence")

# Case Reasoning model
class CaseReasoning(Base):
    __tablename__ = "case_reasoning"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    step_name = Column(String)
    llm_prompt = Column(String)
    llm_response = Column(String)
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    
    dispute = relationship("Dispute", back_populates="reasoning")

# Escalation model
class Escalation(Base):
    __tablename__ = "escalations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    reason = Column(String)
    escalated_to = Column(String)
    contact_method = Column(String)
    support_notes = Column(String)
    override_decision = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    dispute = relationship("Dispute", back_populates="escalations")

# Audit Trail model
class AuditTrail(Base):
    __tablename__ = "audit_trail"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    event = Column(String)
    actor = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    dispute = relationship("Dispute", back_populates="audit_trail")
