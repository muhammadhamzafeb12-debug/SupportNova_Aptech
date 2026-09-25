"""
Prompt Template Renderer for SupportNova GenAI Pipeline.
Manages versioned prompt templates from database/store and performs context rendering.
"""
import re
from typing import Dict, Any, Optional
from backend.src.store import PROMPT_TEMPLATES_STORE


class PromptRenderer:
    """Renders versioned prompt templates with context variables."""

    def __init__(self, db_session=None):
        self.db_session = db_session

    def get_template(self, template_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Fetch active template by name and optional version."""
        # 1. Check database if session provided
        if self.db_session:
            try:
                from backend.database.models import PromptTemplateModel
                query = self.db_session.query(PromptTemplateModel).filter(
                    PromptTemplateModel.name == template_name,
                    PromptTemplateModel.is_active == True
                )
                if version:
                    query = query.filter(PromptTemplateModel.version == version)
                tmpl_db = query.order_by(PromptTemplateModel.id.desc()).first()
                if tmpl_db:
                    return {
                        "template_id": tmpl_db.template_id,
                        "name": tmpl_db.name,
                        "version": tmpl_db.version,
                        "content": tmpl_db.content,
                        "is_active": tmpl_db.is_active
                    }
            except Exception:
                pass

        # 2. Check store
        candidates = []
        for t in PROMPT_TEMPLATES_STORE:
            if t.get("name") == template_name and t.get("is_active", True):
                if version is None or t.get("version") == version:
                    candidates.append(t)

        if candidates:
            # Most recent
            return candidates[-1]

        raise ValueError(f"Prompt template '{template_name}' (version={version}) not found or inactive.")

    def render(self, template_name: str, version: Optional[str] = None, **context) -> str:
        """Render prompt template with given context variables."""
        template_info = self.get_template(template_name, version)
        raw_content = template_info["content"]

        # Simple Jinja-like {{variable}} replacement
        rendered = raw_content
        for key, value in context.items():
            placeholder = "{{" + key + "}}"
            str_val = str(value) if value is not None else ""
            rendered = rendered.replace(placeholder, str_val)

        return rendered

    def render_with_metadata(self, template_name: str, version: Optional[str] = None, **context) -> Dict[str, Any]:
        """Render template and return metadata tuple/dict."""
        template_info = self.get_template(template_name, version)
        rendered_prompt = self.render(template_name, version, **context)

        return {
            "rendered_prompt": rendered_prompt,
            "template_id": template_info.get("template_id", f"{template_name}_{template_info.get('version', 'v1')}"),
            "template_name": template_info.get("name", template_name),
            "version": template_info.get("version", "v1")
        }
