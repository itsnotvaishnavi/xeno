import asyncio
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="Xeno Channel Stub")


class SendRequest(BaseModel):
    communication_id: int
    customer_id: int
    recipient: dict
    channel: str
    message: str
    callback_url: str


@app.post("/send")
async def send_message(payload: SendRequest):
    if random.random() < 0.08:
        raise HTTPException(status_code=500, detail="simulated channel failure")

    asyncio.create_task(simulate_delivery(payload.dict()))
    return {"status": "accepted", "communication_id": payload.communication_id}


async def simulate_delivery(message: dict):
    await asyncio.sleep(random.uniform(0.8, 1.7))
    await notify_callback(message, "delivered", "delivered")

    if random.random() < 0.85:
        await asyncio.sleep(random.uniform(1.0, 2.5))
        await notify_callback(message, "opened", "opened")

        if random.random() < 0.55:
            await asyncio.sleep(random.uniform(1.0, 2.0))
            event = "clicked" if random.random() < 0.55 else "opened"
            await notify_callback(message, event, event)

            if random.random() < 0.25:
                await asyncio.sleep(random.uniform(1.0, 2.5))
                await notify_callback(message, "converted", "order_placed")


async def notify_callback(message: dict, event: str, outcome: str):
    callback_payload = {
        "communication_id": message["communication_id"],
        "event": event,
        "outcome": outcome,
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(message["callback_url"], json=callback_payload, timeout=5)
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
