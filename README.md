# 📄 DOCX Generator API – IT Transformation Advisor

This microservice is part of the AI-powered **IT Transformation Advisor** system. It generates:

- A detailed **infrastructure assessment report** in DOCX
- An executive summary **PowerPoint deck (PPTX)**

These documents are created from structured scoring, recommendations, and findings provided by GPT modules (e.g., GPT2 – it_assessment).

---

## 🚀 Features

- Accepts JSON POST requests via `/generate_assessment`
- Generates:
  - 📄 IT_Current_Status_Assessment_Report.docx
  - 📊 IT_Current_Status_Executive_Report.pptx
- Saves documents inside session-named folders (`temp_sessions/<session_id>/`)
- Serves public download links via `/files/<path>`
- Deployable on [Render](https://render.com)

---

## 🧱 Tech Stack

- Python 3.11+
- Flask
- python-docx
- python-pptx
- gunicorn (WSGI server for production)

---

## 🛠️ API Endpoints

### POST `/generate_assessment`

Generates both DOCX and PPTX reports from IT scoring and recommendations.

#### 📤 Request Body (JSON)

```json
{
  "session_id": "Temp_20250521_user_example_com",
  "score_summary": "Excellent: 20%, Advanced: 40%, Standard: 30%, Obsolete: 10%",
  "recommendations": "Decommission Tier 1 servers and migrate Tier 2 workloads to Azure.",
  "key_findings": "Several critical systems run on unsupported platforms, posing business continuity risks."
}
