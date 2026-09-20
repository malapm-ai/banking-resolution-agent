# ============================================
# GEMINI API HANDLER V2 (IMPROVED)
# ============================================
# Higher token limits + graceful truncation handling

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from config import GEMINI_API_KEY, GEMINI_MODEL, TEMPERATURES

import google.genai as genai

client = genai.Client(api_key=GEMINI_API_KEY)

# ============================================
# INCREASED TOKEN LIMITS FOR EACH STEP
# ============================================

TOKEN_LIMITS = {
    "understand": 800,      # Increased from 500
    "plan": 1200,           # Increased from 800
    "analyze": 1500,        # Increased from 800
    "decide": 1000,         # Increased from 500
    "communicate": 500      # Same
}

def call_gemini_with_retry(prompt, step_name="communicate", max_tokens=None, max_retries=5):
    """
    Call Gemini API with longer backoff for 503 errors.
    Uses higher token limits to prevent truncation.
    
    Args:
        prompt (str): The prompt to send to Gemini
        step_name (str): Step name (understand, plan, analyze, decide, communicate)
        max_tokens (int): Override token limit (optional)
        max_retries (int): Number of retries on 503 error
    
    Returns:
        dict: {"status": "success"/"error", "response": text, ...}
    """
    # Use step-specific limits, or provided limit, or default
    if max_tokens is None:
        max_tokens = TOKEN_LIMITS.get(step_name, 1000)
    
    temperature = TEMPERATURES.get(step_name, 0.5)
    model = GEMINI_MODEL
    
    for attempt in range(max_retries):
        try:
            # Use Chat API (Google recommended)
            chat = client.chats.create(model=model)
            response = chat.send_message(
                prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=temperature,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=max_tokens,
                )
            )
            
            # Extract response text
            if response.text:
                response_text = response.text
            else:
                return {
                    "status": "error",
                    "response": f"Empty response (finish_reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'})",
                    "tokens_used": 0,
                    "model": model,
                    "temperature": temperature,
                    "step": step_name,
                    "error_message": "Empty API response"
                }
            
            # Check if response appears truncated
            is_truncated = response_text.endswith("$") or response_text.count("{") > response_text.count("}")
            if is_truncated:
                print(f"  ⚠️  Response appears truncated. Retrying with higher token limit...")
                higher_tokens = max_tokens + 500
                max_tokens = higher_tokens
                continue
            
            tokens_used = len(prompt) // 4 + len(response_text) // 4
            
            return {
                "status": "success",
                "response": response_text,
                "tokens_used": tokens_used,
                "model": model,
                "temperature": temperature,
                "step": step_name
            }
        
        except Exception as e:
            error_str = str(e)
            is_503 = ("503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str)
            
            if is_503 and attempt < max_retries - 1:
                wait_time = 5 * (2 ** attempt)
                if wait_time > 60:
                    wait_time = 60
                print(f"  ⚠️  API overloaded (503). Waiting {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                return {
                    "status": "error",
                    "response": error_str,
                    "tokens_used": 0,
                    "model": model,
                    "temperature": temperature,
                    "step": step_name,
                    "error_message": error_str
                }
    
    return {
        "status": "error",
        "response": "API unavailable after retries",
        "tokens_used": 0,
        "model": model,
        "temperature": temperature,
        "step": step_name,
        "error_message": "Max retries exceeded"
    }

def call_gemini(prompt, step_name="communicate", max_tokens=None):
    """Backward compatible wrapper."""
    return call_gemini_with_retry(prompt, step_name, max_tokens, max_retries=5)

# ============================================
# STEP FUNCTIONS (Same as before)
# ============================================

def understand(account_number, dispute_type, customer_claim):
    """UNDERSTAND step: Extract key facts from customer's dispute."""
    prompt = f"""You are a banking dispute analyst. Extract the following from the customer's claim:
1. Core issue (1-2 sentences)
2. Amount disputed
3. Key dates
4. Customer impact
5. Supporting evidence mentioned

Dispute Type: {dispute_type}
Customer Claim: {customer_claim}

Respond in JSON format:
{{
    "core_issue": "...",
    "amount": "...",
    "dates": {{"when_occurred": "...", "when_discovered": "..."}},
    "customer_impact": "...",
    "evidence": ["...", "..."],
    "clarity_score": 0.0-1.0
}}
"""
    return call_gemini_with_retry(prompt, step_name="understand", max_tokens=TOKEN_LIMITS["understand"])

def plan(dispute_type, core_issue, customer_risk):
    """PLAN step: Decide which tools to call."""
    prompt = f"""You are a banking dispute resolution planner. Given this case, plan the investigation.

Dispute Type: {dispute_type}
Core Issue: {core_issue}
Customer Risk Level: {customer_risk}

Plan the investigation. Respond in JSON:
{{
    "tools_to_call": [
        {{"tool": "tool_name", "params": "...", "reason": "..."}}
    ],
    "investigation_steps": ["step1", "step2"],
    "expected_resolution_time": "X business days"
}}
"""
    return call_gemini_with_retry(prompt, step_name="plan", max_tokens=TOKEN_LIMITS["plan"])

def analyze(dispute_type, tool_results):
    """ANALYZE step: Review tool outputs and build evidence case."""
    prompt = f"""You are a banking dispute investigator. Analyze the evidence collected.

Dispute Type: {dispute_type}
Tool Results:
{json.dumps(tool_results, indent=2)[:1000]}

Analyze and respond in JSON:
{{
    "findings": "...",
    "supporting_evidence": [...],
    "contradicting_evidence": [...],
    "missing_info": [...],
    "preliminary_assessment": "LIKELY_VALID" or "LIKELY_INVALID" or "UNCLEAR",
    "confidence_level": 0.0-1.0
}}
"""
    return call_gemini_with_retry(prompt, step_name="analyze", max_tokens=TOKEN_LIMITS["analyze"])

def decide(dispute_type, analysis, policies):
    """DECIDE step: Make final decision with confidence score."""
    prompt = f"""You are the final arbiter in banking disputes. Make a decision.

Dispute Type: {dispute_type}
Analysis:
{json.dumps(analysis, indent=2)[:800]}

Respond in JSON:
{{
    "decision": "APPROVE" or "REJECT" or "INVESTIGATE_FURTHER",
    "refund_amount": 0.0,
    "reasoning": "...",
    "confidence_score": 0.0-1.0,
    "risk_flags": [...],
    "next_steps": "..."
}}
"""
    return call_gemini_with_retry(prompt, step_name="decide", max_tokens=TOKEN_LIMITS["decide"])

def communicate(decision, reasoning, customer_name):
    """COMMUNICATE step: Generate empathetic customer message."""
    prompt = f"""You are a customer service specialist. Write an empathetic message.

Decision: {decision}
Reasoning: {reasoning}
Customer Name: {customer_name}

Respond in JSON:
{{
    "message": "...",
    "tone": "empathetic" or "neutral" or "apologetic",
    "action_items": ["...", "..."]
}}
"""
    return call_gemini_with_retry(prompt, step_name="communicate", max_tokens=TOKEN_LIMITS["communicate"])

# ============================================
# HELPER: EXTRACT JSON FROM RESPONSE
# ============================================

def extract_json_from_response(response_text):
    """Try to extract JSON from response. Handle truncated JSON gracefully."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If truncated, try to fix it
                if json_str.endswith("\"") or json_str.endswith(","):
                    json_str += "}"
                    try:
                        return json.loads(json_str)
                    except:
                        return {"raw_response": response_text, "truncated": True}
                return {"raw_response": response_text, "truncated": True}
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
            try:
                return json.loads(json_str)
            except:
                return {"raw_response": response_text, "truncated": True}
        else:
            return {"raw_response": response_text}
