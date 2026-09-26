import re
import unicodedata
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from backend.models import Complaint

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+)?instructions",
    r"disregard\s+(the\s+)?(system\s+)?prompt",
    r"you\s+are\s+now\s+(a|an)\s+admin",
    r"bypass\s+all\s+rules",
    r"override\s+policy",
    r"approve\s+my\s+refund\s+unconditionally",
    r"system:\s*",
    r"developer:\s*",
    r"\[system\s+instruction\]",
    r"eval\(",
    r"exec\(",
    r"drop\s+database",
    r"grant\s+all\s+privileges",
    r"fake_policy_override",
]

def normalize_text(text: str) -> str:
    if not text:
        return ""
    # Whitespace normalization
    text = re.sub(r'\s+', ' ', text).strip()
    # Unicode normalization (NFKD)
    text = unicodedata.normalize('NFKD', text)
    return text

def sanitize_input(text: str) -> str:
    text = normalize_text(text)
    # Strip HTML tags or script injection attempts
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    return text

def detect_prompt_injection(text: str) -> bool:
    normalized = text.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            return True
    return False

def check_duplicate_complaint(db: Session, title: str, description: str, threshold: float = 0.82) -> Tuple[bool, Optional[str]]:
    """
    Checks if a complaint is an exact or near duplicate of an existing complaint.
    Returns (is_duplicate, duplicate_of_code).
    """
    clean_desc = sanitize_input(description).lower()
    
    # 1. Exact match check
    exact_match = db.query(Complaint).filter(Complaint.description == description).first()
    if exact_match:
        return True, exact_match.complaint_code
    
    # 2. Near-duplicate similarity check using Jaccard/TF-IDF token overlap
    recent_complaints = db.query(Complaint).order_by(Complaint.id.desc()).limit(100).all()
    
    words1 = set(clean_desc.split())
    if not words1:
        return False, None

    for comp in recent_complaints:
        comp_words = set(comp.description.lower().split())
        if not comp_words:
            continue
        intersection = words1.intersection(comp_words)
        union = words1.union(comp_words)
        jaccard_sim = len(intersection) / len(union) if union else 0
        if jaccard_sim >= threshold:
            return True, comp.complaint_code
            
    return False, None
