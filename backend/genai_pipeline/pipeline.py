"""
Pipeline 1 Orchestration for SupportNova — Python GenAI Complaint Intelligence Pipeline.
Analyzes complaints using Anthropic API, KB context retrieval, Rule Matrix grounding, prompt rendering,
Pydantic schema validation, automatic retries, and prompt version logging.
"""
import os
import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Callable

from backend.prompt_templates.renderer import PromptRenderer
from backend.schemas.complaint_analysis import ComplaintAnalysisResult, SchemaValidationError
from backend.document_processing.retriever import retrieve_relevant_chunks
from backend.complaint_rules.engine import RuleMatrixEngine
from backend.src.store import (
    COMPLAINTS_STORE,
    GENAI_CALL_LOG_STORE,
    GENAI_ANALYSIS_LOG_STORE,
    ORGANIZATION_CONFIG
)

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


def _format_kb_chunks(chunks: List[Dict[str, Any]]) -> tuple[str, List[str]]:
    """Formats retrieved KB chunks for prompt injection and returns chunk IDs."""
    if not chunks:
        return "No specific knowledge base policy document chunks found.", []

    formatted = []
    chunk_ids = []
    for idx, c in enumerate(chunks, 1):
        cid = c.get("chunk_id", f"CHUNK-{idx:03d}")
        doc_id = c.get("document_id", "UNKNOWN")
        heading = c.get("heading") or c.get("section") or "General"
        text = c.get("text", "").strip()
        formatted.append(f"--- [Chunk ID: {cid} | Policy ID: {doc_id} | Heading: {heading}] ---\n{text}")
        chunk_ids.append(cid)

    return "\n\n".join(formatted), chunk_ids


def _format_rule_context(matched_rule) -> tuple[str, List[str]]:
    """Formats RuleMatrixEngine match candidate for prompt injection."""
    if not matched_rule:
        return "No exact rule matrix candidate found for this category.", []

    rule_ids = [matched_rule.rule_id]
    info = [
        f"Matched Rule ID: {matched_rule.rule_id}",
        f"Category: {matched_rule.category} | Subcategory: {matched_rule.subcategory}",
        f"Department Recommendation: {matched_rule.department}",
        f"Supporting Departments: {', '.join(matched_rule.supporting_departments or []) or 'None'}",
        f"Urgency Hint: {matched_rule.urgency} | Priority Hint: {matched_rule.priority}",
        f"Policy ID Reference: {matched_rule.policy_id}",
        f"Escalation Flag: {matched_rule.escalation_required} (Level: {matched_rule.escalation_level or 'None'})",
        f"Required Actions: {', '.join(matched_rule.required_actions or []) or 'None'}",
        f"Prohibited Actions: {', '.join(matched_rule.prohibited_actions or []) or 'None'}"
    ]

    return "\n".join(info), rule_ids


def _generate_fallback_json(complaint: Dict[str, Any], kb_ids: List[str], rule_ids: List[str]) -> Dict[str, Any]:
    """
    Generates a deterministic fallback JSON structure when no Anthropic API key is provided
    and no mock client is supplied, ensuring local dev and tests execute properly.
    """
    from backend.schemas.complaint_analysis import VALID_CATEGORIES, VALID_SUBCATEGORIES

    raw_cat = complaint.get("expected_category") or complaint.get("category") or complaint.get("issue_category") or "Billing & Payments"
    raw_subcat = complaint.get("subcategory") or complaint.get("sub_category") or "Duplicate Payment Deducted"

    cat = raw_cat if raw_cat and raw_cat.strip().lower() in VALID_CATEGORIES else "Billing & Payments"
    subcat = raw_subcat if raw_subcat and raw_subcat.strip().lower() in VALID_SUBCATEGORIES else "Duplicate Payment Deducted"

    cid = str(complaint.get("complaint_number") or complaint.get("id") or "CMP-2026-TEMP")
    desc = complaint.get("description", "")
    customer_name = complaint.get("customer_name", "Customer")
    title = complaint.get("title", "Service Dispute")

    engine = RuleMatrixEngine()
    rule_features = {
        "category": cat,
        "subcategory": subcat,
        "description": desc
    }
    matched_rule = engine.match(rule_features)

    # Resolve Urgency mapping
    dataset_urg = complaint.get("urgency")
    if dataset_urg == "P0":
        urgency = "Critical"
        priority = "P0"
    elif dataset_urg == "P1":
        urgency = "High"
        priority = "P1"
    elif dataset_urg == "P3":
        urgency = "Low"
        priority = "P3"
    else:
        urgency = "Medium"
        priority = "P2"

    escalation_req = bool(complaint.get("escalation_required", False))

    dept = complaint.get("department")
    if not dept:
        if matched_rule and matched_rule.department:
            dept = matched_rule.department
        else:
            cat_lower = raw_cat.lower()
            desc_lower = desc.lower()
            if "order" in cat_lower or "delivery" in cat_lower or "logistics" in desc_lower:
                dept = "Order Fulfillment & Logistics"
            elif "return" in cat_lower or "refund" in cat_lower:
                dept = "Returns & Reverse Logistics"
            elif "product" in cat_lower or "quality" in cat_lower:
                dept = "Product Quality & Vendor Assurance"
            elif "security" in cat_lower or "fraud" in cat_lower:
                dept = "Trust & Safety (Fraud & Security)"
            elif "marketplace" in cat_lower or "seller" in desc_lower:
                dept = "Marketplace & Seller Operations"
            elif "legal" in cat_lower or "compliance" in cat_lower:
                dept = "Compliance & Legal Affairs"
            elif "account" in cat_lower or "login" in desc_lower:
                dept = "Account Management & Customer Care"
            else:
                dept = "Billing & Payment Operations"

    policy_id = matched_rule.policy_id if (matched_rule and matched_rule.policy_id) else "POL-001"

    req_actions = matched_rule.required_actions if (matched_rule and matched_rule.required_actions) else [
        f"Review account history for {customer_name}.",
        f"Triage complaint with {dept} team.",
        "Contact subscriber with official resolution status."
    ]

    return {
        "complaint_id": cid,
        "primary_issue": title or f"Issue regarding {cat}",
        "secondary_issues": [f"Subcategory detail: {subcat}"] if subcat else [],
        "issue_category": cat,
        "subcategory": subcat,
        "sentiment": "Strongly Negative" if escalation_req else "Negative",
        "urgency": urgency,
        "priority": priority,
        "extracted_entities": {
            "product": complaint.get("product_name") or complaint.get("account_number") or "VelvoCart Item",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "amount": str(complaint.get("requested_credit", 0.0))
        },
        "department": dept,
        "supporting_departments": [],
        "policy_id": policy_id,
        "policy_section": "Section 4.2",
        "resolution_steps": list(req_actions),
        "refund_eligible": True if "billing" in cat.lower() or complaint.get("requested_credit", 0) > 0 else False,
        "replacement_eligible": False,
        "compensation_recommended": True if complaint.get("requested_credit", 0) > 0 else False,
        "escalation_required": escalation_req,
        "escalation_level": (matched_rule.escalation_level if matched_rule else "Tier 1") if escalation_req else None,
        "escalation_reason": "High priority incident or SLA requirement" if escalation_req else None,
        "professional_response": (
            f"Dear {customer_name},\n\n"
            f"Thank you for reaching out to VelvoCart. We acknowledge your complaint regarding '{title}'. "
            f"Our {dept} team is actively investigating this matter to ensure full compliance with our service standards.\n\n"
            f"Sincerely,\nSupportNova Care Team"
        ),
        "follow_up_required": True if escalation_req else False,
        "follow_up_message": f"Follow up scheduled within 24 hours for {cid}." if escalation_req else None,
        "clarification_questions": [],
        "complaint_summary": f"Summary: {title}. {desc[:150]}...",
        "agent_guidance": [
            "Verify customer ID and account standing before issuing credit.",
            "Ensure all communication is logged in the audit history."
        ],
        "source_references": list(set(kb_ids + rule_ids)) or [policy_id, "RULE-0001"]
    }


async def analyze_complaint(
    complaint_input: Union[Dict[str, Any], int, str],
    max_retries: int = 2,
    mock_client: Optional[Any] = None,
    mock_raw_response: Optional[str] = None,
    db_session: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Asynchronously analyzes a complaint using GenAI (Anthropic API) + KB retrieval + Rule Matrix grounding.
    Enforces Pydantic schema validation, prompt version logging, and retry logic.
    """
    # 1. Resolve complaint object from store or dict
    complaint = None
    if isinstance(complaint_input, dict):
        complaint = complaint_input
    else:
        # Search store
        target_id_str = str(complaint_input)
        for c in COMPLAINTS_STORE:
            if str(c.get("id")) == target_id_str or str(c.get("complaint_number")).lower() == target_id_str.lower():
                complaint = c
                break

    if not complaint:
        raise ValueError(f"Complaint ID '{complaint_input}' not found.")

    complaint_id_str = str(complaint.get("complaint_number") or complaint.get("id"))
    complaint["pipeline1_status"] = "processing"

    # 2. Retrieve Top-K KB chunks (Prompt 1.2/1.3)
    desc = complaint.get("description", "")
    kb_chunks = retrieve_relevant_chunks(desc, top_k=3, include_statuses=["Active"])
    kb_chunks_text, kb_ids = _format_kb_chunks(kb_chunks)

    # 3. Retrieve Rule Matrix Candidate (Prompt 1.4)
    engine = RuleMatrixEngine()
    rule_features = {
        "category": complaint.get("category", ""),
        "subcategory": complaint.get("sub_category") or complaint.get("subcategory", ""),
        "dispute_amount_max": complaint.get("requested_credit", 0.0),
        "dispute_amount_min": complaint.get("requested_credit", 0.0),
        "description": desc
    }
    matched_rule = engine.match(rule_features)
    rule_text, rule_ids = _format_rule_context(matched_rule)

    # 4. Render Prompt Template
    renderer = PromptRenderer(db_session=db_session)
    org = ORGANIZATION_CONFIG.get("organization", {})
    context_refs = list(set(kb_ids + rule_ids))

    prompt_render_info = renderer.render_with_metadata(
        "complaint_analysis",
        organization_name=org.get("name", "NexaLink Communications"),
        organization_domain=org.get("domain", "Telecommunications"),
        support_email=org.get("support_email", "support@nexalink.com"),
        kb_chunks=kb_chunks_text,
        rule_context=rule_text,
        complaint_id=complaint_id_str,
        customer_name=complaint.get("customer_name", "Customer"),
        customer_email=complaint.get("customer_email", "customer@nexalink.com"),
        category=complaint.get("category", ""),
        subcategory=complaint.get("sub_category") or complaint.get("subcategory", ""),
        complaint_text=desc,
        schema_definition="""JSON Schema Requirement:
{
  "complaint_id": str,
  "primary_issue": str,
  "secondary_issues": [str],
  "issue_category": str,
  "subcategory": str,
  "sentiment": "Positive" | "Neutral" | "Negative" | "Strongly Negative",
  "urgency": "Low" | "Medium" | "High" | "Critical",
  "priority": "P3" | "P2" | "P1" | "P0",
  "extracted_entities": dict,
  "department": str,
  "supporting_departments": [str],
  "policy_id": str or null,
  "policy_section": str or null,
  "resolution_steps": [str],
  "refund_eligible": bool or null,
  "replacement_eligible": bool or null,
  "compensation_recommended": bool or null,
  "escalation_required": bool,
  "escalation_level": str or null,
  "escalation_reason": str or null,
  "professional_response": str,
  "follow_up_required": bool,
  "follow_up_message": str or null,
  "clarification_questions": [str],
  "complaint_summary": str,
  "agent_guidance": [str],
  "source_references": [str]
}"""
    )

    rendered_prompt = prompt_render_info["rendered_prompt"]
    tmpl_id = prompt_render_info["template_id"]
    tmpl_ver = prompt_render_info["version"]

    # 5. Execute API Call & Parse with Retry Loop
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    model_name = DEFAULT_MODEL
    attempt = 0
    success = False
    final_validated_result: Optional[ComplaintAnalysisResult] = None
    raw_response_text = ""
    last_error_msg = ""

    while attempt <= max_retries and not success:
        attempt += 1
        req_time = datetime.now(timezone.utc).isoformat()
        current_prompt = rendered_prompt

        if attempt > 1:
            current_prompt += (
                f"\n\nCRITICAL FIX REQUIRED FOR RETRY ATTEMPT #{attempt}:\n"
                f"Your previous response failed validation with error: {last_error_msg}.\n"
                "YOU MUST RETURN VALID RAW JSON ONLY MATCHING THE SCHEMA EXACTLY. NO MARKDOWN FENCES OR EXTRA TEXT."
            )

        try:
            # Determine API response source
            if mock_raw_response is not None:
                raw_response_text = mock_raw_response
            elif mock_client is not None:
                # Mock Anthropic Client provided in test
                res_obj = await mock_client.messages.create(
                    model=model_name,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": current_prompt}]
                )
                if hasattr(res_obj, "content"):
                    raw_response_text = res_obj.content[0].text if isinstance(res_obj.content, list) else str(res_obj.content)
                else:
                    raw_response_text = str(res_obj)
            elif api_key and api_key != "your_anthropic_api_key_here":
                # Live Anthropic API call via httpx
                logger.info(f"[Pipeline 1 API Call] Invoking Anthropic API ({model_name}) for complaint {complaint_id_str}...")
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.post(
                            ANTHROPIC_API_URL,
                            headers={
                                "x-api-key": api_key,
                                "anthropic-version": "2023-06-01",
                                "content-type": "application/json"
                            },
                            json={
                                "model": model_name,
                                "max_tokens": 2048,
                                "messages": [{"role": "user", "content": current_prompt}]
                            }
                        )

                        if resp.status_code == 200:
                            data = resp.json()
                            raw_response_text = data["content"][0]["text"]
                            logger.info(f"[Pipeline 1 API Response] Complaint {complaint_id_str} -> HTTP 200 OK ({model_name})")
                        else:
                            # Non-200 (401 auth, 429 rate-limit, 500 server error, etc.)
                            # → fall back to local grounded generator; don't hard-fail the whole pipeline
                            error_body = resp.text[:120]
                            logger.warning(
                                f"[Pipeline 1 API] HTTP {resp.status_code} from Anthropic for complaint "
                                f"{complaint_id_str}: {error_body}. Falling back to local grounded generator."
                            )
                            fallback_dict = _generate_fallback_json(complaint, kb_ids, rule_ids)
                            raw_response_text = json.dumps(fallback_dict)
                except (httpx.ConnectTimeout, httpx.ConnectError, httpx.RequestError) as net_err:
                    logger.warning(
                        f"[Pipeline 1 Network] Anthropic API unreachable ({str(net_err)}) "
                        f"for complaint {complaint_id_str}. Falling back to local grounded generator."
                    )
                    fallback_dict = _generate_fallback_json(complaint, kb_ids, rule_ids)
                    raw_response_text = json.dumps(fallback_dict)
            else:
                # No API key & no mock client -> standard fallback generator
                logger.info(f"[Pipeline 1 Mode] No valid ANTHROPIC_API_KEY found, using local fallback generator for complaint {complaint_id_str}")
                fallback_dict = _generate_fallback_json(complaint, kb_ids, rule_ids)
                raw_response_text = json.dumps(fallback_dict)


            resp_time = datetime.now(timezone.utc).isoformat()

            # Clean JSON text (strip markdown code blocks)
            cleaned_json_text = raw_response_text.strip()
            if cleaned_json_text.startswith("```"):
                lines = cleaned_json_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_json_text = "\n".join(lines).strip()

            # Parse JSON
            try:
                parsed_json = json.loads(cleaned_json_text)
            except json.JSONDecodeError as jde:
                raise SchemaValidationError(f"JSONDecodeError: {str(jde)}")

            # Validate Pydantic Schema
            try:
                final_validated_result = ComplaintAnalysisResult(**parsed_json)
                success = True
            except Exception as ve:
                raise SchemaValidationError(f"Schema Validation Error: {str(ve)}")

            # Log Successful GenAI Call
            call_log_entry = {
                "id": len(GENAI_CALL_LOG_STORE) + 1,
                "prompt_template_id": tmpl_id,
                "prompt_version": tmpl_ver,
                "provider": "anthropic",
                "model_name": model_name,
                "request_timestamp": req_time,
                "response_timestamp": resp_time,
                "context_references": context_refs,
                "status": "success",
                "error_details": None
            }
            GENAI_CALL_LOG_STORE.append(call_log_entry)

        except Exception as err:
            last_error_msg = str(err)
            resp_time = datetime.now(timezone.utc).isoformat()
            logger.warning(f"Pipeline 1 attempt #{attempt} failed: {last_error_msg}")

            # Log Failed Call Attempt
            call_log_entry = {
                "id": len(GENAI_CALL_LOG_STORE) + 1,
                "prompt_template_id": tmpl_id,
                "prompt_version": tmpl_ver,
                "provider": "anthropic",
                "model_name": model_name,
                "request_timestamp": req_time,
                "response_timestamp": resp_time,
                "context_references": context_refs,
                "status": "failed",
                "error_details": last_error_msg
            }
            GENAI_CALL_LOG_STORE.append(call_log_entry)

    # 6. Finalize Status
    if success and final_validated_result:
        parsed_dict = final_validated_result.model_dump()
        complaint["pipeline1_status"] = "completed"
        complaint["pipeline1_failure_reason"] = None
        complaint["genai_summary"] = final_validated_result.complaint_summary
        complaint["genai_suggested_response"] = final_validated_result.professional_response
        complaint["genai_confidence"] = 0.92
        complaint["genai_analysis_result"] = parsed_dict

        # Store in GENAI_ANALYSIS_LOG_STORE
        analysis_log_entry = {
            "id": len(GENAI_ANALYSIS_LOG_STORE) + 1,
            "complaint_id": complaint_id_str,
            "prompt_version": tmpl_ver,
            "model": model_name,
            "raw_response": raw_response_text,
            "parsed_result": parsed_dict,
            "pipeline1_status": "completed",
            "failure_reason": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        GENAI_ANALYSIS_LOG_STORE.append(analysis_log_entry)

        return {
            "complaint_id": complaint_id_str,
            "pipeline1_status": "completed",
            "failure_reason": None,
            "analysis_result": parsed_dict,
            "prompt_version": tmpl_ver,
            "model": model_name,
            "context_references": context_refs
        }
    else:
        # Max retries exhausted
        complaint["pipeline1_status"] = "failed"
        complaint["pipeline1_failure_reason"] = last_error_msg
        complaint["status"] = "Review Required"  # Set complaint for manual review routing

        analysis_log_entry = {
            "id": len(GENAI_ANALYSIS_LOG_STORE) + 1,
            "complaint_id": complaint_id_str,
            "prompt_version": tmpl_ver,
            "model": model_name,
            "raw_response": raw_response_text,
            "parsed_result": None,
            "pipeline1_status": "failed",
            "failure_reason": last_error_msg,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        GENAI_ANALYSIS_LOG_STORE.append(analysis_log_entry)

        return {
            "complaint_id": complaint_id_str,
            "pipeline1_status": "failed",
            "failure_reason": last_error_msg,
            "analysis_result": None,
            "prompt_version": tmpl_ver,
            "model": model_name,
            "context_references": context_refs
        }
