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
        print("Initializing RAG Pipeline...")

        from langchain_community.document_loaders import TextLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        # 1. Load museum data
        data_path = os.path.join(os.path.dirname(__file__), "museum_data.txt")
        loader = TextLoader(data_path, encoding="utf-8")
        documents = loader.load()

        # 2. Split into chunks — smaller chunks = more precise retrieval
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " "]
        )
        chunks = splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks.")

        # 3. Try OpenAI, fall back to local
        api_key = os.getenv("OPENAI_API_KEY")
        use_openai_mode = False

        if api_key and api_key.strip():
            try:
                print("Attempting OpenAI mode...")
                from langchain_openai import OpenAIEmbeddings, ChatOpenAI
                embeddings = OpenAIEmbeddings(openai_api_key=api_key)
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=api_key)
                embeddings.embed_query("test")
                use_openai_mode = True
                print("OpenAI initialized successfully.")
            except Exception as e_openai:
                print(f"OpenAI failed ({e_openai}). Falling back to local...")
                use_openai_mode = False

        if not use_openai_mode:
            print("Using local Extractive QA...")
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                from transformers import pipeline as hf_pipeline

                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                qa_extractor = hf_pipeline(
                    "question-answering",
                    model="deepset/roberta-base-squad2"
                )
                print("Local QA model (roberta-base-squad2) loaded.")
            except Exception as e_local:
                print(f"FAILED to load local QA model: {e_local}")
                qa_chain = None
                return

        # 4. Initialize Vector Store with unique collection name and local persistence
        import time
        unique_col = f"museum_{int(time.time())}"
        persist_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
        vector_store = Chroma.from_documents(
            chunks,
            embeddings,
            collection_name=unique_col,
            persist_directory=persist_dir
        )
        print(f"Vector Store ready: collection '{unique_col}' at {persist_dir}")

        retriever = vector_store.as_retriever(search_kwargs={"k": 8})

        if use_openai_mode:
            prompt = ChatPromptTemplate.from_template(
                """You are a professional and friendly Rwanda Museum Guide.
Your goal is to provide insightful and culturally rich stories about Rwandan heritage.

DIRECTIONS:
1. Respond in the language: {language}.
2. Answer ONLY using the information in the Context provided.
3. If the context doesn't contain the answer, say you don't have that detail.
4. Be descriptive, respectful, and engaging.
5. Mention the specific museum or artifact when possible.

Context:
{context}

Visitor Question:
{query}

Your Answer:"""
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
        else:
            qa_chain = "local_extractive"

        print(f"RAG initialized. Mode: {'OpenAI' if use_openai_mode else 'Local Extractive QA'}")

    except Exception as e:
        print(f"ERROR during RAG initialization: {e}")
        qa_chain = None


def get_answer(query: str, language: str = "en") -> str:
    global retriever, qa_chain, vector_store, qa_extractor, use_openai_mode

    if qa_chain is None or retriever is None:
        return "The museum guide system is currently initializing. Please try again in a moment."

    try:
        # Retrieve top 6 closest chunks by semantic similarity
        docs_and_scores = vector_store.similarity_search_with_score(query, k=6)

        if not docs_and_scores:
            return "I'm sorry, I couldn't find any information about that in the museum archives."

        # OpenAI mode: use the full generative chain
        if use_openai_mode:
            response = qa_chain.invoke({"query": query, "language": language})
            return response.strip()

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
