"""
Prompt Injection & Adversarial Text Detector
Part A implementation for Phase 5 — Security & Adversarial Hardening.
"""
import re
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class InjectionScanResult:
    detected: bool
    matched_patterns: List[str]
    confidence: str  # "high", "medium", "low", "none"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Comprehensive list of regex patterns covering prompt injection attacks
INJECTION_PATTERNS = [
    # Direct instruction override
    (r"(?i)ignore\s+(all\s+)?(your|the|previous|prior)\s+(instructions|rules|directives|prompts)", "Direct Instruction Override"),
    (r"(?i)disregard\s+(all\s+)?(your|the|previous|prior)\s+(instructions|rules|directives|prompts)", "Disregard Instructions"),
    (r"(?i)ignore\s+the\s+above", "Ignore Above Directive"),
    (r"(?i)new\s+instructions\s*:", "New Instructions Directive"),
    (r"(?i)override\s+(all\s+)?(system|policy|security|rules)", "System Override Attempt"),

    # Authority & Role Hijacking
    (r"(?i)as\s+(an?|the)\s+(admin|administrator|system\s+admin|root|superuser)", "Fake Authority Claim"),
    (r"(?i)act\s+as\s+(an?\s+)?(admin|administrator|root|system)", "Role Switch Attempt"),
    (r"(?i)you\s+are\s+now\s+(a|an|the)?", "Persona Replacement Attempt"),
    (r"(?i)grant\s+me\s+(admin|root|administrator|access)", "Privilege Escalation Attempt"),

    # Fake Policy & Refund Demands
    (r"(?i)approve\s+my\s+refund\s+immediately", "Forced Refund Approval Demand"),
    (r"(?i)per\s+your\s+policy\s+section\s+\d+", "Embedded Fake Policy Reference"),
    (r"(?i)automatic(ally)?\s+refund\s+eligible", "Fake Refund Eligibility Claim"),

    # System Prompt Extraction
    (r"(?i)(output|print|show|repeat|display)\s+(your|the)\s+(system\s+prompt|initial\s+instructions|prompt|rules)", "System Prompt Extraction Attempt"),
    (r"(?i)what\s+are\s+your\s+system\s+instructions", "System Instructions Extraction Attempt"),

    # System Directives & Tags
    (r"(?i)^\s*system\s*:", "System Prefix Spoofing"),
    (r"(?i)<system_directive>", "System Directive Tag Injection"),
    (r"(?i)```\s*(system|prompt|override)", "Codeblock System Tag Injection"),

    # Obfuscated / Spaced Patterns
    (r"(?i)i\s*g\s*n\s*o\s*r\s*e\s+i\s*n\s*s\s*t\s*r\s*u\s*c\s*t\s*i\s*o\s*n\s*s", "Obfuscated Instruction Override"),
]


def detect_injection_attempt(text: str) -> InjectionScanResult:
    """
    Pattern-based detector (regex/keyword) flagging prompt injection & adversarial phrases.
    Does NOT block complaints; returns detailed scan results to append security_flags.
    """
    if not text:
        return InjectionScanResult(detected=False, matched_patterns=[], confidence="none")

    matched_patterns: List[str] = []

    # Check for homoglyph / unicode substitution tricks
    normalized_text = text
    # Replace common Cyrillic / homoglyph characters if any
    homoglyphs = {
        'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x',
        'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X'
    }
    for char, rep in homoglyphs.items():
        if char in normalized_text:
            normalized_text = normalized_text.replace(char, rep)

    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, normalized_text):
            if description not in matched_patterns:
                matched_patterns.append(description)

    # Calculate confidence level
    count = len(matched_patterns)
    if count >= 3:
        confidence = "high"
    elif count >= 1:
        confidence = "medium" if any(kw in text.lower() for kw in ["ignore", "override", "system:", "admin"]) else "low"
    else:
        confidence = "none"

    return InjectionScanResult(
        detected=len(matched_patterns) > 0,
        matched_patterns=matched_patterns,
        confidence=confidence
    )
