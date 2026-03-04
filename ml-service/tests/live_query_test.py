import urllib.request
import json

url = "http://localhost:5050/query"

def ask(question):
    payload = json.dumps({"query": question, "language": "en"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()).get("response", "NO RESPONSE")
    except Exception as e:
        return f"ERROR: {e}"

questions = [
    "What does the zigzag pattern on agaseke mean?",
    "What wood is used to make the Inanga zither?",
    "How were the Rwandan battle shields reinforced?",
    "Tell me about the Karinga drum in the Ethnographic Museum",
    "What happens when the eternal fire goes out?",
]

with open("live_query_results.txt", "w", encoding="utf-8") as f:
    for q in questions:
        r = ask(q)
        f.write(f"Q: {q}\n")
        f.write(f"A: {r}\n")
        f.write("-" * 60 + "\n")
        print(f"Done: {q[:50]}")

print("Results saved to live_query_results.txt")
