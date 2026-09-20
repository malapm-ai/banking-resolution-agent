# ============================================
# BANKING RESOLUTION AGENT - CONFIGURATION FILE
# ============================================

import os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "demo-key")
GEMINI_MODEL = "models/gemini-3.6-flash"

DATABASE_TYPE = "sqlite"
DATABASE_PATH = "data/banking_agent.db"

TEMPERATURES = {
    "understand": 0.2,
    "plan": 0.3,
    "analyze": 0.2,
    "decide": 0.1,
    "communicate": 0.7
}

CONFIDENCE_THRESHOLDS = {
    "auto_approve": 0.85,
    "flag_for_review": 0.75,
    "escalate": 0.0
}

DISPUTE_CATEGORIES = [
    "UNAUTHORIZED",
    "DUPLICATE",
    "AMOUNT_MISMATCH",
    "NO_SERVICE",
    "DEFECTIVE",
    "CANCELLED",
    "UNDELIVERED",
    "MERCHANT_ERROR",
    "OTHERS"
]

CORE_TOOLS = [
    "customer_profile",
    "transaction_search",
    "fraud_detection",
    "risk_scoring",
    "policy_retrieval",
    "rules_engine",
    "audit_logger",
    "notification_service"
]

VERBOSE_LOGGING = True
GEMINI_REQUESTS_PER_MINUTE = 15
MOCK_CUSTOMERS_COUNT = 1000
MOCK_TRANSACTIONS_COUNT = 5000

MOCK_CUSTOMERS_FILE = "data/mock_customers.json"
MOCK_TRANSACTIONS_FILE = "data/mock_transactions.json"
POLICIES_FILE = "data/policies.json"
EMBEDDINGS_FILE = "data/embeddings.pkl"
