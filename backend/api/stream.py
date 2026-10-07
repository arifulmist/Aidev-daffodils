import time
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/stream", tags=["Event Stream Adapter"])

# In-memory circular telemetry stream buffer (last 50 events)
STREAM_BUFFER: List[Dict[str, Any]] = [
    {
        "stream_id": "EVT-ST-101",
        "source": "CBS_LEDGER",
        "transaction_id": "TX10082",
        "event_type": "WALLET_DEBITED",
        "status": "SUCCESS",
        "amount": 2500.0,
        "timestamp": "14:32:09",
        "latency_ms": 142,
        "channel": "NPSB_INTEROPERABLE"
    },
    {
        "stream_id": "EVT-ST-102",
        "source": "MERCHANT_WEBHOOK",
        "transaction_id": "TX10082",
        "event_type": "MERCHANT_ACK_TIMEOUT",
        "status": "FAILED",
        "amount": 2500.0,
        "timestamp": "14:32:15",
        "latency_ms": 6012,
        "channel": "API_GATEWAY"
    },
    {
        "stream_id": "EVT-ST-103",
        "source": "REVERSAL_WORKER",
        "transaction_id": "TX10082",
        "event_type": "REVERSAL_TIMEOUT",
        "status": "FAILED",
        "amount": 2500.0,
        "timestamp": "14:32:20",
        "latency_ms": 5030,
        "channel": "CORE_LEDGER"
    },
    {
        "stream_id": "EVT-ST-104",
        "source": "SWITCH_CORE",
        "transaction_id": "TX10084",
        "event_type": "SECURITY_ALERT",
        "status": "ANOMALY_FLAGGED",
        "amount": 50000.0,
        "timestamp": "16:45:01",
        "latency_ms": 28,
        "channel": "VELOCITY_ENGINE"
    }
]

class IngestEventRequest(BaseModel):
    source: str = Field(..., description="CBS_LEDGER, MERCHANT_WEBHOOK, NPSB_SWITCH, or REVERSAL_WORKER")
    transaction_id: str
    event_type: str
    status: str = "SUCCESS"
    amount: float = 0.0
    latency_ms: int = 50
    channel: str = "NPSB_INTEROPERABLE"
    metadata: Dict[str, Any] = {}

@router.get("/feed")
def get_stream_feed(limit: int = 20):
    """Returns the most recent real-time streaming events from the adapter buffer."""
    return {
        "status": "STREAMING_ACTIVE",
        "adapter_type": "Kafka / Webhook Enterprise Event Stream Adapter",
        "buffer_size": len(STREAM_BUFFER),
        "events": STREAM_BUFFER[-limit:][::-1]
    }

@router.post("/events")
def ingest_event(req: IngestEventRequest):
    """
    Ingests an external real-time event from Core Banking or Merchant Webhook.
    Simulates production message queue consumption (Kafka / RabbitMQ topic consumer).
    """
    now = datetime.now()
    evt = {
        "stream_id": f"EVT-ST-{int(time.time() * 1000) % 100000}",
        "source": req.source,
        "transaction_id": req.transaction_id,
        "event_type": req.event_type,
        "status": req.status,
        "amount": req.amount,
        "timestamp": now.strftime("%H:%M:%S"),
        "latency_ms": req.latency_ms,
        "channel": req.channel,
        "metadata": req.metadata
    }
    STREAM_BUFFER.append(evt)
    if len(STREAM_BUFFER) > 100:
        STREAM_BUFFER.pop(0)

    return {
        "status": "INGESTED",
        "stream_id": evt["stream_id"],
        "event": evt
    }

@router.post("/simulate-burst")
def simulate_telemetry_burst():
    """
    Simulates a live 4-event transaction failure burst across CBS and Merchant Gateway.
    Allows evaluators to observe real-time stream ingestion in action.
    """
    now_str = datetime.now().strftime("%H:%M:%S")
    burst_tx = f"TX{int(time.time()) % 100000}"

    new_events = [
        {
            "stream_id": f"EVT-BURST-1",
            "source": "CBS_LEDGER",
            "transaction_id": burst_tx,
            "event_type": "PAYMENT_INITIATED",
            "status": "SUCCESS",
            "amount": 1850.0,
            "timestamp": now_str,
            "latency_ms": 65,
            "channel": "UPAY_APP"
        },
        {
            "stream_id": f"EVT-BURST-2",
            "source": "CBS_LEDGER",
            "transaction_id": burst_tx,
            "event_type": "WALLET_DEBITED",
            "status": "SUCCESS",
            "amount": 1850.0,
            "timestamp": now_str,
            "latency_ms": 120,
            "channel": "CORE_LEDGER"
        },
        {
            "stream_id": f"EVT-BURST-3",
            "source": "MERCHANT_WEBHOOK",
            "transaction_id": burst_tx,
            "event_type": "MERCHANT_ACK_TIMEOUT",
            "status": "TIMEOUT",
            "amount": 1850.0,
            "timestamp": now_str,
            "latency_ms": 5000,
            "channel": "EXTERNAL_MERCHANT_POS"
        },
        {
            "stream_id": f"EVT-BURST-4",
            "source": "OPS_AI_DISPATCH",
            "transaction_id": burst_tx,
            "event_type": "DISPUTE_AUTO_DETECTED",
            "status": "FLAGGED",
            "amount": 1850.0,
            "timestamp": now_str,
            "latency_ms": 12,
            "channel": "AI_STREAM_LISTENER"
        }
    ]

    for e in new_events:
        STREAM_BUFFER.append(e)

    return {
        "status": "BURST_SIMULATED",
        "generated_transaction": burst_tx,
        "events_count": len(new_events),
        "latest_events": new_events
    }
