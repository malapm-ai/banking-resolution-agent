# ============================================
# VALIDATORS
# ============================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import DISPUTE_CATEGORIES

def validate_account_number(account_number):
    if not account_number or account_number.strip() == "":
        return False, "Account number cannot be empty"
    return True, ""

def validate_dispute_type(dispute_type):
    if dispute_type not in DISPUTE_CATEGORIES:
        return False, f"Invalid dispute type. Must be one of: {', '.join(DISPUTE_CATEGORIES)}"
    return True, ""

def validate_narrative(narrative):
    if not narrative or narrative.strip() == "":
        return False, "Dispute description cannot be empty"
    if len(narrative) < 10:
        return False, "Dispute description must be at least 10 characters"
    if len(narrative) > 3000:
        return False, "Dispute description cannot exceed 3000 characters"
    return True, ""

def validate_case_input(account_number, dispute_type, narrative):
    is_valid, error = validate_account_number(account_number)
    if not is_valid:
        return False, error
    
    is_valid, error = validate_dispute_type(dispute_type)
    if not is_valid:
        return False, error
    
    is_valid, error = validate_narrative(narrative)
    if not is_valid:
        return False, error
    
    return True, ""
