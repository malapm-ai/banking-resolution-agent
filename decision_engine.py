# ============================================
# DECISION ENGINE
# ============================================
# Confidence scoring and escalation logic

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from config import CONFIDENCE_THRESHOLDS

# ============================================
# CONFIDENCE SCORING
# ============================================

def calculate_confidence(evidence, analysis_result, policy_match):
    """
    Calculate confidence score (0.0 to 1.0) based on evidence quality.
    
    Args:
        evidence (dict): Collected evidence from tools
        analysis_result (dict): LLM analysis output
        policy_match (dict): How well the case matches policy
    
    Returns:
        float: Confidence score (0.0 to 1.0)
    """
    
    base_score = 0.5  # Start neutral
    
    # ===== EVIDENCE FACTORS =====
    # Good fraud detection score reduces dispute validity
    if "fraud_detection" in evidence:
        fraud_score = evidence["fraud_detection"].get("fraud_score", 0.0)
        if fraud_score > 0.7:
            base_score -= 0.15  # Lower confidence if fraud suspected
        elif fraud_score < 0.3:
            base_score += 0.10  # Higher confidence if fraud unlikely
    
    # Customer risk score affects confidence
    if "risk_scoring" in evidence:
        risk_data = evidence["risk_scoring"].get("data")
        if risk_data and isinstance(risk_data, dict):
            risk_level = risk_data.get("risk_level", "MEDIUM")
            
            if risk_level == "HIGH":
                base_score -= 0.10  # Lower confidence for high-risk customers
            elif risk_level == "LOW":
                base_score += 0.05  # Higher confidence for low-risk customers
    
    # Transaction details clarity
    if "transaction_search" in evidence:
        tx_data = evidence["transaction_search"].get("data")
        if tx_data:
            # Transaction found and complete = higher confidence
            if isinstance(tx_data, dict):
                base_score += 0.15
            elif isinstance(tx_data, list) and len(tx_data) > 0:
                base_score += 0.10
    
    # ===== ANALYSIS FACTORS =====
    if analysis_result and "data" in analysis_result:
        analysis_data = analysis_result["data"]
        
        # Supporting evidence count
        supporting = len(analysis_data.get("supporting_evidence", []))
        if supporting >= 3:
            base_score += 0.15
        elif supporting >= 1:
            base_score += 0.08
        
        # Contradicting evidence count (reduces confidence)
        contradicting = len(analysis_data.get("contradicting_evidence", []))
        if contradicting >= 2:
            base_score -= 0.15
        elif contradicting >= 1:
            base_score -= 0.08
        
        # Missing information (reduces confidence)
        missing = len(analysis_data.get("missing_info", []))
        if missing >= 3:
            base_score -= 0.10
        elif missing >= 1:
            base_score -= 0.05
        
        # Preliminary assessment from LLM
        assessment = analysis_data.get("preliminary_assessment", "UNCLEAR")
        if assessment == "LIKELY_VALID":
            base_score += 0.20
        elif assessment == "LIKELY_INVALID":
            base_score -= 0.20
        # UNCLEAR adds nothing
    
    # ===== POLICY FACTORS =====
    if policy_match and "data" in policy_match:
        policy_data = policy_match["data"]
        
        # Clear policy guidance = higher confidence
        if policy_data.get("refund_percentage", 0) == 100:
            base_score += 0.10
        elif policy_data.get("refund_percentage", 0) == 0:
            base_score -= 0.10
    
    # Ensure score stays in valid range
    confidence = max(0.0, min(1.0, base_score))
    
    return confidence

# ============================================
# DETERMINE NEXT ACTION
# ============================================

def determine_action(confidence_score):
    """
    Determine what to do based on confidence score.
    
    Thresholds:
    - >= 0.85: AUTO_EXECUTE (approve/reject based on evidence)
    - 0.75-0.85: FLAG_FOR_REVIEW (flag for human review)
    - < 0.75: ESCALATE (send to specialist)
    
    Args:
        confidence_score (float): Confidence (0.0 to 1.0)
    
    Returns:
        dict: {
            "action": "AUTO_EXECUTE" | "FLAG_FOR_REVIEW" | "ESCALATE",
            "confidence": confidence_score,
            "human_review_needed": bool,
            "escalation_team": "Specialist Dispute Team" or "None"
        }
    """
    
    thresholds = CONFIDENCE_THRESHOLDS
    
    if confidence_score >= thresholds["auto_approve"]:
        action = "AUTO_EXECUTE"
        human_review = False
        escalation_team = None
    elif confidence_score >= thresholds["flag_for_review"]:
        action = "FLAG_FOR_REVIEW"
        human_review = True
        escalation_team = "Review Queue"
    else:
        action = "ESCALATE"
        human_review = True
        escalation_team = "Specialist Dispute Team"
    
    return {
        "action": action,
        "confidence": confidence_score,
        "human_review_needed": human_review,
        "escalation_team": escalation_team,
        "threshold_auto_approve": thresholds["auto_approve"],
        "threshold_flag": thresholds["flag_for_review"]
    }

# ============================================
# ESTIMATE RESOLUTION
# ============================================

def estimate_resolution_time(dispute_type, policy_match, complexity_factors):
    """
    Estimate resolution time based on type and complexity.
    
    Args:
        dispute_type (str): UNAUTHORIZED, DUPLICATE, etc.
        policy_match (dict): Matched policy
        complexity_factors (dict): {has_merchant_response, has_full_evidence, ...}
    
    Returns:
        dict: {
            "estimated_days": int,
            "best_case_days": int,
            "worst_case_days": int,
            "factors": [list of factors affecting timeline]
        }
    """
    
    base_days = {
        "UNAUTHORIZED": 7,
        "DUPLICATE": 5,
        "AMOUNT_MISMATCH": 15,
        "NO_SERVICE": 20,
        "DEFECTIVE": 14,
        "CANCELLED": 15,
        "UNDELIVERED": 15,
        "MERCHANT_ERROR": 10,
        "OTHERS": 20
    }
    
    estimated = base_days.get(dispute_type, 20)
    factors = []
    
    # Adjust based on complexity
    if complexity_factors.get("has_full_evidence"):
        estimated -= 3
        factors.append("Full evidence provided (faster)")
    else:
        factors.append("Incomplete evidence (slower)")
    
    if complexity_factors.get("has_merchant_response"):
        estimated -= 5
        factors.append("Merchant already responded (faster)")
    else:
        estimated += 3
        factors.append("Awaiting merchant response (slower)")
    
    if complexity_factors.get("involves_international"):
        estimated += 5
        factors.append("International transaction (slower)")
    
    if complexity_factors.get("high_risk_customer"):
        estimated += 3
        factors.append("High-risk customer (requires extra review)")
    
    if complexity_factors.get("multiple_disputes"):
        estimated += 2
        factors.append("Customer has multiple disputes (pattern review)")
    
    # Bounds
    best_case = max(1, estimated - 5)
    worst_case = estimated + 10
    
    return {
        "estimated_days": estimated,
        "best_case_days": best_case,
        "worst_case_days": worst_case,
        "factors": factors,
        "dispute_type": dispute_type
    }

# ============================================
# BUILD DECISION SUMMARY
# ============================================

def build_decision_summary(
    case_id,
    dispute_type,
    customer_claim,
    evidence,
    analysis,
    gemini_decision,
    confidence_score,
    policy_info
):
    """
    Build complete decision summary for case.
    
    Returns:
        dict: Complete case decision record
    """
    
    action = determine_action(confidence_score)
    
    # Determine refund amount
    refund_amount = 0.0
    if gemini_decision and "data" in gemini_decision:
        refund_amount = gemini_decision["data"].get("refund_amount", 0.0)
    
    # Build summary
    summary = {
        "case_id": case_id,
        "dispute_type": dispute_type,
        "customer_claim": customer_claim,
        "confidence_score": round(confidence_score, 3),
        "action": action["action"],
        "human_review_needed": action["human_review_needed"],
        "escalation_team": action["escalation_team"],
        "refund_amount": refund_amount,
        "decision": gemini_decision["data"].get("decision", "UNKNOWN") if gemini_decision and "data" in gemini_decision else "UNKNOWN",
        "reasoning": gemini_decision["data"].get("reasoning", "") if gemini_decision and "data" in gemini_decision else "",
        "risk_flags": gemini_decision["data"].get("risk_flags", []) if gemini_decision and "data" in gemini_decision else [],
        "evidence_summary": {
            "customer_profile_found": "customer_profile" in evidence and evidence["customer_profile"].get("status") == "success",
            "transaction_found": "transaction_search" in evidence and evidence["transaction_search"].get("status") == "success",
            "fraud_check_done": "fraud_detection" in evidence and evidence["fraud_detection"].get("status") == "success",
            "risk_assessment_done": "risk_scoring" in evidence and evidence["risk_scoring"].get("status") == "success"
        },
        "policy_info": policy_info
    }
    
    return summary

# ============================================
# ESCALATION CRITERIA
# ============================================

def check_escalation_criteria(evidence, confidence, customer_risk, fraud_risk):
    """
    Check if case should be escalated regardless of confidence.
    Some cases MUST go to human even if confidence is high.
    
    Returns:
        dict: {
            "should_escalate": bool,
            "reason": "...",
            "escalation_priority": "HIGH" | "MEDIUM" | "LOW"
        }
    """
    
    escalation_reasons = []
    priority = "MEDIUM"
    
    # High fraud risk always escalate
    if fraud_risk and fraud_risk > 0.8:
        escalation_reasons.append("High fraud risk detected")
        priority = "HIGH"
    
    # High customer risk escalate with high priority
    if customer_risk and customer_risk > 0.85:
        escalation_reasons.append("Customer risk profile exceeds safe threshold")
        priority = "HIGH"
    
    # Very high refund amounts escalate
    if evidence.get("transaction_search") and "data" in evidence["transaction_search"]:
        tx_data = evidence["transaction_search"]["data"]
        if isinstance(tx_data, dict) and tx_data.get("amount", 0) > 100000:
            escalation_reasons.append("Very high transaction amount (>100K)")
            priority = "HIGH"
    
    # Missing critical evidence escalate
    missing_critical = False
    if not evidence.get("customer_profile") or evidence["customer_profile"].get("status") != "success":
        escalation_reasons.append("Customer profile not found")
        missing_critical = True
    if not evidence.get("transaction_search") or evidence["transaction_search"].get("status") != "success":
        escalation_reasons.append("Disputed transaction not found")
        missing_critical = True
    
    if missing_critical:
        priority = "HIGH"
    
    should_escalate = len(escalation_reasons) > 0
    
    return {
        "should_escalate": should_escalate,
        "reasons": escalation_reasons,
        "escalation_priority": priority if should_escalate else "NONE"
    }
