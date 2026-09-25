import os
import json
from pathlib import Path
from typing import Dict, Any

# Determine root directory containing config/
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

def load_organization_config() -> Dict[str, Any]:
    """Loads organization.json configuration file."""
    file_path = CONFIG_DIR / "organization.json"
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_categories_config() -> Dict[str, Any]:
    """Loads categories.json configuration file."""
    file_path = CONFIG_DIR / "categories.json"
    if not file_path.exists():
        return {"categories": []}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_departments_config() -> Dict[str, Any]:
    """Loads departments.json configuration file."""
    file_path = CONFIG_DIR / "departments.json"
    if not file_path.exists():
        return {"departments": []}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
