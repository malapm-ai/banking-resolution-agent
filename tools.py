# ============================================
# BANKING RESOLUTION AGENT - CORE TOOLS
# ============================================
# 8 functions that the agent can call to gather info and take action

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import random

# Add src to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from config import DATABASE_PATH

# ============================================
# TOOL 1: CUSTOMER PROFILE
# ============================================
def customer_profile(customer_id):
    """
    Fetch customer details from database.
    Returns: name, email, phone, account_type, kyc_status, risk_score
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {
                "status": "error",
                "message": f"Customer {customer_id} not found",
                "data": None
            }
        
        return {
            "status": "success",
            "message": "Customer profile retrieved",
            "data": {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"],
                "account_type": row["account_type"],
                "kyc_status": row["kyc_status"],
                "risk_score": row["risk_score"],
                "created_at": row["created_at"]
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

# ============================================
# TOOL 2: TRANSACTION SEARCH
# ============================================
def transaction_search(customer_id, transaction_id=None, limit=10):
    """
    Find transactions for a customer.
    If transaction_id is provided, fetch that specific one.
    Otherwise, return last N transactions (default 10).
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if transaction_id:
            # Fetch specific transaction
            cursor.execute(
                "SELECT * FROM transactions WHERE id = ? AND customer_id = ?",
                (transaction_id, customer_id)
            )
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {
                    "status": "error",
                    "message": f"Transaction {transaction_id} not found",
                    "data": None
                }
            
            return {
                "status": "success",
                "message": "Transaction found",
                "data": {
                    "id": row["id"],
                    "customer_id": row["customer_id"],
                    "amount": row["amount"],
                    "merchant": row["merchant"],
                    "merchant_category": row["merchant_category"],
                    "transaction_date": row["transaction_date"],
                    "posting_date": row["posting_date"],
                    "location": row["location"],
                    "status": row["status"],
                    "auth_method": row["auth_method"]
                }
            }
        else:
            # Fetch last N transactions
            cursor.execute(
                """SELECT * FROM transactions 
                   WHERE customer_id = ? 
                   ORDER BY transaction_date DESC 
                   LIMIT ?""",
                (customer_id, limit)
            )
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return {
                    "status": "success",
                    "message": "No transactions found",
                    "data": []
                }
            
            transactions = []
            for row in rows:
                transactions.append({
                    "id": row["id"],
                    "amount": row["amount"],
                    "merchant": row["merchant"],
                    "merchant_category": row["merchant_category"],
                    "transaction_date": row["transaction_date"],
                    "posting_date": row["posting_date"],
                    "location": row["location"],
                    "status": row["status"],
                    "auth_method": row["auth_method"]
                })
            
            return {
                "status": "success",
                "message": f"Found {len(transactions)} transactions",
                "data": transactions
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

# ============================================
# TOOL 3: FRAUD DETECTION
# ============================================
def fraud_detection(transaction_id, customer_id):
    """
    Analyze transaction for fraud patterns.
    Returns fraud risk score (0.0 to 1.0).
    Mock implementation - real version would call ML model.
    """
    try:
        # Get transaction details
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM transactions WHERE id = ? AND customer_id = ?",
            (transaction_id, customer_id)
        )
        transaction = cursor.fetchone()
        
        if not transaction:
            conn.close()
            return {
                "status": "error",
                "message": "Transaction not found",
                "data": None
            }
        
        # Mock fraud scoring based on transaction properties
        fraud_score = 0.0
        indicators = []
        
        # High amount transactions slightly higher risk
        if transaction["amount"] > 50000:
            fraud_score += 0.15
            indicators.append("high_amount")
        
        # International locations slightly higher risk
        if transaction["location"] and "international" in transaction["location"].lower():
            fraud_score += 0.20
            indicators.append("international")
        
        # Online merchants slightly higher risk
        if transaction["merchant_category"] and "online" in transaction["merchant_category"].lower():
            fraud_score += 0.10
            indicators.append("online_merchant")
        
        # Add random variation (0.0 to 0.15) for realism
        fraud_score += random.uniform(0.0, 0.15)
        fraud_score = min(fraud_score, 1.0)  # Cap at 1.0
        
        conn.close()
        
        return {
            "status": "success",
            "message": "Fraud analysis completed",
            "data": {
                "fraud_score": round(fraud_score, 3),
                "risk_level": "HIGH" if fraud_score > 0.7 else "MEDIUM" if fraud_score > 0.4 else "LOW",
                "indicators": indicators,
                "recommendation": "INVESTIGATE" if fraud_score > 0.7 else "MONITOR" if fraud_score > 0.4 else "APPROVED"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

# ============================================
# TOOL 4: RISK SCORING
# ============================================
def risk_scoring(customer_id):
    """
    Calculate customer risk profile.
    Returns overall risk score and risk level.
    Considers: account age, kyc status, recent disputes, transaction patterns.
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get customer
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            conn.close()
            return {
                "status": "error",
                "message": f"Customer {customer_id} not found",
                "data": None
            }
        
        risk_score = 0.0
        risk_factors = []
        
        # KYC status check
        if customer["kyc_status"] != "VERIFIED":
            risk_score += 0.20
            risk_factors.append("kyc_not_verified")
        
        # Account age check (use stored risk_score as proxy)
        if customer["risk_score"] is not None:
            risk_score += customer["risk_score"] * 0.3
        
        # Count recent disputes
        cursor.execute(
            "SELECT COUNT(*) as count FROM disputes WHERE customer_id = ? AND created_at > datetime('now', '-90 days')",
            (customer_id,)
        )
        recent_disputes = cursor.fetchone()["count"]
        if recent_disputes > 2:
            risk_score += 0.25
            risk_factors.append(f"multiple_disputes_90d ({recent_disputes})")
        
        # Count total transactions
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE customer_id = ?", (customer_id,))
        total_txns = cursor.fetchone()["count"]
        if total_txns < 5:
            risk_score += 0.15
            risk_factors.append("low_transaction_history")
        
        risk_score = min(risk_score, 1.0)
        conn.close()
        
        return {
            "status": "success",
            "message": "Risk analysis completed",
            "data": {
                "risk_score": round(risk_score, 3),
                "risk_level": "HIGH" if risk_score > 0.7 else "MEDIUM" if risk_score > 0.4 else "LOW",
                "risk_factors": risk_factors,
                "recommendation": "ESCALATE" if risk_score > 0.7 else "REVIEW" if risk_score > 0.4 else "STANDARD"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

# ============================================
# TOOL 5: POLICY RETRIEVAL (RAG)
# ============================================
def policy_retrieval(query):
    """
    Search policies using RAG (Retrieval-Augmented Generation).
    This is a placeholder - will be filled in by rag_handler.py
    Returns relevant policy sections.
    """
    try:
        # For now, return mock policies
        # In full implementation, this will call sentence-transformers embeddings
        policies = {
            "UNAUTHORIZED": "Policy UNAUTH-001: Unauthorized transactions are refunded within 5-7 business days. Customer must file dispute within 60 days of discovery.",
            "DUPLICATE": "Policy DUP-001: Duplicate charge refunds are processed immediately upon verification. Investigation period: 3-5 business days.",
            "AMOUNT_MISMATCH": "Policy AMT-001: Amount discrepancy disputes are escalated to merchant for verification. Resolution time: 10-15 business days.",
            "NO_SERVICE": "Policy SVC-001: No service disputes require proof of service attempt. Refund approved if service not delivered.",
            "DEFECTIVE": "Policy DEF-001: Defective product disputes require photographic evidence. Return/refund process initiated within 7 days.",
            "CANCELLED": "Policy CAN-001: Cancelled service disputes are verified with merchant. Refund timeline depends on merchant response.",
            "UNDELIVERED": "Policy UND-001: Undelivered item disputes require tracking confirmation. Refund or re-delivery arranged within 10 business days.",
            "MERCHANT_ERROR": "Policy MER-001: Merchant error disputes (incorrect charges, billing errors) are refunded after verification.",
            "OTHERS": "Policy OTH-001: Other dispute types are evaluated on case-by-case basis. Standard resolution time: 15-20 business days."
        }
        
        return {
            "status": "success",
            "message": "Policies retrieved",
            "data": policies
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

# ============================================
# TOOL 6: RULES ENGINE
# ============================================
def rules_engine(dispute_type, confidence_score, customer_risk, fraud_risk):
    """
    Apply business rules to determine action.
    Inputs: dispute_type, confidence_score (0-1), customer_risk (0-1), fraud_risk (0-1)
    Returns: decision (APPROVE, REJECT, INVESTIGATE, ESCALATE)
    """
    try:
        decision = "INVESTIGATE"  # Default
        reason = ""
        
        # Rule 1: High fraud risk always investigate
        if fraud_risk > 0.7:
            decision = "INVESTIGATE"
            reason = "High fraud risk detected"
        
        # Rule 2: High customer risk always escalate
        elif customer_risk > 0.8:
            decision = "ESCALATE"
            reason = "Customer risk profile exceeds threshold"
        
        # Rule 3: High confidence + low risk = auto-approve
        elif confidence_score > 0.85 and customer_risk < 0.3 and fraud_risk < 0.3:
            decision = "APPROVE"
            reason = f"High confidence ({confidence_score:.2%}) and low risk profile"
        
        # Rule 4: Medium confidence = investigate
        elif 0.75 <= confidence_score <= 0.85:
            decision = "INVESTIGATE"
            reason = f"Medium confidence ({confidence_score:.2%}) - human review needed"
        
        # Rule 5: Low confidence = escalate
        elif confidence_score < 0.75:
            decision = "ESCALATE"
            reason = f"Low confidence ({confidence_score:.2%}) - escalate to specialist"
        
        return {
            "status": "success",
            "message": "Rules engine processed",
            "data": {
                "decision": decision,
                "reason": reason,
                "confidence": confidence_score,
                "customer_risk": customer_risk,
                "fraud_risk": fraud_risk
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

# ============================================
# TOOL 7: AUDIT LOGGER
# ============================================
def audit_logger(case_id, event, actor, details):
    """
    Log an event to audit trail.
    Used for compliance and investigation.
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Insert audit record
        cursor.execute("""
            INSERT INTO audit_trail (case_id, event, actor, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            case_id,
            event,
            actor,
            json.dumps(details) if isinstance(details, dict) else details,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Logged: {event}",
            "data": {
                "case_id": case_id,
                "event": event,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

# ============================================
# TOOL 8: NOTIFICATION SERVICE
# ============================================
def notification_service(customer_id, message_type, message_body):
    """
    Send notification to customer.
    Types: EMAIL, SMS, IN_APP
    In MVP: just logs, doesn't actually send.
    """
    try:
        # Get customer contact info
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        conn.close()
        
        if not customer:
            return {
                "status": "error",
                "message": f"Customer {customer_id} not found",
                "data": None
            }
        
        # Log notification (MVP doesn't actually send)
        notification_log = {
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "customer_email": customer["email"],
            "customer_phone": customer["phone"],
            "message_type": message_type,
            "message_body": message_body,
            "sent_at": datetime.now().isoformat(),
            "status": "SENT_MOCK"  # MVP uses mock sending
        }
        
        return {
            "status": "success",
            "message": f"Notification prepared ({message_type})",
            "data": notification_log
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

# ============================================
# TOOL REGISTRY
# ============================================
# Dictionary of all available tools
TOOL_REGISTRY = {
    "customer_profile": customer_profile,
    "transaction_search": transaction_search,
    "fraud_detection": fraud_detection,
    "risk_scoring": risk_scoring,
    "policy_retrieval": policy_retrieval,
    "rules_engine": rules_engine,
    "audit_logger": audit_logger,
    "notification_service": notification_service
}

def execute_tool(tool_name, *args, **kwargs):
    """
    Execute a tool by name.
    Used by the agent executor.
    """
    if tool_name not in TOOL_REGISTRY:
        return {
            "status": "error",
            "message": f"Tool '{tool_name}' not found",
            "data": None
        }
    
    try:
        tool_func = TOOL_REGISTRY[tool_name]
        return tool_func(*args, **kwargs)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error executing {tool_name}: {str(e)}",
            "data": None
        }
