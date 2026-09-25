# SupportNova AI Usage & Architecture Disclosures

## 🤖 AI Models & Pipelines Used

SupportNova utilizes a dual-pipeline architecture to process, classify, route, and resolve customer complaints with zero hallucination tolerance:

1. **Generative AI Pipeline:**
   - **Model:** Anthropic Claude 3.5 Sonnet / Claude 3 Haiku
   - **Role:** Natural language complaint parsing, sentiment scoring, root-cause summary extraction, and drafting resolution responses.

2. **Deterministic Python Ground-Truth Pipeline:**
   - **Role:** Independent rule-based classification, contract verification, regulatory trigger detection, SLA assignment, and financial credit limits enforcement.

3. **Dual-Pipeline Alignment & Hallucination Detector:**
   - Compares GenAI proposed routing/category against Python ground-truth.
   - Flags discrepancies, out-of-boundary financial credits, or unverified claims for human reviewer queue.

## 🛡️ Safety, Security, and Compliance

- **PII Scrubbing:** Customer identities and credit card numbers are scrubbed prior to sending prompts to GenAI APIs.
- **Role-Based Access Control:** Strict role segregation enforced across Customer, Agent, Reviewer, Manager, and Admin dashboards.
- **Audit Logging:** Every AI decision and ground-truth validation is recorded in the PostgreSQL database with timestamp and confidence score.
