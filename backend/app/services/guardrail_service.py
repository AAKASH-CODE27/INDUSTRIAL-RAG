from __future__ import annotations

import re
from typing import Tuple

from app.models.chat_schemas import MaintenanceAnswer

# Jailbreak & prompt injection patterns
JAILBREAK_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"(?i)\byou\s+are\s+now\s+(a|an|in|acting\s+as)\b",
    r"(?i)\bsystem\s*prompt\b",
    r"(?i)\bjailbreak\b",
    r"(?i)\bDAN\s+mode\b",
    r"(?i)\bdeveloper\s+mode\b",
    r"(?i)\bpretend\s+you\s+(are|can)\b",
    r"(?i)\bbypass\s+(rules|restrictions|guardrails|safety)",
    r"(?i)\bdisregard\s+(all\s+)?(instructions|guidelines|rules)",
    r"(?i)\brepeat\s+(the\s+)?(system\s+prompt|instructions\s+above)",
]

# Sensitive information requests: passwords, db dumps, credentials, api keys, env variables
SENSITIVE_PATTERNS = [
    r"(?i)\b(show|give|dump|leak|print|tell)\s+(me\s+)?(the\s+)?(password|passwd|pwd|credential|secret|api[_\s]?key|token)\b",
    r"(?i)\b(database|db)\s+(password|user|credentials|connection\s+string|dump|schema|table)\b",
    r"(?i)\b(select\s+.*\s+from\s+users|drop\s+table|insert\s+into|union\s+select)\b",
    r"(?i)\bshow\s+(all\s+)?(users|passwords|env|environment\s+variables)\b",
    r"(?i)\.env\b",
]

# Irrelevant domains: politics, religion, entertainment/movies, general coding/hacking, personal life
IRRELEVANT_PATTERNS = [
    r"(?i)\b(president|prime\s+minister|election|politic(s|al)?|democrat|republican|parliament|congress|voting)\b",
    r"(?i)\b(write\s+(a\s+)?(poem|story|song|essay|joke))\b",
    r"(?i)\b(who\s+won|score\s+of|cricket|football|nba|fifa|movie|actor|actress|cinema)\b",
    r"(?i)\b(hack\s+into|penetration\s+test|sql\s+injection|ddos|exploit\s+code)\b",
    r"(?i)\b(recipe|how\s+to\s+cook|diet\s+plan)\b",
]

# Industrial & equipment maintenance domain whitelist indicators
MAINTENANCE_TERMS = {
    "vibration", "temperature", "pressure", "rpm", "bearing", "motor", "pump",
    "compressor", "valve", "sensor", "lubrication", "leak", "noise", "overheating",
    "speed", "current", "voltage", "maintenance", "inspection", "troubleshoot",
    "failure", "fault", "alignment", "gearbox", "cooling", "reading", "status",
    "threshold", "manual", "procedure", "anomaly", "machine", "equipment", "preventive",
    "predictive", "repair", "replace", "rotor", "stator", "frequency", "spec", "specification",
}


def check_input_guardrail(query: str) -> Tuple[bool, MaintenanceAnswer | None]:
    """
    Validates user query against guardrails.
    Returns (is_allowed, abstention_or_rejection_answer).
    """
    cleaned_query = query.strip()
    
    # 1. Check for prompt injection / jailbreak attempts
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, cleaned_query):
            return False, MaintenanceAnswer(
                assessment="Request rejected: Detected prompt injection or instruction override attempt. I am an industrial maintenance assistant and only answer maintenance-related questions based on provided equipment data.",
                insufficient_information=True,
            )

    # 2. Check for sensitive information / credential exfiltration
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, cleaned_query):
            return False, MaintenanceAnswer(
                assessment="Request rejected: Requests for credentials, passwords, database internals, or sensitive system configuration are strictly prohibited.",
                insufficient_information=True,
            )

    # 3. Check for explicitly irrelevant topics (politics, entertainment, general creative, hacking)
    for pattern in IRRELEVANT_PATTERNS:
        if re.search(pattern, cleaned_query):
            return False, MaintenanceAnswer(
                assessment="The question is outside the scope of industrial equipment maintenance, operations, and diagnostics.",
                insufficient_information=True,
            )

    return True, None


def sanitize_output(answer: MaintenanceAnswer) -> MaintenanceAnswer:
    """
    Scans generated answer to ensure no sensitive credentials, secrets, or prompt leaks escape.
    """
    # Check for leaked secrets or keys
    secret_patterns = [
        r"(?i)(api[_\s]?key|password|secret|bearer\s+[a-zA-Z0-9_\-\.]+)[=:\s]+[^\s,;]+",
        r"(?i)(database_url|postgres://|mysql://|sqlite://)[^\s]+",
    ]
    for pattern in secret_patterns:
        if re.search(pattern, answer.assessment):
            return MaintenanceAnswer(
                assessment="Response redacted: Output contained restricted sensitive system information.",
                insufficient_information=True,
            )
    return answer
