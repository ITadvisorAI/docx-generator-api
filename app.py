from flask import Flask, request, jsonify
from generate_assessment import generate_assessment_docs

app = Flask(__name__)

@app.route("/generate_assessment", methods=["POST"])
def generate_assessment():
    try:
        data = request.get_json()
        session_id = data["session_id"]
        score_summary = data["score_summary"]
        recommendations = data["recommendations"]
        key_findings = data["key_findings"]

        result = generate_assessment_docs(session_id, score_summary, recommendations, key_findings)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["HEAD", "GET"])
def health_check():
    return "✅ docx-generator-api is live"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10010)
