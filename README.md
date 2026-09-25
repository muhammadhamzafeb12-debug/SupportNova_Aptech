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
  app/                          # Streamlit presentation UI layer
    Home.py                     # Entry point & landing page
    pages/                      # Role-based Streamlit views
  backend/                      # Core business logic python packages
    complaint_processing/       # Complaint lifecycle & ingestion
    document_processing/        # PDF, DOCX, OCR text extraction
    knowledge_base/             # FAISS / RAG indexer
    genai_pipeline/             # Anthropic Claude complaint classification
    python_validation/          # Ground-truth deterministic verifiers
    complaint_rules/            # Rule matrix execution
    routing_rules/              # Department auto-routing logic
    escalation_rules/           # SLA breach & executive escalation matrix
    prompt_templates/           # System & reasoning prompt templates
    schemas/                    # Pydantic data models
    comparison_engine/          # Dual-pipeline alignment checker
    hallucination_checks/       # Ground-truth inconsistency detection
    security/                   # Authentication & role authorization
    database/                   # SQLAlchemy ORM models & migrations
    tests/                      # Pytest suite
  config/                       # Domain JSON configurations
  sample_complaints/            # Test payload datasets
  sample_documents/             # Attachment samples
  hidden_test_ready/            # Hidden evaluation dataset
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
