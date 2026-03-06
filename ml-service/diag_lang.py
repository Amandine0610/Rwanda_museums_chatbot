from rag_pipeline import initialize_rag, get_answer
import os

# Mock environment if needed (already set in .env usually)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "missing")

print("Initializing RAG...")
initialize_rag()

print("\n--- TEST: KINYARWANDA ---")
# Query: "Karinga ni iki?" (What is Karinga?)
ans_rw = get_answer("Karinga ni iki?", "rw")
print(f"RESPONSE (RW): {ans_rw}")

print("\n--- TEST: FRENCH ---")
# Query: "Qu'est-ce que le Karinga ?" (What is Karinga?)
ans_fr = get_answer("Qu'est-ce que le Karinga ?", "fr")
print(f"RESPONSE (FR): {ans_fr}")
