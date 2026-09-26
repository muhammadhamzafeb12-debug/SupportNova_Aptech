"""
Ground-truth business-rule engine for SupportNova.
Pure deterministic Python engine — completely independent of GenAI models.
Evaluates structured complaint features against active rule matrix conditions.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.src.store import RULE_MATRIX_STORE, RULE_MATCH_LOG_STORE


@dataclass
class MatchedRule:
    rule_id: str
    category: str
    subcategory: str
    department: str
    supporting_departments: List[str]
    urgency: str
    priority: str
    policy_id: str
    escalation_required: bool
    escalation_level: Optional[str]
    required_actions: List[str]
    prohibited_actions: List[str]
    follow_up_required: bool
    conditions: Dict[str, Any]
    matched_keys_count: int = 0
    updated_at: str = ""


class RuleMatrixEngine:
    def __init__(self, rules_store: Optional[List[Dict[str, Any]]] = None):
        """Initialize engine with a rule dataset or default to RULE_MATRIX_STORE."""
        self.rules_store = rules_store if rules_store is not None else RULE_MATRIX_STORE

    def match(self, complaint_features: dict) -> Optional[MatchedRule]:
        """
        Pure deterministic matching algorithm.
        No LLM call, no randomness, 100% reproducible.
        
        Algorithm:
        1. Filter active rules.
        2. Match category & subcategory (case-insensitive).
        3. Evaluate condition dict against complaint_features.
        4. Rank matches by condition specificity (most matched keys win; ties broken by most recent updated_at).
        5. Log attempt to audit trail store and database.
        """
        features = complaint_features or {}
        category_input = str(features.get("category", "")).strip().lower()
        subcategory_input = str(features.get("subcategory", "") or features.get("sub_category", "")).strip().lower()

        # Step 1 & 2: Filter candidate active rules matching category/subcategory
        candidate_rules = []
        for rule in self.rules_store:
            if not rule.get("is_active", True):
                continue

            rule_cat = str(rule.get("category", "")).strip().lower()
            rule_subcat = str(rule.get("subcategory", "")).strip().lower()

            # Category must match if provided in features
            if category_input and rule_cat and category_input != rule_cat:
                continue

            # Subcategory must match if provided in features
            if subcategory_input and rule_subcat and subcategory_input != rule_subcat:
                continue

            candidate_rules.append(rule)

        # If no candidates matched exact subcategory, fallback to matching active rules of the same category
        if not candidate_rules and category_input:
            for rule in self.rules_store:
                if not rule.get("is_active", True):
                    continue
                rule_cat = str(rule.get("category", "")).strip().lower()
                if category_input == rule_cat:
                    candidate_rules.append(rule)

        # Step 3: Evaluate conditions for each candidate rule
        matched_rules: List[MatchedRule] = []

        for rule in candidate_rules:
            conditions = rule.get("conditions", {})
            if not isinstance(conditions, dict):
                continue

            rule_matches = True
            matched_count = 0

            for cond_key, cond_val in conditions.items():
                feature_val = features.get(cond_key)
                if feature_val is None:
                    # Strip common condition prefixes/suffixes if exact key not in features
                    base_key = cond_key
                    for suffix in ("_min", "_max"):
                        if base_key.endswith(suffix):
                            base_key = base_key[:-len(suffix)]
                    for prefix in ("min_", "max_", "gte_", "lte_"):
                        if base_key.startswith(prefix):
                            base_key = base_key[len(prefix):]
                    feature_val = features.get(base_key)

                if feature_val is None:
                    # Feature not provided in input features — skip checking this optional condition
                    continue

                # Evaluate condition based on type and operator naming
                if not self._evaluate_single_condition(cond_key, cond_val, feature_val):
                    rule_matches = False
                    break

                matched_count += 1

            if rule_matches:
                matched_rules.append(MatchedRule(
                    rule_id=rule.get("rule_id", "UNKNOWN"),
                    category=rule.get("category", ""),
                    subcategory=rule.get("subcategory", ""),
                    department=rule.get("department", ""),
                    supporting_departments=rule.get("supporting_departments", []),
                    urgency=rule.get("urgency", "Medium"),
                    priority=rule.get("priority", "Medium"),
                    policy_id=rule.get("policy_id", ""),
                    escalation_required=rule.get("escalation_required", False),
                    escalation_level=rule.get("escalation_level"),
                    required_actions=rule.get("required_actions", []),
                    prohibited_actions=rule.get("prohibited_actions", []),
                    follow_up_required=rule.get("follow_up_required", False),
                    conditions=conditions,
                    matched_keys_count=matched_count,
                    updated_at=rule.get("updated_at", "")
                ))

        # Step 4: Precedence ranking
        # Rank by: 1) matched_keys_count descending (most specific condition set wins)
        #          2) updated_at descending (most recent wins tie)
        #          3) rule_id descending as final fallback
        final_match: Optional[MatchedRule] = None
        if matched_rules:
            matched_rules.sort(
                key=lambda r: (r.matched_keys_count, r.updated_at or "", r.rule_id),
                reverse=True
            )
            final_match = matched_rules[0]

        # Step 5: Log match attempt for audit trail deliverable
        now_iso = datetime.now(timezone.utc).isoformat()
        log_entry = {
            "rule_id": final_match.rule_id if final_match else "no_match",
            "complaint_features": features,
            "matched": final_match is not None,
            "matched_at": now_iso
        }
        RULE_MATCH_LOG_STORE.append(log_entry)

        # Attempt logging to DB rule_match_log table if DB session available
        try:
            from backend.database.db import SessionLocal, HAS_SQLALCHEMY
            from backend.database.models import RuleMatchLogModel
            if HAS_SQLALCHEMY and SessionLocal:
                db = SessionLocal()
                try:
                    db_log = RuleMatchLogModel(
                        rule_id=final_match.rule_id if final_match else "no_match",
                        complaint_features=features,
                        matched=final_match is not None,
                        matched_at=datetime.now(timezone.utc)
                    )
                    db.add(db_log)
                    db.commit()
                except Exception:
                    db.rollback()
                finally:
                    db.close()
        except Exception:
            pass

        return final_match

    def _evaluate_single_condition(self, key: str, target_val: Any, actual_val: Any) -> bool:
        """Evaluates a single condition key-value pair against an actual feature value."""
        if actual_val is None:
            return False

        # Boolean check
        if isinstance(target_val, bool):
            return bool(actual_val) == target_val

        # Numeric threshold comparisons based on key naming conventions
        if key.startswith("min_") or key.endswith("_min") or key.startswith("gte_"):
            try:
                return float(actual_val) >= float(target_val)
            except (ValueError, TypeError):
                return False

        if key.startswith("max_") or key.endswith("_max") or key.startswith("lte_"):
            try:
                return float(actual_val) <= float(target_val)
            except (ValueError, TypeError):
                return False

        # Operator dict handling e.g. {">=": 100}
        if isinstance(target_val, dict):
            for op, val in target_val.items():
                op_str = str(op).lower()
                try:
                    if op_str in (">=", "gte"):
                        if not (float(actual_val) >= float(val)): return False
                    elif op_str in ("<=", "lte"):
                        if not (float(actual_val) <= float(val)): return False
                    elif op_str in (">", "gt"):
                        if not (float(actual_val) > float(val)): return False
                    elif op_str in ("<", "lt"):
                        if not (float(actual_val) < float(val)): return False
                    elif op_str in ("==", "equals", "eq"):
                        if not (str(actual_val).strip().lower() == str(val).strip().lower()): return False
                    elif op_str in ("in", "contains"):
                        if isinstance(val, list):
                            if not any(str(x).lower() in str(actual_val).lower() for x in val): return False
                        else:
                            if not (str(val).lower() in str(actual_val).lower()): return False
                except (ValueError, TypeError):
                    return False
            return True

        # List / Keyword check
        if isinstance(target_val, list):
            if isinstance(actual_val, list):
                return bool(set(target_val).intersection(set(actual_val)))
            elif isinstance(actual_val, str):
                actual_lower = actual_val.lower()
                return any(str(item).lower() in actual_lower for item in target_val)

        # Reverse list check (actual_val is a list of features)
        if isinstance(actual_val, list):
            return any(str(target_val).lower() == str(item).lower() for item in actual_val)

        # Direct numeric equality check
        if isinstance(target_val, (int, float)) and isinstance(actual_val, (int, float)):
            return float(actual_val) == float(target_val)

        # General string equality check
        return str(actual_val).strip().lower() == str(target_val).strip().lower()

