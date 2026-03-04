from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_pipeline import initialize_rag, get_answer
import os

app = Flask(__name__)
CORS(app)

print("Starting Rwandan Museum ML Service...")
initialize_rag()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "Museum-RAG-Engine"})

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(force=True, silent=True)
    if data is None:
        data = {}
    user_query = data.get("query", "")
    language = data.get("language", "en")

    print(f"Received query: '{user_query}' in language: '{language}'")

    if not user_query:
        return jsonify({
            "language": language,
            "response": "Please provide a question."
        })

    answer = get_answer(user_query, language)
    print(f"Generated answer in {language}: {answer[:80]}...")

    return jsonify({
        "language": language,
        "response": answer
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=False)

