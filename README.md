# Rwanda Museum Interactive Guide — Multilingual RAG Chatbot

**Amandine Irakoze** · BSc. Software Engineering Capstone · African Leadership University (ALU)  
**Supervisor:** Thadee Gatera

I built a visitor-facing **React (Vite)** app and a **Flask** backend that runs **retrieval-augmented generation (RAG)** over museum text I curated in **ChromaDB**, with optional **Google Gemini** for grounded answers. I also implemented hand-maintained **keyword routes** in `app.py` (`CORE_FACTS`) so frequent questions in English, French, and Kinyarwanda can be answered without calling the LLM.

**Live site:** [https://rwanda-museums-chatbot.vercel.app/](https://rwanda-museums-chatbot.vercel.app/)  
**My repository:** [https://github.com/Amandine0610/Rwanda_museums_chatbot](https://github.com/Amandine0610/Rwanda_museums_chatbot)

I present my full argument, literature review, methods, and evaluation in my **submitted capstone report (PDF)**. This README is my implementation and run guide so assessors can reproduce and inspect my work.

---

## 1. RAG pipeline (my backend)

| Stage | What I implemented |
|--------|-------------------|
| **Corpus** | Eight plain-text files in `knowledge_base/` (one museum each) that I prepared and maintain. |
| **Indexing** | On first run, I chunk the text and embed it with Chroma’s default embedding function (ONNX). |
| **Storage** | **ChromaDB** under `chroma_db/` (local, not in Git; I rebuild or restore it per environment). |
| **Retrieval** | Query embedding and similarity search; I support an optional **museum** filter via `museumId`. |
| **Generation** | **Gemini** receives retrieved passages and instructions I wrote to stay in context and match the visitor’s language. |
| **Curated answers** | **`CORE_FACTS`** in `app.py`: my fixed copy for common intents (hours, location, fees, etc.). |
| **Fallback** | If the API is unavailable, my server can still return material derived from retrieved chunks. |

My frontend sends `query`, `language`, and `museumId` to `/api/chat`; everything above runs on the server.

---

## 2. My design choices

| Decision | Why I chose it | Alternatives I did not use |
|----------|----------------|----------------------------|
| **RAG vs fine-tuning** | I can update museum content by editing files and re-indexing. | Fine-tuning a small corpus risks overfitting and costly retraining when facts change. |
| **ChromaDB + default embeddings** | Straightforward Python integration and persistence; fits the hosting limits I targeted. | Managed vector DBs or larger embedding models would raise cost and resource needs. |
| **Gemini (HTTP API)** | Strong multilingual output; one integration point from Flask. | Other APIs or on-device models are valid trade-offs (cost, latency, operations). |
| **`CORE_FACTS`** | Stable answers for high-frequency questions; less LLM reliance for simple facts. | LLM-only routing would be simpler but less controllable for those intents. |

---

## 3. Scope and limitations (my honest bounds)

- My knowledge base is **small** (eight museum-specific files), not a full national archive or web crawl.
- Any pilot results I report apply only to **my setup and sample**; wider claims would need a larger, designed study.
- My RAG stack and prompts **reduce** the risk of unsupported answers; they do **not** guarantee perfect factual alignment on every query. My **EULA** states that answers are assistive and may be incomplete.
- I put quantitative results in my **report**, with **N**, procedure, and limitations—I do not treat them as population-level claims here.

---

## 4. Evaluation artefact in my repository

I ship a script that checks **intent / routing** into my curated paths (not full end-to-end answer quality):

```bash
# From repository root, after: pip install -r requirements.txt
python scripts/evaluation/evaluate_intent.py
```

I use `scripts/evaluation/intent_test_set.csv`. Optionally: `pip install scikit-learn` for a printed classification report.

End-to-end factual accuracy, engagement, and large-scale hallucination rates would need a separate protocol (e.g. gold Q&A, human raters), which I discuss in my report.

---

## 5. Museums (IDs in my app)

| ID | Museum |
|---:|---|
| 1 | King's Palace Museum (Nyanza) |
| 2 | Ethnographic Museum (Huye) |
| 3 | Museum Ingabo (Kigali) |
| 4 | Campaign Against Genocide Museum |
| 5 | Kandt House Museum |
| 6 | Environment Museum (Karongi) |
| 7 | Kigali Genocide Memorial |
| 8 | Rwanda Art Museum |

---

## 6. My system architecture

```
Visitor (browser)
       |
       v
React/Vite (Vercel)  --POST /api/chat-->  Flask (Railway): app.py
                                                |
                        +-----------------------+-----------------------+
                        |                       |                       |
                        v                       v                       v
                 ChromaDB retrieve      CORE_FACTS match          Gemini REST
                 (museum-scoped)        (hours, location…)        (grounded prompt)
                        |                       |                       |
                        +-----------------------+-------+---------------+
                                                        v
                                                 JSON response
```

---

## 7. Technology stack I used

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, Tailwind CSS, Axios |
| Backend | Python 3.11, Flask, Flask-CORS, Gunicorn |
| Vector store | ChromaDB |
| LLM | Google Gemini (REST; I configure models in `app.py`) |
| Hosting | Vercel (frontend), Railway (backend) |

---

## 8. How to clone, install, and run my project

**Requirements:** Python 3.11+, Node.js 18+, and a **Google AI (Gemini) API key** if you want generative replies (some retrieval-only paths may still run without it).

### Clone my repo

```bash
git clone https://github.com/Amandine0610/Rwanda_museums_chatbot.git
cd Rwanda_museums_chatbot
```

### Backend

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

Set `GOOGLE_API_KEY` in **`ml-service/.env`** or a **`.env` file at the project root** (I load these in `app.py`).

```bash
python app.py
```

Default URL is usually **http://127.0.0.1:8000**. The first run may build `chroma_db/` from `knowledge_base/` and can take several minutes.

### Frontend

```bash
cd frontend
npm install
```

Create **`frontend/.env`** (see my `frontend/.env.example`):

```env
VITE_API_URL=http://127.0.0.1:8000
```

```bash
npm run dev
```

Open the URL shown in the terminal (often **http://localhost:5173**).

### QR admin page

`http://localhost:5173/?admin=qr` — I use this to generate or test per-museum links.

### If something breaks

| Issue | What I check |
|-------|----------------|
| Missing Gemini key | `GOOGLE_API_KEY` or `GEMINI_API_KEY` locally or on Railway; redeploy after changing Railway variables. |
| Slow or empty first reply | Initial Chroma indexing; Railway cold start; disk space. |
| CORS errors | `VITE_API_URL` must match my Flask server’s scheme, host, and port. |

---

## 9. Environment variables I rely on

| Variable | Where | Role |
|----------|--------|------|
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | Railway / local `.env` | Gemini API |
| `VITE_API_URL` | Vercel / `frontend/.env` | Backend base URL for my SPA |

I do not commit secrets. `.env` files are in `.gitignore`.

---

## 10. How I organised my repository

```
Rwanda_museums_chatbot/
├── app.py                 # My Flask API, RAG, Chroma, Gemini, CORE_FACTS
├── requirements.txt
├── Procfile
├── runtime.txt
├── railway.toml
├── knowledge_base/        # My museum text sources
├── chroma_db/             # Vector store (gitignored)
├── scripts/evaluation/    # My intent test CSV + evaluate_intent.py
├── frontend/              # My React UI
├── docs/                  # My figures, notebooks, supporting write-ups
├── ml-service/            # Optional alternate RAG service (not required for my main deploy)
└── backend/               # Legacy Node stub (not my production API)
```

---

## 11. What I implemented

- Multilingual UI and prompts: **English, French, Kinyarwanda**
- Museum-scoped retrieval when `museumId` is provided
- QR deep links for context per site
- EULA with browser-stored consent; I disclose use of a third-party model API
- Light / dark theme with persisted preference

---

## 12. What I would extend next

- A larger annotated Q&A set and inter-rater checks on factual grounding
- Experiments on chunk size, top-k, and embedding or model choices
- Additional evaluation metrics from the literature, with clear reporting of uncertainty
- An optional local or self-hosted LLM path for offline or policy-sensitive deployments

---

## 13. Academic integrity and my written report

I developed this project as my BSc. Software Engineering Capstone at ALU. My **signed PDF report** is the authoritative document for **citations, figures, evaluation narrative, and my supervisor’s approval**. Please read this README together with that report and my repository when you assess my work.

---

*Supervisor: Thadee Gatera. My final report includes student and supervisor signatures as required by the programme.*
