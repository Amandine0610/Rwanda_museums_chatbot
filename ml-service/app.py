from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_pipeline import initialize_rag, get_answer
import os

import threading

app = Flask(__name__)
CORS(app)

rag_initialized = False

def background_init():
    global rag_initialized
    print("Starting Rwandan Museum ML Service (Background)...")
    try:
        initialize_rag()
        rag_initialized = True
        print("RAG Initialization Complete.")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize RAG in background: {e}")

# Start initialization in a separate thread to allow server to bind port quickly
threading.Thread(target=background_init, daemon=True).start()

@app.route('/health', methods=['GET'])
def health():
    status = "healthy" if rag_initialized else "loading"
    return jsonify({"status": status, "service": "Museum-RAG-Engine", "initialized": rag_initialized})

@app.route("/query", methods=["POST"])
def query():
    if not rag_initialized:
        return jsonify({
            "response": "The museum guide is still waking up... Please wait 30 more seconds and try again.",
            "status": "loading"
        }), 503

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
    # Use PORT from environment (Render/Railway inject this)
    port = int(os.environ.get('PORT', 5050))
    print(f"Binding to port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

