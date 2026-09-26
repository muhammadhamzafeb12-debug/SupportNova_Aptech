# SupportNova 🚀

**SupportNova** is an AI-powered customer complaint resolution platform for **NovaCart Technologies**. It uses a **Dual-Pipeline Architecture**:
- **Pipeline 1 (GenAI)**: Recommends resolutions using Generative AI (Gemini / LLM).
- **Pipeline 2 (Python Ground-Truth)**: Deterministic business-rules engine with 120+ rules (100% LLM-free validation).

---

## 🔑 Quick Demo Login Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` |
| **Manager** | `manager` | `manager123` |
| **Reviewer** | `reviewer` | `reviewer123` |
| **Agent** | `agent` | `agent123` |
| **Customer** | `customer` | `customer123` |

---

## ⚡ How to Run

### 1. Backend Server (FastAPI)
```powershell
cmd /c "set PYTHONPATH=. && .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000"
```
*API Docs:* http://localhost:8000/docs

### 2. Frontend UI (Vite + React)
```powershell
cd frontend
npm run dev
```
*Web App:* http://localhost:3000

### 3. Run Automated Tests (Pytest)
```powershell
cmd /c "set PYTHONPATH=. && .\.venv\Scripts\python.exe -m pytest"
```

---

## 🛡️ Key Features
- **Dual-Pipeline Verification**: Compares AI predictions against Python business rules.
- **Rule Matrix**: 120+ structured rules across 10 categories.
- **Prompt Injection Protection**: Strips malicious commands from complaint text.
- **Manual Review Queue**: Automatically flags mismatches and rule violations.
