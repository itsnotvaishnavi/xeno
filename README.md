# Xeno Mini CRM Assignment

A working AI-native mini CRM for reaching shoppers, built as a two-service prototype.

## What it includes

- `backend/crm_service.py` — CRM core service with data ingestion, segmentation, campaign dispatch, and receipt processing.
- `backend/channel_stub.py` — Separate channel simulator service that accepts campaign sends and asynchronously calls back with delivery/engagement events.
- `frontend/index.html` — A lightweight web UI for importing data, defining segments, drafting campaigns, and viewing campaign performance.
- `sample_data.json` — Example customers and orders to seed the CRM.

## Run locally

1. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

2. Start the channel stub:
   ```bash
   python backend/channel_stub.py
   ```

3. Start the CRM service:
   ```bash
   python backend/crm_service.py
   ```

4. Open the app in your browser:
   ```text
   http://127.0.0.1:8000
   ```

## AI-native features

- Optional OpenAI integration via `OPENAI_API_KEY`.
- AI-assisted segment suggestions and message drafting.
- If no API key is configured, the app falls back to an explicit, explainable local recommendation engine.

## Scope choices

- Focused on shopper engagement, not sales or support workflows.
- Stub channel model mirrors real delivery+callback lifecycle.
- Persistent CRM state in SQLite for simple durability.
- Web UI supports audience building, campaign creation, and performance analytics.

## Deployment notes

This prototype is ready to deploy on any container-friendly platform or Python app host. Use a service like Render, Railway, or Fly.io with both services exposed and the frontend served by the CRM backend.
