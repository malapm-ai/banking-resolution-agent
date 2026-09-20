# ============================================
# LOGGER MODULE
# ============================================
# Logs cases, evidence, reasoning, and audit trail to database

import sqlite3
import sys
from pathlib import Path
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from config import DATABASE_PATH

# ============================================
# LOG DISPUTE CASE
# ============================================

def log_dispute(dispute_record, full_case_data):
    """
    Log a dispute case to the database.
    
    Args:
        dispute_record (dict): Main dispute information
        full_case_data (dict): Complete case data including all steps
    
    Returns:
        dict: {
            "status": "success" or "error",
            "message": "...",
            "case_id": "..."
        }
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        case_id = dispute_record["id"]
        
        # Insert into disputes table
        cursor.execute("""
            INSERT INTO disputes (
                id, customer_id, transaction_id, dispute_type, customer_claim,
                decision, confidence_score, reasoning_summary, action_taken,
                refund_amount, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            dispute_record.get("customer_id"),
            dispute_record.get("transaction_id"),
            dispute_record.get("dispute_type"),
            dispute_record.get("customer_claim"),
            dispute_record.get("decision"),
            dispute_record.get("confidence_score", 0.0),
            dispute_record.get("reasoning_summary", ""),
            dispute_record.get("action_taken", ""),
            dispute_record.get("refund_amount", 0.0),
            datetime.now().isoformat()
        ))
        
        # Log evidence
        if "steps" in full_case_data:
            for step_name, step_result in full_case_data["steps"].items():
                if isinstance(step_result, dict) and "data" in step_result:
                    cursor.execute("""
                        INSERT INTO case_evidence (case_id, tool_name, tool_output, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (
                        case_id,
                        step_name,
                        json.dumps(step_result["data"]),
                        datetime.now().isoformat()
                    ))
        
        # Log reasoning (LLM steps)
        step_count = 0
        if "understanding" in full_case_data:
            cursor.execute("""
                INSERT INTO case_reasoning (case_id, step_name, llm_prompt, llm_response, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                case_id,
                "UNDERSTAND",
                "Understanding extraction",
                json.dumps(full_case_data["understanding"]),
                datetime.now().isoformat()
            ))
            step_count += 1
        
        if "analysis" in full_case_data:
            cursor.execute("""
                INSERT INTO case_reasoning (case_id, step_name, llm_prompt, llm_response, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                case_id,
                "ANALYZE",
                "Evidence analysis",
                json.dumps(full_case_data["analysis"]),
                datetime.now().isoformat()
            ))
            step_count += 1
        
        if "decision" in full_case_data:
            cursor.execute("""
                INSERT INTO case_reasoning (case_id, step_name, llm_prompt, llm_response, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                case_id,
                "DECIDE",
                "Final decision making",
                json.dumps(full_case_data["decision"]),
                datetime.now().isoformat()
            ))
            step_count += 1
        
        # Log audit trail
        cursor.execute("""
            INSERT INTO audit_trail (case_id, event, actor, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            case_id,
            "CASE_CREATED",
            "SYSTEM",
            json.dumps({
                "dispute_type": dispute_record.get("dispute_type"),
                "confidence_score": dispute_record.get("confidence_score", 0.0),
                "action": dispute_record.get("action_taken")
            }),
            datetime.now().isoformat()
        ))
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Case {case_id} logged to database",
            "case_id": case_id,
            "evidence_records": len(full_case_data.get("steps", {})),
            "reasoning_records": step_count,
            "audit_trails": 1
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to log case: {str(e)}",
            "case_id": dispute_record.get("id", "UNKNOWN"),
            "error": str(e)
        }

# ============================================
# LOG ESCALATION
# ============================================

def log_escalation(case_id, reason, escalated_to):
    """
    Log case escalation to database.
    
    Args:
        case_id (str): Case ID
        reason (str): Why case was escalated
        escalated_to (str): Team/person it was escalated to
    
    Returns:
        dict: {status, message}
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO escalations (case_id, reason, escalated_to, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            case_id,
            reason,
            escalated_to,
            datetime.now().isoformat()
        ))
        
        # Log in audit trail too
        cursor.execute("""
            INSERT INTO audit_trail (case_id, event, actor, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            case_id,
            "CASE_ESCALATED",
            "SYSTEM",
            json.dumps({"escalated_to": escalated_to, "reason": reason}),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Case {case_id} escalated to {escalated_to}"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to log escalation: {str(e)}"
        }

# ============================================
# LOG CUSTOMER SATISFACTION
# ============================================

def log_satisfaction(case_id, satisfied, reason=""):
    """
    Log customer satisfaction survey response.
    
    Args:
        case_id (str): Case ID
        satisfied (bool): Customer satisfied?
        reason (str): Optional reason/feedback
    
    Returns:
        dict: {status, message}
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        satisfaction_value = "YES" if satisfied else "NO"
        
        # Update disputes table
        cursor.execute("""
            UPDATE disputes 
            SET customer_satisfied = ?, satisfaction_reason = ?
            WHERE id = ?
        """, (
            satisfaction_value,
            reason,
            case_id
        ))
        
        # Log in audit trail
        cursor.execute("""
            INSERT INTO audit_trail (case_id, event, actor, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            case_id,
            "SATISFACTION_SURVEY",
            "CUSTOMER",
            json.dumps({"satisfied": satisfied, "reason": reason}),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Satisfaction recorded for case {case_id}"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to log satisfaction: {str(e)}"
        }

# ============================================
# RETRIEVE CASE
# ============================================

def retrieve_case(case_id):
    """
    Retrieve complete case data from database.
    
    Args:
        case_id (str): Case ID
    
    Returns:
        dict: Complete case information
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get dispute
        cursor.execute("SELECT * FROM disputes WHERE id = ?", (case_id,))
        dispute = cursor.fetchone()
        
        if not dispute:
            conn.close()
            return {"status": "error", "message": f"Case {case_id} not found"}
        
        # Get evidence
        cursor.execute("SELECT * FROM case_evidence WHERE case_id = ?", (case_id,))
        evidence_rows = cursor.fetchall()
        evidence = [dict(row) for row in evidence_rows]
        
        # Get reasoning
        cursor.execute("SELECT * FROM case_reasoning WHERE case_id = ?", (case_id,))
        reasoning_rows = cursor.fetchall()
        reasoning = [dict(row) for row in reasoning_rows]
        
        # Get escalations
        cursor.execute("SELECT * FROM escalations WHERE case_id = ?", (case_id,))
        escalation_rows = cursor.fetchall()
        escalations = [dict(row) for row in escalation_rows]
        
        # Get audit trail
        cursor.execute("SELECT * FROM audit_trail WHERE case_id = ? ORDER BY timestamp", (case_id,))
        audit_rows = cursor.fetchall()
        audit_trail = [dict(row) for row in audit_rows]
        
        conn.close()
        
        return {
            "status": "success",
            "case": dict(dispute),
            "evidence": evidence,
            "reasoning": reasoning,
            "escalations": escalations,
            "audit_trail": audit_trail
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve case: {str(e)}"
        }

# ============================================
# QUERY CASES
# ============================================

def query_cases(filters=None, limit=10):
    """
    Query cases from database with optional filters.
    
    Args:
        filters (dict): {status, dispute_type, decision, date_from, date_to}
        limit (int): Maximum records to return
    
    Returns:
        dict: {status, cases, count}
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Base query
        query = "SELECT * FROM disputes WHERE 1=1"
        params = []
        
        if filters:
            if filters.get("dispute_type"):
                query += " AND dispute_type = ?"
                params.append(filters["dispute_type"])
            
            if filters.get("decision"):
                query += " AND decision = ?"
                params.append(filters["decision"])
            
            if filters.get("date_from"):
                query += " AND created_at >= ?"
                params.append(filters["date_from"])
            
            if filters.get("date_to"):
                query += " AND created_at <= ?"
                params.append(filters["date_to"])
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        cases = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "status": "success",
            "count": len(cases),
            "cases": cases
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to query cases: {str(e)}",
            "cases": []
        }
