# 🚀 Technical Deployment & Installation Manual
**Developer**: Amandine Irakoze | **Project**: Rwanda Museum Universal Guide
# 🚀 Technical Deployment Report
**Developer**: Amandine Irakoze | BSc. Software Engineering

In this report, I document the infrastructure and deployment strategy for my Rwandan Museum Chatbot. The system is designed to be highly available, leveraging a microservices architecture across cloud providers.

## 1. System Components
My application consists of three main layers:
- **ML Search Engine**: A Python/Flask RAG pipeline containerized with Docker.
- **Node.js API Gateway**: A proxy server managing cross-origin communication.
- **React Frontend**: A mobile-first Vite application.

## 2. Infrastructure Setup
I utilized **Render** to host the entire ecosystem. Below are the configurations I implemented for each service:

### A. ML Search Engine (Web Service)
I deployed this as a Dockerized web service. To ensure stability on the Render Free Tier (512MB RAM), I implemented a "Lightweight RAG" fallback. If a generative LLM (OpenAI) is unavailable, the system automatically falls back to local semantic search using the `all-MiniLM-L6-v2` model, which fits efficiently within memory limits.

- **Build Command**: Render automatically detects the `Dockerfile`.
- **Environment**: I configured the `OPENAI_API_KEY` in the Render dashboard.

### B. API Gateway (Web Service)
The backend bridge is a Node.js service that handles requests from the frontend and communicates with the ML engine.
- **Variables**: I set `ML_SERVICE_URL` to point to my deployed ML service.
- **Start Command**: `node server.js`

### C. Frontend Interface (Static Site)
My frontend is optimized as a static site for performance.
- **Build Settings**: `npm install && npm run build`
- **Publish Directory**: `dist`
- **Bridge**: I set `VITE_API_URL` to link the UI to my backend.

## 3. Local Development Manual
For my local testing and development process, I use the following commands:

### Python ML Environment
```bash
cd ml-service
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Backend & Frontend
```bash
# Backend
cd backend && npm install && node server.js

# Frontend
cd frontend && npm install && npm run dev
```

## 4. Performance & Scalability Summary
Tested against 5 museum datasets, the system maintains a sub-second response time. By using a modular vector store, I ensured that new museum archives can be indexed and deployed without changing the core application logic.

---

## 🏗️ Dockerization
For portability, I have containerized the ML service. This ensures the environment is identical across all platforms.

```bash
cd ml-service
docker build -t museum-chatbot-ml .
docker run -p 10000:10000 museum-chatbot-ml
```

---
**Technical Note**: The system is designed to handle 5+ museums simultaneously by dynamically updating its vector store context during initialization.
