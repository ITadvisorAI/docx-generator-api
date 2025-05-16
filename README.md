# 📄 DOCX Generator API – IT Transformation Advisor

This Flask-based microservice generates personalized DOCX intake reports based on structured JSON input. It is part of the IT Transformation Advisor automation system and integrates with Make.com and OpenAI GPTs.

---

## 🚀 Features

- Accepts JSON input including email, session ID, answers, and file list
- Generates a `.docx` report using a Word template (`intakeform.docx`)
- Saves the generated file in a temp folder by `session_id`
- Serves the generated file at a public URL
- Easily deployable to [Render.com](https://render.com)

---

## 🧱 Tech Stack

- Python 3.11+
- Flask
- python-docx
- requests
- gunicorn (for production)

---

## 🛠️ API Endpoints

### `POST /generate_intake`

Generate an intake report for a user session.

#### Request Body (JSON)

```json
{
  "session_id": "Temp_05162025_test.user@example.com",
  "email": "test.user@example.com",
  "intake_answers": {
    "selected_categories": ["Infrastructure Modernization"],
    "selected_programs": {
      "Infrastructure Modernization": ["Cloud Strategy"]
    },
    "q1": "Primary goal?",
    "q2": "When will the project start?",
    "q3": "Optimization target?",
    "q4": "Preferred platform?",
    "q5": "Delivery model?"
  },
  "files": [
    {
      "name": "asset_inventory.csv",
      "url": "https://...",
      "type": "asset_inventory"
    }
  ]
}
