# NexaLink Communications — Organization Profile
**SupportNova Project Reference Document**
*Config Version 1.0 | Last Updated: 2026-09-25*

---

## 1. Company Overview

| Field | Detail |
|---|---|
| **Company Name** | NexaLink Communications |
| **Industry** | Telecommunications |
| **Founded** | 2009 |
| **Headquarters** | Austin, Texas, USA |
| **Subscribers** | ~4.2 million active |
| **Coverage** | 29 US States |
| **Support Email** | support@nexalink.com |
| **Support Phone** | 1-800-NEX-LINK |

NexaLink Communications is a mid-tier telecommunications provider offering mobile voice and
data plans, home broadband, enterprise fiber solutions, and IPTV streaming to over 4.2 million
subscribers across 29 states. The company is known for its aggressive 5G rollout and its
**NexaCloud** unified communications platform targeting small and medium-sized businesses.

---

## 2. Product & Service Catalog (12 Products)

| ID | Product | Type | Monthly Price |
|---|---|---|---|
| PROD-001 | NexaMobile Lite | Prepaid Mobile Plan | $19.99 |
| PROD-002 | NexaMobile Unlimited | Postpaid Mobile Plan | $49.99 |
| PROD-003 | NexaMobile Family Pack | Shared Family Plan (5 lines) | $119.99 |
| PROD-004 | NexaFiber Home 300 | Residential Broadband (300 Mbps) | $39.99 |
| PROD-005 | NexaFiber Home 1Gig | Residential Broadband (1 Gbps) | $69.99 |
| PROD-006 | NexaStream TV | IPTV (180+ channels, cloud DVR) | $29.99 |
| PROD-007 | NexaBundle Home+ | Fiber 300 + IPTV Bundle | $59.99 |
| PROD-008 | NexaCloud SMB | Unified Comms for SMBs (VoIP+Video) | $149.99 |
| PROD-009 | NexaFiber Enterprise | SLA-backed Business Fiber | $299.99 |
| PROD-010 | NexaRoam Global Pass | International Roaming Add-on (80+ countries) | $24.99 |
| PROD-011 | NexaShield Security Suite | Mobile & Network Security Add-on | $9.99 |
| PROD-012 | NexaDevice Hub | Wi-Fi 6E Mesh Router (3-node lease) | $8.99/mo |

---

## 3. Complaint Category Structure (10 Categories, 33 Subcategories)

| # | Category | Code | Subcategories | Priority Weight |
|---|---|---|---|---|
| 1 | Billing & Payments | `BILLING` | 5 | 9/10 |
| 2 | Network & Connectivity | `NETWORK` | 4 | 10/10 |
| 3 | Device & Equipment | `DEVICE` | 3 | 7/10 |
| 4 | Account Management | `ACCOUNT` | 3 | 8/10 |
| 5 | Account Security & Fraud | `SECURITY` | 3 | 10/10 |
| 6 | International Roaming | `ROAMING` | 2 | 7/10 |
| 7 | NexaStream TV & IPTV | `IPTV` | 3 | 6/10 |
| 8 | Installation & Field Service | `INSTALLATION` | 3 | 8/10 |
| 9 | Number Portability & Transfer | `PORTABILITY` | 3 | 7/10 |
| 10 | Regulatory & Compliance | `COMPLIANCE` | 4 | 10/10 |

> **Design Note:** Categories with priority weight **10** trigger enhanced SLA timers and
> auto-escalation rules within SupportNova. Subcategory codes are the canonical identifiers
> used across the AI routing engine, Python ground-truth classifier, and the dashboard UI.

---

## 4. Department Structure (9 Departments)

| ID | Department | Short Name | SLA Response | SLA Resolution | Can Credit? |
|---|---|---|---|---|---|
| DEPT-001 | Billing & Revenue Assurance | Billing | 24 hrs | 72 hrs | ✅ |
| DEPT-002 | Network Operations & Engineering | Network Ops | 4 hrs | 24 hrs | ❌ |
| DEPT-003 | Device & Warranty Services | Device & Warranty | 12 hrs | 96 hrs | ❌ |
| DEPT-004 | Account Management & Provisioning | Account Management | 8 hrs | 48 hrs | ❌ |
| DEPT-005 | Account Security & Fraud Prevention | Security & Fraud | 1 hr | 12 hrs | ✅ |
| DEPT-006 | Content & Streaming Services | Content Services | 8 hrs | 48 hrs | ❌ |
| DEPT-007 | Field Operations & Installation Services | Field Operations | 4 hrs | 48 hrs | ❌ |
| DEPT-008 | Regulatory Affairs & Legal Compliance | Compliance & Legal | 2 hrs | 24 hrs | ✅ |
| DEPT-009 | Executive Escalations & Customer Relations | Executive Escalations | 1 hr | 8 hrs | ✅ |

### Escalation Matrix

- **Default Final Escalation:** Executive Escalations (DEPT-009)
- **Triggers for Immediate Executive Escalation:**
  - 3+ failed resolution attempts at primary department
  - Media or social media mention linked to the complaint
  - Legal threat or attorney-of-record involvement
  - VIP or Enterprise account flag
  - Safety risk to customer or property

> **Critical:** DEPT-005 (Security & Fraud) operates a 24/7 rapid-response team.
> Any complaint tagged `SECURITY_SIM_SWAP` or `SECURITY_ACCOUNT_TAKEOVER` must
> bypass standard queue routing and be treated as P0.

---

## 5. Configuration Architecture for SupportNova

All data in this document is machine-readable and stored in three JSON config files:

| File | Purpose |
|---|---|
| `config/organization.json` | Company identity, product catalog, app metadata |
| `config/categories.json` | All complaint categories and subcategories with routing hints |
| `config/departments.json` | Department definitions, SLA targets, and escalation matrix |

> **Architectural Principle:** No category codes, department IDs, SLA values, or product
> names are hard-coded in application logic. All SupportNova modules load these configs at
> runtime, making the platform fully reconfigurable without code changes.

---

## 6. SupportNova AI Routing Rules (Derived from Config)

The following routing rules are auto-derived by the SupportNova engine from `departments.json`:

1. Complaints tagged `COMPLIANCE_REGULATORY_COMPLAINT` → **auto-route to DEPT-008**, bypass queue.
2. Any complaint where `priority_weight = 10` → activate **enhanced SLA monitoring**.
3. Departments with `can_issue_credits: true` → displayed with credit-authorization actions in agent UI.
4. Repeat complaints (≥3 on same account within 30 days) → escalate to **DEPT-009** regardless of category.

---

*This document is auto-consistent with the three JSON config files. Any updates to the configs should be reflected here.*
