#!/usr/bin/env python3
"""
Secret Scanner — SupportNova CI Security Check
Fails the build if hardcoded secrets resembling API keys are found in the codebase.

Patterns detected:
- Anthropic API keys (sk-ant-...)
- AWS Access keys (AKIA...)
- Long base64 strings near words 'key', 'secret', 'token', 'password', 'api_key'
- Generic API key patterns in assignments
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directories and files to skip
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".next", ".pytest_cache", "dist", ".venv", "venv"}
SKIP_EXTENSIONS = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff", ".woff2", ".ttf", ".ico", ".webp", ".lock"}
SKIP_FILES = {"secret_scan.py", "package-lock.json"}

# Secret patterns to detect
SECRET_PATTERNS = [
    # Anthropic API key
    (r'sk-ant-[A-Za-z0-9_\-]{20,}', "Anthropic API Key"),
    # AWS Access Key ID
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
    # AWS Secret Access Key
    (r'(?i)(aws[_\-]?secret|aws[_\-]?access)[\'"\s]*[:=][\'"\s]*[A-Za-z0-9/+]{40,}', "AWS Secret Key"),
    # Generic API key assignment
    (r'(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[=:]\s*["\'][A-Za-z0-9_\-\.]{20,}["\']', "Generic API Key Assignment"),
    # OpenAI key
    (r'sk-[A-Za-z0-9]{40,}', "OpenAI API Key"),
    # Long base64 near secret words
    (r'(?i)(password|passwd|secret|token|key)\s*[=:]\s*["\'][A-Za-z0-9+/=]{32,}["\']', "Potential Hardcoded Secret"),
    # JWT secret in non-test env config
    (r'(?i)JWT_SECRET\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded JWT Secret"),
]

# Patterns for test/example files (allowed to have fake keys, but emit a warning)
EXPECTED_TEST_WARNINGS = {
    "test_fake_secret_scan": True,
}

def scan_file(filepath: Path) -> list:
    """Returns list of (line_number, pattern_name, line_content) for each match found."""
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(content.splitlines(), 1):
            for pattern, name in SECRET_PATTERNS:
                if re.search(pattern, line):
                    findings.append((lineno, name, line.strip()))
    except Exception:
        pass
    return findings


def main():
    all_findings = []

    for fpath in ROOT.rglob("*"):
        if not fpath.is_file():
            continue
        # Skip unwanted dirs
        parts = set(fpath.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        if fpath.suffix.lower() in SKIP_EXTENSIONS:
            continue
        if fpath.name in SKIP_FILES:
            continue
        # Skip the scan script itself
        if fpath.name == "secret_scan.py":
            continue

        findings = scan_file(fpath)
        if findings:
            for lineno, name, line in findings:
                all_findings.append({
                    "file": str(fpath.relative_to(ROOT)),
                    "line": lineno,
                    "pattern": name,
                    "content": line[:120]
                })

    if all_findings:
        print(f"\n{'='*60}")
        print(f"SECRET SCAN FAILED — {len(all_findings)} potential secret(s) found:")
        print(f"{'='*60}")
        for f in all_findings:
            print(f"  [{f['pattern']}] {f['file']}:{f['line']}")
            print(f"    {f['content']}\n")
        print("Remove exposed secrets, use environment variables instead.")
        sys.exit(1)
    else:
        print("✓ Secret scan passed — no hardcoded secrets detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
