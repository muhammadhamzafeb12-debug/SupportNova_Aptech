"""
SkillSprint AI Dual-Pipeline Onboarding & Skill Training Engine

Pipeline 1: GenAI Onboarding Plan Generation (Modules, Checklists, Tasks, Quizzes, Assessments)
Pipeline 2: Python Deterministic Ground-Truth Validation Engine (Coverage, Traceability, Contradictions, Role Relevance)
Comparison & Verification Decision Engine (Verified / Warning / Manual Review)
"""

from typing import Dict, Any, List
import re

def run_pipeline_1_genai(employee: Dict[str, Any], role_matrix: Dict[str, Any], knowledge_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Pipeline 1: Generates structured onboarding plan (Learning Modules, Checklists, Tasks, Quizzes, Assessments)
    """
    role_title = role_matrix.get("role_title", employee.get("role_title", "Employee"))
    req_skills = role_matrix.get("required_skills", [])
    req_sops = role_matrix.get("required_sops", [])
    
    # Extract source references from knowledge base chunks
    valid_doc_ids = [c.get("doc_id", "POL-001") for c in knowledge_chunks] if knowledge_chunks else ["POL-001", "POL-002", "SOP-LOG-01"]
    
    modules = []
    # Module 1: Company & Role Fundamentals
    modules.append({
        "module_id": "MOD-101",
        "title": f"Introduction & Role Expectations for {role_title}",
        "duration_hours": 4,
        "source_doc_id": valid_doc_ids[0] if valid_doc_ids else "POL-001",
        "topics": [
            "Company Architecture & Values",
            f"Core Competencies for {role_title}",
            "Security & Compliance Protocols"
        ]
    })
    
    # Module 2: Core Skill & SOP Mastery
    sops_ref = valid_doc_ids[1] if len(valid_doc_ids) > 1 else "SOP-002"
    modules.append({
        "module_id": "MOD-102",
        "title": "Standard Operating Procedures & Workflow Execution",
        "duration_hours": 8,
        "source_doc_id": sops_ref,
        "topics": req_sops if req_sops else ["Order Processing SOP", "Quality Assurance Checklist", "Customer Escalations"]
    })

    # Module 3: Advanced Skills & Tooling
    modules.append({
        "module_id": "MOD-103",
        "title": "Tooling, Analytics & Performance Standards",
        "duration_hours": 6,
        "source_doc_id": valid_doc_ids[0],
        "topics": req_skills if req_skills else ["CRM Platform", "Ticket Management", "SLA Tracking"]
    })

    # Checklists
    checklists = [
        {"id": "CHK-01", "item": "Complete Security & Compliance NDA", "mandatory": True},
        {"id": "CHK-02", "item": "Set up Dev/Workspace Tooling & Credentials", "mandatory": True},
        {"id": "CHK-03", "item": "Review Core Role SOPs & Policy Guidelines", "mandatory": True},
        {"id": "CHK-04", "item": "Shadow Senior Team Member on 3 Live Operations", "mandatory": False}
    ]

    # Tasks
    tasks = [
        {"task_id": "TSK-01", "title": "Setup System Access & Security 2FA", "day": 1, "estimated_hours": 2},
        {"task_id": "TSK-02", "title": "Read & Sign Off Policy Document " + (valid_doc_ids[0] if valid_doc_ids else "POL-001"), "day": 2, "estimated_hours": 3},
        {"task_id": "TSK-03", "title": "Complete Hands-on Operational Workflow Practice", "day": 4, "estimated_hours": 5},
        {"task_id": "TSK-04", "title": "Submit First Independent Operations Log", "day": 7, "estimated_hours": 4}
    ]

    # Quizzes
    quizzes = [
        {
            "quiz_id": "QZ-01",
            "title": "Company Policy & Security Quiz",
            "passing_score": role_matrix.get("minimum_passing_quiz_score", 80),
            "questions_count": 10
        },
        {
            "quiz_id": "QZ-02",
            "title": f"SOP & Operational Execution for {role_title}",
            "passing_score": role_matrix.get("minimum_passing_quiz_score", 80),
            "questions_count": 12
        }
    ]

    # Assessments
    assessments = [
        {
            "assessment_id": "ASM-01",
            "title": "Day-7 Practical Onboarding Scenario Evaluation",
            "evaluator": "Direct Manager / Supervisor",
            "type": "PRACTICAL_EVALUATION"
        },
        {
            "assessment_id": "ASM-02",
            "title": "Final Onboarding Competency Certification",
            "evaluator": "Department Head",
            "type": "CERTIFICATION"
        }
    ]

    return {
        "learning_modules": modules,
        "checklists": checklists,
        "tasks": tasks,
        "quizzes": quizzes,
        "assessments": assessments
    }


def run_pipeline_2_python_validation(employee: Dict[str, Any], role_matrix: Dict[str, Any], genai_plan: Dict[str, Any], knowledge_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Pipeline 2: Non-LLM Ground-Truth Validation Engine
    Validates requirements coverage, source traceability, contradiction detection, and role relevance.
    """
    req_skills = set(role_matrix.get("required_skills", []))
    req_sops = set(role_matrix.get("required_sops", []))
    all_requirements = req_skills.union(req_sops)

    # Collect topics and text from GenAI plan
    covered_items = set()
    plan_text = ""
    modules = genai_plan.get("learning_modules", [])
    
    for mod in modules:
        plan_text += " " + mod.get("title", "")
        for topic in mod.get("topics", []):
            plan_text += " " + str(topic)
            for req in all_requirements:
                if req.lower() in str(topic).lower():
                    covered_items.add(req)

    # Calculate Coverage %
    if all_requirements:
        coverage_percent = round((len(covered_items) / len(all_requirements)) * 100.0, 1)
    else:
        coverage_percent = 100.0

    missing = list(all_requirements - covered_items)

    # Validate Sources & Traceability
    valid_doc_ids = set(c.get("doc_id") for c in knowledge_chunks if c.get("doc_id")) if knowledge_chunks else set()
    verified_sources = []
    unverified_sources = []

    for mod in modules:
        source_id = mod.get("source_doc_id")
        if source_id:
            if valid_doc_ids and source_id in valid_doc_ids:
                verified_sources.append(source_id)
            elif not valid_doc_ids:
                verified_sources.append(source_id)
            else:
                unverified_sources.append(source_id)

    total_modules = len(modules)
    traceability_score = round((len(verified_sources) / max(total_modules, 1)) * 100.0, 1)

    # Detect Contradictions & Outdated Policy References
    contradictions = []
    if unverified_sources:
        contradictions.append(f"Unapproved or unverified document source referenced in modules: {', '.join(unverified_sources)}")

    if "outdated" in plan_text.lower() or "deprecated" in plan_text.lower():
        contradictions.append("Plan references deprecated operational guidelines.")

    # Consistency Score
    consistency_score = 100.0 - (len(contradictions) * 20.0) - (len(missing) * 10.0)
    consistency_score = max(0.0, min(100.0, round(consistency_score, 1)))

    return {
        "coverage_score": coverage_percent,
        "traceability_score": traceability_score,
        "consistency_score": consistency_score,
        "covered_requirements": list(covered_items),
        "missing_requirements": missing,
        "verified_sources": list(set(verified_sources)),
        "unverified_sources": list(set(unverified_sources)),
        "contradictions_detected": contradictions
    }


def compute_verification_decision(val_res: Dict[str, Any]) -> str:
    """
    Computes overall verification decision: VERIFIED, WARNING, or MANUAL_REVIEW
    """
    coverage = val_res.get("coverage_score", 0.0)
    contradictions = val_res.get("contradictions_detected", [])
    traceability = val_res.get("traceability_score", 0.0)

    if contradictions or coverage < 60.0:
        return "MANUAL_REVIEW"
    elif coverage < 85.0 or traceability < 80.0:
        return "WARNING"
    else:
        return "VERIFIED"
