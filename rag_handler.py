# ============================================
# RAG HANDLER (Retrieval-Augmented Generation)
# ============================================
# Retrieves policies using sentence embeddings + cosine similarity
# Uses local embeddings (sentence-transformers) - no external API calls

import json
import sys
from pathlib import Path
import pickle
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from config import POLICIES_FILE, EMBEDDINGS_FILE, DATABASE_PATH

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    print("Error: sentence-transformers not installed.")
    print("Run: pip install sentence-transformers")
    sys.exit(1)

# ============================================
# INITIALIZE EMBEDDINGS MODEL
# ============================================

# Load the embedding model (all-MiniLM-L6-v2 is small & fast)
print("Loading embeddings model (all-MiniLM-L6-v2)...")
embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Embeddings model loaded.")

# ============================================
# LOAD POLICIES
# ============================================

def load_policies():
    """
    Load policies from JSON file.
    Returns: dict of {policy_id: policy_content}
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        policies_path = db_path.parent / POLICIES_FILE
        
        if not policies_path.exists():
            # Return default policies if file doesn't exist
            return get_default_policies()
        
        with open(policies_path, 'r', encoding='utf-8') as f:
            policies = json.load(f)
        
        return policies
    except Exception as e:
        print(f"Error loading policies: {e}")
        return get_default_policies()

def get_default_policies():
    """
    Default policies (embedded in code as fallback).
    """
    return {
        "POL_UNAUTH_001": {
            "id": "POL_UNAUTH_001",
            "category": "UNAUTHORIZED",
            "title": "Unauthorized Transaction Protection",
            "content": """
Customer Protection for Unauthorized Transactions:
- Customers have 60 days to report unauthorized transactions
- Banks must investigate within 10 business days
- If unauthorized confirmed: Full refund within 5-7 business days
- No customer liability for unauthorized transactions over INR 5,000 if reported within 30 days
- Customer must not have shared PIN or password
""",
            "refund_percentage": 100,
            "investigation_days": 10,
            "resolution_days": 7
        },
        "POL_DUP_001": {
            "id": "POL_DUP_001",
            "category": "DUPLICATE",
            "title": "Duplicate Charge Resolution",
            "content": """
Duplicate Charge Policy:
- Duplicate charges are processed as billing errors
- Immediate reversal upon verification (no investigation needed)
- Refund issued within 3-5 business days
- Evidence needed: Transaction receipt + merchant confirmation
- Priority: HIGH (same-day review)
""",
            "refund_percentage": 100,
            "investigation_days": 3,
            "resolution_days": 5
        },
        "POL_AMT_001": {
            "id": "POL_AMT_001",
            "category": "AMOUNT_MISMATCH",
            "title": "Amount Discrepancy Resolution",
            "content": """
Amount Mismatch / Billing Discrepancy:
- Refund = (Charged Amount - Agreed Amount)
- Merchant must confirm authorized amount within 7 days
- If merchant non-responsive: Refund issued as credit
- Customer provides: Receipt showing agreed amount + proof of dispute
- Investigation period: 10-15 business days
""",
            "refund_percentage": 100,
            "investigation_days": 15,
            "resolution_days": 15
        },
        "POL_SVC_001": {
            "id": "POL_SVC_001",
            "category": "NO_SERVICE",
            "title": "Service Not Rendered / Delivered",
            "content": """
No Service / Service Not Delivered:
- Customer has 30 days to report from service date
- Must provide: Contract/order confirmation + proof service was not rendered
- Merchant investigation: 7-10 days
- If service still not available: Full refund
- Resolution: 15-20 business days
- Priority: MEDIUM
""",
            "refund_percentage": 100,
            "investigation_days": 20,
            "resolution_days": 20
        },
        "POL_DEF_001": {
            "id": "POL_DEF_001",
            "category": "DEFECTIVE",
            "title": "Defective Product or Quality Issues",
            "content": """
Defective Product Claim:
- Customer must report within 14 days of delivery
- Evidence required: Photos of defect + delivery proof
- Options: Repair, replacement, or refund
- Merchant has 7 days to respond
- If unresponsive: Full refund approved
- Resolution: 7-14 business days
""",
            "refund_percentage": 100,
            "investigation_days": 14,
            "resolution_days": 14
        },
        "POL_CAN_001": {
            "id": "POL_CAN_001",
            "category": "CANCELLED",
            "title": "Cancelled Service / Transaction Reversal",
            "content": """
Cancelled Service Reversal:
- Customer must provide: Cancellation confirmation from merchant
- If no confirmation: Merchant verification required (5 days)
- Refund processing: 5-7 business days after confirmation
- Partial refunds: Based on merchant's cancellation policy
- Total resolution: 10-15 business days
""",
            "refund_percentage": 100,
            "investigation_days": 15,
            "resolution_days": 15
        },
        "POL_UND_001": {
            "id": "POL_UND_001",
            "category": "UNDELIVERED",
            "title": "Undelivered Item or Order",
            "content": """
Undelivered Item / Failed Delivery:
- Customer must report within 30 days of expected delivery
- Evidence: Tracking info showing non-delivery
- Options: Re-delivery or refund
- Merchant investigation: 7-10 days
- If re-delivery refused: Full refund approved
- Resolution: 10-15 business days
""",
            "refund_percentage": 100,
            "investigation_days": 15,
            "resolution_days": 15
        },
        "POL_MER_001": {
            "id": "POL_MER_001",
            "category": "MERCHANT_ERROR",
            "title": "Merchant Billing Error / Processing Mistake",
            "content": """
Merchant Error / Billing Mistake:
- Examples: Wrong amount charged, duplicate entry, wrong card used
- Merchant must acknowledge error within 5 days
- Refund issued upon merchant confirmation
- If merchant denies: Investigation and evidence review
- Resolution: 7-10 business days if acknowledged, 15-20 if disputed
""",
            "refund_percentage": 100,
            "investigation_days": 20,
            "resolution_days": 20
        },
        "POL_OTH_001": {
            "id": "POL_OTH_001",
            "category": "OTHERS",
            "title": "Other Disputes / General Cases",
            "content": """
Other Dispute Types - Case-by-Case Review:
- Not covered by standard categories
- Full investigation with all evidence review
- Customer must provide: Detailed explanation + supporting docs
- Merchant verification: Mandatory
- Investigation period: 15-20 business days
- Decision: Based on merit and available evidence
- Escalation: To dispute specialist if complex
""",
            "refund_percentage": 0,  # Varies by case
            "investigation_days": 20,
            "resolution_days": 20
        }
    }

# ============================================
# CREATE & SAVE EMBEDDINGS
# ============================================

def create_and_save_embeddings(policies):
    """
    Create embeddings for all policies and save to file.
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        embeddings_path = db_path.parent / EMBEDDINGS_FILE
        
        embeddings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create embeddings for each policy
        embeddings_data = {}
        
        for policy_id, policy in policies.items():
            content = policy.get("content", "")
            
            # Generate embedding
            embedding = embeddings_model.encode(content, convert_to_tensor=False)
            
            embeddings_data[policy_id] = {
                "policy_id": policy_id,
                "category": policy.get("category", ""),
                "title": policy.get("title", ""),
                "embedding": embedding.tolist()  # Convert to list for JSON serialization
            }
        
        # Save embeddings
        with open(embeddings_path, 'wb') as f:
            pickle.dump(embeddings_data, f)
        
        print(f"Embeddings created and saved: {len(embeddings_data)} policies")
        return embeddings_data
    
    except Exception as e:
        print(f"Error creating embeddings: {e}")
        return None

# ============================================
# LOAD EMBEDDINGS
# ============================================

def load_embeddings():
    """
    Load pre-computed embeddings from file.
    If not found, create new ones.
    """
    try:
        # Path from src/ up to project root, then to data/
        db_path = Path(__file__).parent.parent / DATABASE_PATH
        embeddings_path = db_path.parent / EMBEDDINGS_FILE
        
        if embeddings_path.exists():
            with open(embeddings_path, 'rb') as f:
                embeddings_data = pickle.load(f)
            return embeddings_data
        else:
            # Create new embeddings
            policies = load_policies()
            return create_and_save_embeddings(policies)
    
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        return None

# ============================================
# SEARCH POLICIES (RAG CORE)
# ============================================

def search_policies(query, top_k=3):
    """
    Search policies using semantic similarity.
    
    Args:
        query (str): Customer's question or dispute description
        top_k (int): Number of most relevant policies to return
    
    Returns:
        dict: {
            "status": "success" or "error",
            "results": [
                {"policy_id": "...", "title": "...", "content": "...", "score": 0.0-1.0},
                ...
            ]
        }
    """
    try:
        # Load policies and embeddings
        policies = load_policies()
        embeddings_data = load_embeddings()
        
        if not embeddings_data:
            return {
                "status": "error",
                "message": "Embeddings not available",
                "results": []
            }
        
        # Generate embedding for query
        query_embedding = embeddings_model.encode(query, convert_to_tensor=False)
        
        # Calculate similarity scores
        similarities = {}
        
        for policy_id, emb_data in embeddings_data.items():
            policy_embedding = np.array(emb_data["embedding"])
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, policy_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(policy_embedding)
            )
            
            similarities[policy_id] = similarity
        
        # Sort by similarity and get top_k
        sorted_policies = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        top_policies = sorted_policies[:top_k]
        
        # Build results
        results = []
        for policy_id, score in top_policies:
            policy = policies.get(policy_id, {})
            results.append({
                "policy_id": policy_id,
                "category": policy.get("category", ""),
                "title": policy.get("title", ""),
                "content": policy.get("content", ""),
                "refund_percentage": policy.get("refund_percentage", 0),
                "resolution_days": policy.get("resolution_days", 0),
                "relevance_score": float(score)
            })
        
        return {
            "status": "success",
            "message": f"Found {len(results)} relevant policies",
            "results": results,
            "query": query
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "results": []
        }

# ============================================
# GET POLICY BY CATEGORY
# ============================================

def get_policy_by_category(category):
    """
    Get policy for a specific dispute category.
    
    Args:
        category (str): Dispute category (UNAUTHORIZED, DUPLICATE, etc.)
    
    Returns:
        dict: Policy details or None if not found
    """
    try:
        policies = load_policies()
        
        for policy_id, policy in policies.items():
            if policy.get("category") == category:
                return policy
        
        return None
    
    except Exception as e:
        print(f"Error getting policy: {e}")
        return None

# ============================================
# INITIALIZE ON IMPORT
# ============================================

if __name__ == "__main__":
    print("RAG Handler Initialization Test")
    print("=" * 50)
    
    # Load policies
    policies = load_policies()
    print(f"Loaded {len(policies)} policies")
    
    # Create embeddings
    embeddings = load_embeddings()
    print(f"Loaded {len(embeddings) if embeddings else 0} embeddings")
    
    # Test search
    test_query = "I was charged twice for the same item"
    results = search_policies(test_query, top_k=3)
    
    print(f"\nSearch test: '{test_query}'")
    print(f"Results: {len(results['results'])} policies found")
    
    for result in results['results']:
        print(f"  - {result['title']} (Score: {result['relevance_score']:.3f})")
