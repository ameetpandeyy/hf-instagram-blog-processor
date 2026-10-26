---
title: Teamo API
emoji: 💬
colorFrom: pink
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

# TeAmo Backend - FastAPI on Hugging Face Spaces

This is the production-ready, cost-optimized FastAPI backend for the **TeAmo** AI Companion mobile and web app.

---

## 🚀 Key Architectural Advantages

1. **Ultra Cost-Effective**:
   - Uses `gemini-2.0-flash` with aggressive token optimization (`~150` max completion tokens).
   - Asynchronous memory extraction every 8–10 messages instead of per turn.
   - Selective fact retrieval (top 3–4 facts only) keeps context windows small and costs at fractions of a cent per 1,000 interactions.

2. **Zero Data Loss (Firebase + Supabase Sync)**:
   - Firebase handles anonymous and federated authentication on clients.
   - Every request validates the Firebase ID token and idempotently syncs the user into Supabase (`users` table).
   - Double-entry ledger (`credit_ledger` table with PostgreSQL atomic RPC `apply_credit_transaction`) guarantees zero balance corruption or race conditions.

3. **Deployable for Free on Hugging Face Spaces**:
   - The included `Dockerfile` conforms directly with Hugging Face Docker Space specs (`PORT 7860`, non-root user `uid 1000`).

---

## 📦 How to Deploy on Hugging Face Spaces

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Set:
   - **Space Name**: `teamo-backend` (or any preferred name).
   - **SDK**: Select **Docker** (Blank).
   - **Hardware**: Free Tier (2 vCPU · 16 GB RAM).
3. Clone or push the `backend/` directory contents to your Hugging Face Space repository:
   ```bash
   cd backend
   git init
   git remote add origin https://huggingface.co/spaces/<your-username>/teamo-backend
   git add .
   git commit -m "Deploy TeAmo FastAPI"
   git push -u origin main
   ```
4. In your Hugging Face Space settings (**Settings > Variables and secrets**), add the following Secrets:
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `SUPABASE_URL`: Your Supabase Project URL.
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase Service Role Secret Key.
   - `FIREBASE_PROJECT_ID`: Your Firebase Project ID (e.g. `teamoaichat`).
5. Your Space will build and expose a live HTTPS API:
   `https://<your-username>-teamo-backend.hf.space`
   - Health check: `https://<your-username>-teamo-backend.hf.space/health`
   - Swagger Docs: `https://<your-username>-teamo-backend.hf.space/docs`
