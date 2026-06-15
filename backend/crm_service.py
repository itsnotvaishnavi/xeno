import json
import os
from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests

from backend import ai_helpers, database

app = FastAPI(title="Xeno Mini CRM")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend")), name="static")

CHANNEL_SERVICE_URL = os.environ.get("CHANNEL_SERVICE_URL", "http://127.0.0.1:8001")
CRM_CALLBACK_URL = os.environ.get("CRM_CALLBACK_URL", "http://127.0.0.1:8000/api/callback")


class ImportPayload(BaseModel):
    customers: list[dict]
    orders: list[dict]


class SegmentPayload(BaseModel):
    name: str
    criteria: dict


class CampaignPayload(BaseModel):
    name: str
    segment_id: int
    channel: str
    subject: str | None = None
    body: str


class AISegmentPayload(BaseModel):
    goal: str


class AIMessagePayload(BaseModel):
    brand: str
    goal: str
    channel: str


@app.get("/")
async def app_home():
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(html_path, "r", encoding="utf-8") as handle:
        return Response(content=handle.read(), media_type="text/html")


@app.post("/api/import-data")
async def import_data(payload: ImportPayload):
    for customer in payload.customers:
        database.insert_customer(customer)
    for order in payload.orders:
        database.insert_order(order)
    return {"status": "ok", "customers": len(payload.customers), "orders": len(payload.orders)}


@app.get("/api/customers")
async def customers():
    return database.query_customers()


@app.get("/api/orders")
async def orders():
    return database.query_orders()


@app.post("/api/segments")
async def create_segment(payload: SegmentPayload):
    segment_id = database.create_segment(payload.name, payload.criteria)
    return {"id": segment_id, "name": payload.name, "criteria": payload.criteria}


@app.get("/api/segments")
async def list_segments():
    return database.list_segments()


@app.post("/api/campaigns")
async def create_campaign(payload: CampaignPayload, background_tasks: BackgroundTasks):
    segment_criteria = database.get_segment_criteria(payload.segment_id)
    if not segment_criteria:
        return Response(content="Segment not found", status_code=404)

    campaign_id = database.create_campaign(payload.name, payload.segment_id, payload.channel, payload.subject, payload.body)
    customers = database.customer_segment_ids(segment_criteria)
    communications = []
    for customer_id in customers:
        message = payload.body.replace("{name}", database.get_customer_by_id(customer_id)["name"])
        comm_id = database.create_communication(campaign_id, customer_id, payload.channel, message)
        communications.append(comm_id)
        background_tasks.add_task(send_message_to_channel, comm_id, customer_id, payload.channel, message)

    return {"campaign_id": campaign_id, "recipient_count": len(customers), "communication_ids": communications}


def send_message_to_channel(communication_id: int, customer_id: int, channel: str, message: str) -> None:
    customer = database.get_customer_by_id(customer_id)
    payload = {
        "communication_id": communication_id,
        "customer_id": customer_id,
        "recipient": {
            "name": customer["name"],
            "email": customer["email"],
            "phone": customer["phone"],
        },
        "channel": channel,
        "message": message,
        "callback_url": CRM_CALLBACK_URL,
    }
    try:
        requests.post(f"{CHANNEL_SERVICE_URL}/send", json=payload, timeout=5)
    except requests.RequestException:
        database.update_communication_status(communication_id, "failed", "channel_unreachable")


@app.post("/api/callback")
async def receive_callback(request: Request):
    body = await request.json()
    communication_id = body.get("communication_id")
    event = body.get("event")
    outcome = body.get("outcome")
    if not communication_id or not event:
        return Response(content="Invalid callback", status_code=400)

    if event == "delivered":
        database.update_communication_status(communication_id, "delivered", outcome)
    elif event in {"opened", "clicked", "converted"}:
        database.update_communication_status(communication_id, event, outcome)
    else:
        database.update_communication_status(communication_id, "failed", outcome)

    return {"status": "received", "communication_id": communication_id}


@app.get("/api/campaigns")
async def campaigns():
    campaigns = database.list_campaigns()
    output = []
    for campaign in campaigns:
        metrics = database.campaign_metrics(campaign["id"])
        output.append({**campaign, "metrics": metrics})
    return output


@app.get("/api/communications")
async def communications(campaign_id: int | None = None):
    return database.list_communications(campaign_id)


@app.post("/api/ai/suggest-segment")
async def suggest_segment(payload: AISegmentPayload):
    customers = database.query_customers()
    suggestion = ai_helpers.suggest_segment(payload.goal, customers)
    return suggestion


@app.post("/api/ai/draft-message")
async def draft_message(payload: AIMessagePayload):
    return ai_helpers.draft_message(payload.brand, payload.goal, payload.channel)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
