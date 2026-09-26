# SupportNova — AI-Powered Customer Complaint Intelligence Platform

SupportNova is an enterprise-grade AI complaint resolution intelligence platform built for telecommunications providers (configured for **NexaLink Communications**).

## 🚀 Architecture Highlights

- **Dual-Pipeline Validation Engine:** GenAI reasoning pipeline paired with deterministic Python ground-truth verification.
- **Configuration-Driven Design:** All organization profiles, product catalogs, complaint taxonomy (10 categories, 33 subcategories), and department SLA matrices are dynamically loaded from JSON files in `config/`.
- **Decoupled Monorepo Architecture:**
  - `app/` — Multipage Streamlit UI presentation layer.
  - `backend/` — Fully testable, decoupled Python core modules (routing, rules engine, document processing, RAG knowledge base, hallucination detection).

## 📁 Repository Directory Layout

```
supportnova/
  frontend/                     # React + Next.js Enterprise Dark-Glow UI layer
    pages/                      # App page routing
    src/                        # Components, context, and views (Dashboards, Reviewer Queue, KB, SLA)
  backend/                      # Core business logic Python packages
    complaint_processing/       # State machine (validate_transition) & SLA tracking engine
    document_processing/        # PDF, DOCX, OCR text extraction
    knowledge_base/             # RAG indexer
    genai_pipeline/             # LLM complaint analysis & prompt templates
    python_validation/          # Ground-truth deterministic verifiers
    complaint_rules/            # Rule Matrix Engine
    routing_rules/              # Department auto-routing logic
    escalation_rules/           # SLA breach & executive escalation matrix
    prompt_templates/           # System & reasoning prompt templates
    schemas/                    # Pydantic data models
    comparison_engine/          # Dual-pipeline alignment checker
    hallucination_checks/       # Ground-truth inconsistency detection
    security/                   # Authentication & role authorization
    database/                   # SQLAlchemy ORM models & seed database
    src/api/                    # FastAPI routers (complaints, reviewer, sla, auth, kb)
    tests/                      # Pytest suite
  config/                       # Domain JSON configurations & sla_targets.json
  sample_complaints/            # Test payload datasets
  sample_documents/             # Attachment samples
  hidden_test_ready/            # Evaluation dataset
  documentation/                # Architecture docs & guides
  screenshots/                  # System screenshots
  reports/                      # Generated evaluation reports
```

## 🛠️ Quickstart Guide

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Streamlit application:**
   ```bash
   streamlit run app/Home.py
   ```

3. **Run unit & integration tests:**
   ```bash
   pytest backend/tests
   ```
