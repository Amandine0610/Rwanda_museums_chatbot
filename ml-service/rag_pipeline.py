import os
from dotenv import load_dotenv

load_dotenv()

vector_store = None
qa_chain = None
retriever = None
qa_extractor = None  # For local extractive QA
use_openai_mode = False


def initialize_rag():
    global vector_store, qa_chain, retriever, qa_extractor, use_openai_mode

    try:
        print("--- RAG INITIALIZATION START ---")
        
        # Check for OpenAI Key immediately
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("WARNING: OPENAI_API_KEY not found in environment variables.")
        else:
            print(f"DEBUG: OpenAI Key found (starts with: {api_key[:8]}...)")

        from langchain_community.document_loaders import TextLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        # 1. Load museum data
        data_path = os.path.join(os.path.dirname(__file__), "museum_data.txt")
        if not os.path.exists(data_path):
            print(f"ERROR: museum_data.txt NOT FOUND at {data_path}")
            return
            
        loader = TextLoader(data_path, encoding="utf-8")
        documents = loader.load()

        # 2. Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " "]
        )
        chunks = splitter.split_documents(documents)
        print(f"Documents parsed into {len(chunks)} chunks.")

        # 3. Try OpenAI
        use_openai_mode = False
        if api_key and api_key.strip():
            try:
                from langchain_openai import OpenAIEmbeddings, ChatOpenAI
                print("Initializing OpenAI Models...")
                embeddings = OpenAIEmbeddings(openai_api_key=api_key)
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=api_key)
                # Quick test
                embeddings.embed_query("ping")
                use_openai_mode = True
                print("SUCCESS: OpenAI (gpt-4o-mini) initialized.")
            except Exception as e_openai:
                print(f"ERROR: OpenAI initialization failed: {e_openai}")

        # 4. Fallback Handling
        if not use_openai_mode:
            print("FALLBACK: OpenAI unavailable (Quota or Key issue).")
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                print("Loading Lightweight Embeddings (MiniLM)...")
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                print("MiniLM Embeddings loaded successfully.")
                use_openai_mode = False
                qa_chain = "lightweight_mode" # Flag for direct chunk return
            except Exception as e_light:
                print(f"FAILED to load light embeddings: {e_light}")
                qa_chain = None
                return

        # 5. Initialize Vector Store
        persist_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
        vector_store = Chroma.from_documents(
            chunks,
            embeddings,
            collection_name="museum_collection",
            persist_directory=persist_dir
        )
        print(f"Vector Store ready at {persist_dir}")

        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        if use_openai_mode:
            prompt = ChatPromptTemplate.from_template(
                """You are a Rwanda Museum Guide. Answer ONLY using the context:
                
                Context: {context}
                Language: {language}
                Question: {query}
                
                Answer:"""
            )

            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)

            qa_chain = (
                {
                    "context": (lambda x: x["query"]) | retriever | format_docs,
                    "query": lambda x: x["query"],
                    "language": lambda x: x["language"]
                }
                | prompt
                | llm
                | StrOutputParser()
            )

        print("--- RAG INITIALIZATION COMPLETE ---")

    except Exception as e:
        print(f"CRITICAL ERROR during RAG init: {e}")
        qa_chain = None


def get_answer(query: str, language: str = "en") -> str:
    global retriever, qa_chain, vector_store, use_openai_mode

    if qa_chain is None or retriever is None:
        return "The museum guide system is currently initializing or encountered a configuration error. Please check your API key."

    try:
        # 1. OpenAI Generative Mode
        if use_openai_mode:
            response = qa_chain.invoke({"query": query, "language": language})
            return response.strip()

        # 2. Lightweight Fallback Mode (Returns direct archive match)
        # This is used when OpenAI fails to prevent memory crashes on Render.
        docs_and_scores = vector_store.similarity_search_with_score(query, k=1)
        if not docs_and_scores:
            return "I'm sorry, I couldn't find any information about that in the museum archives."

        best_chunk = docs_and_scores[0][0].page_content.strip()
        
        # Multilingual prefix based on language
        intro = {
            "en": "I found this in the museum archives: ",
            "fr": "J'ai trouvé ceci dans les archives du musée: ",
            "rw": "Ibi niko bimeze mu nyandiko z'intebe y'ubumenyi: ",
        }.get(language, "I found this: ")

        return f"{intro}\n\n{best_chunk}"

        # ── LOCAL PRECISION MODE ──────────────────────────────────────────────
        # KEY INSIGHT: Sort by distance score (lower = better in Chroma L2 space).
        # Use ONLY THE SINGLE BEST CHUNK as context for the QA model.
        # This prevents mixing contexts from different museums.
        sorted_docs = sorted(docs_and_scores, key=lambda x: x[1])
        best_chunk = sorted_docs[0][0].page_content.strip()
        best_score = sorted_docs[0][1]

        # Run extractive QA on this one focused chunk
        result = qa_extractor(question=query, context=best_chunk)
        qa_answer = result.get("answer", "").strip()
        qa_score = result.get("score", 0)

        print(f"DEBUG: chunk_dist={best_score:.3f}, qa_score={qa_score:.4f}, answer='{qa_answer[:70]}'")

        # Multilingual guide greeting
        intro = {
            "en": "Great question! Here is what our museum records say:\n\n",
            "fr": "Bonne question ! Voici ce que disent nos archives du musee :\n\n",
            "rw": "Ikibazo cyiza! Dore ibyo inyandiko z'inzu ndangamurage zivuga:\n\n",
        }.get(language, "Great question! Here is what our museum records say:\n\n")

        # Multilingual follow-up prompt
        suggestions = {
            "en": (
                "\n\n\U0001f4a1 *Would you like to know more? You can ask me about:*\n"
                "- The history and significance of this artifact\n"
                "- Other artifacts in this museum\n"
                "- Related cultural traditions"
            ),
            "fr": (
                "\n\n\U0001f4a1 *Voulez-vous en savoir plus ? Vous pouvez me demander :*\n"
                "- L'histoire et la signification de cet artefact\n"
                "- D'autres artefacts dans ce musee\n"
                "- Les traditions culturelles associees"
            ),
            "rw": (
                "\n\n\U0001f4a1 *Urashaka kumenya ibindi? Ushobora kumbaza:*\n"
                "- Amateka n'akamaro k'iki gikoresho\n"
                "- Ibindi bikoresho ndangamuco muri iyi nzu ndangamurage\n"
                "- Imihango y'umuco ijyanye n'iyi ngingo"
            ),
        }.get(language, "\n\n\U0001f4a1 *Feel free to ask me more about this museum!*")

        # Case 1: QA found a specific answer (even if short, like an artifact name)
        if qa_score > 0.05 and len(qa_answer) > 4:
            # Try to expand to the full enclosing sentence for a richer answer
            sentences = [
                s.strip() for s in best_chunk.replace("\n", " ").split(".")
                if qa_answer.lower() in s.lower() and len(s.strip()) > 30
            ]
            if sentences:
                expanded = sentences[0] + "."
                # If expanding gives a good length, use it
                if len(expanded) > 60:
                    return f"{intro}{expanded}{suggestions}"

            # Fallback: return just the QA answer if sentence expansion failed
            return f"{intro}{qa_answer}{suggestions}"

        # Case 2: QA confidence low — return the entire best-matching section
        # Trim to 800 chars max for readability
        display = best_chunk[:800] + ("..." if len(best_chunk) > 800 else "")
        return f"{intro}{display}{suggestions}"

    except Exception as e:
        return f"I encountered a small error: {str(e)}"
