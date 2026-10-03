import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
from backend.config import settings
from backend.database import SessionLocal, Transaction, TransactionEvent, Complaint, HistoricalCase, init_db

# Deterministic seed for reproducible evaluation
random.seed(42)

SCENARIOS = {
    "SUCCESS": {
        "weight": 0.50,
        "wallet_debited": True,
        "merchant_received": True,
        "reversal_found": False,
        "merchant_ack": True,
        "failure_code": "NONE",
        "status": "SUCCESS",
        "description": "Standard successful payment without any failure."
    },
    "MERCHANT_ACK_FAILURE": {
        "weight": 0.10,
        "wallet_debited": True,
        "merchant_received": False,
        "reversal_found": False,
        "merchant_ack": False,
        "failure_code": "MRC_TIMEOUT",
        "status": "FAILED",
        "description": "Customer wallet was debited but merchant gateway failed to send ACK."
    },
    "MISSING_REVERSAL": {
        "weight": 0.09,
        "wallet_debited": True,
        "merchant_received": False,
        "reversal_found": False,
        "merchant_ack": False,
        "failure_code": "REV_NOT_TRIGGERED",
        "status": "FAILED",
        "description": "Transaction failed at downstream gateway but automatic auto-reversal job failed."
    },
    "STATUS_SYNC_DELAY": {
        "weight": 0.08,
        "wallet_debited": True,
        "merchant_received": True,
        "reversal_found": False,
        "merchant_ack": True,
        "failure_code": "SYNC_LAG",
        "status": "PENDING",
        "description": "Merchant already received funds, but app/core wallet state cache has not updated."
    },
    "DUPLICATE_TRANSACTION": {
        "weight": 0.06,
        "wallet_debited": True,
        "merchant_received": True,
        "reversal_found": False,
        "merchant_ack": True,
        "failure_code": "DUP_IDEMPOTENCY_ERR",
        "status": "SUCCESS",
        "description": "User clicked multiple times or network retry caused double debit for same order."
    },
    "NETWORK_TIMEOUT": {
        "weight": 0.07,
        "wallet_debited": False,
        "merchant_received": False,
        "reversal_found": False,
        "merchant_ack": False,
        "failure_code": "NET_GATEWAY_TIMEOUT",
        "status": "FAILED",
        "description": "Network dropped before transaction could reach core debit ledger."
    },
    "INSUFFICIENT_BALANCE": {
        "weight": 0.04,
        "wallet_debited": False,
        "merchant_received": False,
        "reversal_found": False,
        "merchant_ack": False,
        "failure_code": "BAL_INSUFFICIENT",
        "status": "FAILED",
        "description": "Transaction rejected during balance validation stage."
    },
    "SUSPICIOUS_ACTIVITY": {
        "weight": 0.03,
        "wallet_debited": True,
        "merchant_received": False,
        "reversal_found": False,
        "merchant_ack": False,
        "failure_code": "RISK_VELOCITY_BREACH",
        "status": "FAILED",
        "description": "Multiple high-frequency micro/macro transactions triggered velocity risk alert."
    },
    "UNKNOWN_FAILURE": {
        "weight": 0.03,
        "wallet_debited": False,
        "merchant_received": False,
        "reversal_found": False,
        "merchant_ack": False,
        "failure_code": "ERR_UNKNOWN_999",
        "status": "FAILED",
        "description": "Internal unclassified system error or protocol mismatch."
    }
}

TRANSACTION_TYPES = ["MERCHANT_PAYMENT", "SEND_MONEY", "CASH_OUT", "MOBILE_RECHARGE", "UTILITY_BILL"]

COMPLAINT_TEMPLATES = {
    "MERCHANT_ACK_FAILURE": [
        "Money has been deducted from my account ({amount} BDT) but the shopkeeper didn't receive it.",
        "I scanned QR at merchant {merchant_id} and {amount} taka was cut, but POS machine showed failed.",
        "Taka kete niyeche kintu dokandari pay ni. Amount was {amount} tk at merchant {merchant_id}.",
        "Shop owner said money didn't arrive, but SMS shows {amount} deducted.",
        "Paid {amount} taka at merchant around {time}, merchant claims no payment received."
    ],
    "MISSING_REVERSAL": [
        "Payment of {amount} failed yesterday, message said reversal in 2 hours but still not refunded.",
        "Transaction failed at payment gateway, money deducted from wallet, no reversal received yet.",
        "Amar {amount} taka refund hoy nai. Payment failed hoise kintu taka ferot ashe nai.",
        "Failed transaction of {amount} tk on {time}, reversal missing from my statement.",
        "Customer care promised reversal for {amount} tk within 24 hours, still no refund."
    ],
    "STATUS_SYNC_DELAY": [
        "Merchant says payment succeeded and gave goods, but my app shows status 'PENDING'.",
        "App shows pending for {amount} BDT even though merchant got confirmation SMS.",
        "Why is my transaction still showing pending after 3 hours? Amount {amount} taka.",
        "Status sync issue: money deducted, merchant received, app showing waiting for confirmation."
    ],
    "DUPLICATE_TRANSACTION": [
        "I only made one payment of {amount} taka, but money was deducted TWICE from my account!",
        "Duplicate charge: two debits of {amount} tk within seconds for the same purchase.",
        "Double deduction happened for my merchant bill payment of {amount} taka.",
        "Dui bar taka keteche! Paid once but charged twice {amount} tk at merchant {merchant_id}."
    ],
    "NETWORK_TIMEOUT": [
        "App timed out showing network error while paying {amount} taka.",
        "Internet connection dropped during PIN entry, don't know if money sent.",
        "Network timeout during processing, app closed abruptly.",
        "Connection lost during payment of {amount} tk to merchant {merchant_id}."
    ],
    "INSUFFICIENT_BALANCE": [
        "Transaction was rejected stating insufficient balance, please check my account statement.",
        "Tried to pay {amount} taka, said balance low, but I think I have enough funds.",
        "Why did my payment get cancelled for balance check error?"
    ],
    "SUSPICIOUS_ACTIVITY": [
        "My account is blocked after repeated transaction attempts, please unblock immediately.",
        "Got security warning after attempting multiple payments of {amount} taka.",
        "Suspicious transaction alert triggered on my account, need urgent review."
    ],
    "UNKNOWN_FAILURE": [
        "Payment failed with weird error code ERR_999, what happened to my {amount} taka?",
        "Transaction crashed with unknown server error, please investigate.",
        "System gave unknown error during payment of {amount} taka."
    ],
    "SUCCESS": [
        "Just checking if my payment of {amount} taka went through smoothly to {merchant_id}.",
        "Need transaction receipt for my payment of {amount} BDT.",
        "Want to confirm transaction details for {amount} taka paid earlier."
    ]
}

HISTORICAL_CASES_DATA = [
    {
        "case_code": "HIST-001",
        "title": "Merchant ACK Timeout - Automatic Reconciliation Required",
        "scenario": "MERCHANT_ACK_FAILURE",
        "symptoms": "Wallet debited, merchant gateway failed to send ACK within 15s. Transaction status FAILED.",
        "root_cause": "MERCHANT_ACK_FAILURE",
        "resolution": "Reconcile with merchant aggregator logs; initiate manual/batch credit reversal to customer wallet.",
        "assigned_team": "Reconciliation"
    },
    {
        "case_code": "HIST-002",
        "title": "Failed Payment with Missing Reversal Job",
        "scenario": "MISSING_REVERSAL",
        "symptoms": "Wallet debited, transaction terminated with REV_NOT_TRIGGERED, no reversal credit event found after 30 min.",
        "root_cause": "MISSING_REVERSAL",
        "resolution": "Trigger immediate manual reversal via Core Ledger Admin; credit disputed amount back to customer.",
        "assigned_team": "Reconciliation"
    },
    {
        "case_code": "HIST-003",
        "title": "Merchant Received but App State Pending",
        "scenario": "STATUS_SYNC_DELAY",
        "symptoms": "Merchant received funds, gateway marked SUCCESS, but app state cache remained in PENDING status.",
        "root_cause": "STATUS_SYNC_DELAY",
        "resolution": "Invalidate transaction cache in Redis cluster; force push status sync webhook to customer app.",
        "assigned_team": "Network & Core Banking"
    },
    {
        "case_code": "HIST-004",
        "title": "Duplicate Rapid Payment Idempotency Failure",
        "scenario": "DUPLICATE_TRANSACTION",
        "symptoms": "Two debit events with identical amount within 3 seconds; merchant received duplicate credit.",
        "root_cause": "DUPLICATE_TRANSACTION",
        "resolution": "Initiate duplicate chargeback against merchant settlement pool; refund duplicate debit to customer.",
        "assigned_team": "Merchant Operations"
    },
    {
        "case_code": "HIST-005",
        "title": "Gateway Network Drop Before Core Ledger",
        "scenario": "NETWORK_TIMEOUT",
        "symptoms": "Network gateway timed out at 15s, no wallet debit event, no merchant notification.",
        "root_cause": "NETWORK_TIMEOUT",
        "resolution": "Confirm no ledger debit occurred; inform customer that transaction was never processed and balance is safe.",
        "assigned_team": "Customer Care Tier 2"
    },
    {
        "case_code": "HIST-006",
        "title": "Insufficient Account Balance at Authorization",
        "scenario": "INSUFFICIENT_BALANCE",
        "symptoms": "Transaction rejected during balance check step; zero funds deducted.",
        "root_cause": "INSUFFICIENT_BALANCE",
        "resolution": "Advise customer on current available balance and applicable cash-out/VAT fees.",
        "assigned_team": "Customer Care Tier 2"
    },
    {
        "case_code": "HIST-007",
        "title": "High Velocity Transaction Pattern",
        "scenario": "SUSPICIOUS_ACTIVITY",
        "symptoms": "More than 6 transactions in 2 minutes or abnormal high value outside customer behavior curve.",
        "root_cause": "SUSPICIOUS_ACTIVITY",
        "resolution": "Escalate to Fraud & Risk Unit for KYC verification and temporary safety hold review.",
        "assigned_team": "Fraud & Security"
    },
    {
        "case_code": "HIST-008",
        "title": "Core Gateway Unmapped Protocol Error",
        "scenario": "UNKNOWN_FAILURE",
        "symptoms": "Gateway threw ERR_UNKNOWN_999 without explicit ledger reason.",
        "root_cause": "UNKNOWN_FAILURE",
        "resolution": "Assign to Core Systems Engineering for log trace audit and patch validation.",
        "assigned_team": "Network & Core Banking"
    }
]


def generate_event_timeline(tx_id: str, scenario: str, base_time: datetime, amount: float) -> Tuple[List[Dict], datetime]:
    """Generates a realistic chronological event timeline for a given failure/success scenario."""
    events = []
    curr_time = base_time

    # Step 1: PAYMENT_INITIATED (Always happens)
    events.append({
        "transaction_id": tx_id,
        "event_type": "PAYMENT_INITIATED",
        "event_status": "SUCCESS",
        "timestamp": curr_time,
        "metadata_json": json.dumps({"channel": "APP_QR", "amount": amount})
    })

    if scenario == "INSUFFICIENT_BALANCE":
        curr_time += timedelta(seconds=random.randint(1, 2))
        events.append({
            "transaction_id": tx_id,
            "event_type": "BALANCE_CHECK",
            "event_status": "FAILED",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"reason": "INSUFFICIENT_FUNDS", "required": amount})
        })
        events.append({
            "transaction_id": tx_id,
            "event_type": "TRANSACTION_FAILED",
            "event_status": "FAILED",
            "timestamp": curr_time + timedelta(seconds=1),
            "metadata_json": json.dumps({"error": "BAL_INSUFFICIENT"})
        })
        return events, curr_time + timedelta(seconds=1)

    if scenario == "NETWORK_TIMEOUT":
        curr_time += timedelta(seconds=random.randint(10, 15))
        events.append({
            "transaction_id": tx_id,
            "event_type": "GATEWAY_DISPATCH",
            "event_status": "FAILED",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"error": "NET_GATEWAY_TIMEOUT", "duration_ms": 15200})
        })
        events.append({
            "transaction_id": tx_id,
            "event_type": "TRANSACTION_FAILED",
            "event_status": "FAILED",
            "timestamp": curr_time + timedelta(seconds=1),
            "metadata_json": json.dumps({"error": "NETWORK_TIMEOUT"})
        })
        return events, curr_time + timedelta(seconds=1)

    # Step 2: WALLET_DEBITED
    curr_time += timedelta(seconds=random.randint(1, 2))
    events.append({
        "transaction_id": tx_id,
        "event_type": "WALLET_DEBITED",
        "event_status": "SUCCESS",
        "timestamp": curr_time,
        "metadata_json": json.dumps({"ledger": "CORE_DEBIT", "amount": amount})
    })

    if scenario == "SUSPICIOUS_ACTIVITY":
        curr_time += timedelta(seconds=1)
        events.append({
            "transaction_id": tx_id,
            "event_type": "SECURITY_ALERT",
            "event_status": "FAILED",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"rule": "VELOCITY_THRESHOLD_EXCEEDED", "risk_score": 0.94})
        })
        events.append({
            "transaction_id": tx_id,
            "event_type": "TRANSACTION_FAILED",
            "event_status": "FAILED",
            "timestamp": curr_time + timedelta(seconds=1),
            "metadata_json": json.dumps({"error": "RISK_VELOCITY_BREACH"})
        })
        return events, curr_time + timedelta(seconds=1)

    # Step 3: MERCHANT_NOTIFIED
    curr_time += timedelta(seconds=random.randint(1, 3))
    events.append({
        "transaction_id": tx_id,
        "event_type": "MERCHANT_NOTIFIED",
        "event_status": "SUCCESS",
        "timestamp": curr_time,
        "metadata_json": json.dumps({"gateway": "AGGREGATOR_v2"})
    })

    if scenario == "MERCHANT_ACK_FAILURE":
        curr_time += timedelta(seconds=random.randint(12, 18))
        events.append({
            "transaction_id": tx_id,
            "event_type": "MERCHANT_ACK_TIMEOUT",
            "event_status": "FAILED",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"error": "MRC_TIMEOUT", "timeout_sec": 15})
        })
        events.append({
            "transaction_id": tx_id,
            "event_type": "TRANSACTION_FAILED",
            "event_status": "FAILED",
            "timestamp": curr_time + timedelta(seconds=1),
            "metadata_json": json.dumps({"failure_code": "MRC_TIMEOUT"})
        })
        return events, curr_time + timedelta(seconds=1)

    if scenario == "MISSING_REVERSAL":
        curr_time += timedelta(seconds=random.randint(10, 15))
        events.append({
            "transaction_id": tx_id,
            "event_type": "MERCHANT_ACK_TIMEOUT",
            "event_status": "FAILED",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"error": "DOWNSTREAM_UNAVAILABLE"})
        })
        curr_time += timedelta(seconds=2)
        events.append({
            "transaction_id": tx_id,
            "event_type": "TRANSACTION_FAILED",
            "event_status": "FAILED",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"failure_code": "REV_NOT_TRIGGERED"})
        })
        curr_time += timedelta(seconds=5)
        events.append({
            "transaction_id": tx_id,
            "event_type": "REVERSAL_FAILED",
            "event_status": "FAILED",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"error": "AUTO_REVERSAL_QUEUE_DROPPED"})
        })
        return events, curr_time

    if scenario == "STATUS_SYNC_DELAY":
        curr_time += timedelta(seconds=random.randint(2, 4))
        events.append({
            "transaction_id": tx_id,
            "event_type": "MERCHANT_ACK_RECEIVED",
            "event_status": "SUCCESS",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"merchant_auth": "AUTH_9981"})
        })
        events.append({
            "transaction_id": tx_id,
            "event_type": "STATUS_SYNC_LAG",
            "event_status": "PENDING",
            "timestamp": curr_time + timedelta(seconds=2),
            "metadata_json": json.dumps({"cache_status": "STALE_CACHE_DELAY"})
        })
        return events, curr_time + timedelta(seconds=2)

    if scenario == "DUPLICATE_TRANSACTION":
        curr_time += timedelta(seconds=1)
        events.append({
            "transaction_id": tx_id,
            "event_type": "DUPLICATE_REQUEST_DETECTED",
            "event_status": "SUCCESS",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"duplicate_seq": 2, "idempotency_key": f"IDEM_{tx_id}"})
        })
        curr_time += timedelta(seconds=2)
        events.append({
            "transaction_id": tx_id,
            "event_type": "MERCHANT_ACK_RECEIVED",
            "event_status": "SUCCESS",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"pos_batch": "DUP_SETTLE"})
        })
        events.append({
            "transaction_id": tx_id,
            "event_type": "TRANSACTION_COMPLETED",
            "event_status": "SUCCESS",
            "timestamp": curr_time + timedelta(seconds=1),
            "metadata_json": json.dumps({"status": "SUCCESS_DUPLICATE"})
        })
        return events, curr_time + timedelta(seconds=1)

    if scenario == "UNKNOWN_FAILURE":
        curr_time += timedelta(seconds=random.randint(3, 6))
        events.append({
            "transaction_id": tx_id,
            "event_type": "SYSTEM_EXCEPTION",
            "event_status": "FAILED",
            "timestamp": curr_time,
            "metadata_json": json.dumps({"code": "ERR_UNKNOWN_999", "layer": "SWITCH"})
        })
        events.append({
            "transaction_id": tx_id,
            "event_type": "TRANSACTION_FAILED",
            "event_status": "FAILED",
            "timestamp": curr_time + timedelta(seconds=1),
            "metadata_json": json.dumps({"failure_code": "ERR_UNKNOWN_999"})
        })
        return events, curr_time + timedelta(seconds=1)

    # Standard SUCCESS
    curr_time += timedelta(seconds=random.randint(1, 3))
    events.append({
        "transaction_id": tx_id,
        "event_type": "MERCHANT_ACK_RECEIVED",
        "event_status": "SUCCESS",
        "timestamp": curr_time,
        "metadata_json": json.dumps({"auth_code": "OK_200"})
    })
    curr_time += timedelta(seconds=1)
    events.append({
        "transaction_id": tx_id,
        "event_type": "TRANSACTION_COMPLETED",
        "event_status": "SUCCESS",
        "timestamp": curr_time,
        "metadata_json": json.dumps({"final_status": "SUCCESS"})
    })
    return events, curr_time


def generate_synthetic_dataset(num_transactions: int = 10000, num_complaints: int = 2000):
    """Generates synthetic dataset and persists both into Database and Data files for ML."""
    init_db()
    db = SessionLocal()

    # Seed Historical Cases first
    existing_cases = db.query(HistoricalCase).count()
    if existing_cases == 0:
        for hc in HISTORICAL_CASES_DATA:
            db_case = HistoricalCase(
                case_code=hc["case_code"],
                title=hc["title"],
                scenario=hc["scenario"],
                symptoms=hc["symptoms"],
                root_cause=hc["root_cause"],
                resolution=hc["resolution"],
                assigned_team=hc["assigned_team"]
            )
            db.add(db_case)
        db.commit()

    scenario_names = list(SCENARIOS.keys())
    scenario_weights = [SCENARIOS[s]["weight"] for s in scenario_names]

    base_time = datetime.now() - timedelta(days=14)
    transactions_data = []
    events_data = []
    complaints_data = []

    # Inject 5 predefined demo cases first!
    demo_specs = [
        # Demo 1: Phase 17 Case 1 - Missing Reversal
        {"id": "TX10082", "cust": "C1024", "merch": "M44", "amt": 2500.0, "scen": "MISSING_REVERSAL", "type": "MERCHANT_PAYMENT"},
        # Demo 2: Phase 17 Case 2 - Successful Transaction
        {"id": "TX10083", "cust": "C2050", "merch": "M12", "amt": 1200.0, "scen": "SUCCESS", "type": "MERCHANT_PAYMENT"},
        # Demo 3: Phase 17 Case 3 - Suspicious Activity Anomaly
        {"id": "TX10084", "cust": "C9999", "merch": "M88", "amt": 75000.0, "scen": "SUSPICIOUS_ACTIVITY", "type": "CASH_OUT"},
        # Demo 4: Merchant ACK Failure
        {"id": "TX10085", "cust": "C3030", "merch": "M44", "amt": 500.0, "scen": "MERCHANT_ACK_FAILURE", "type": "MERCHANT_PAYMENT"},
        # Demo 5: Duplicate Payment
        {"id": "TX10086", "cust": "C4040", "merch": "M31", "amt": 1000.0, "scen": "DUPLICATE_TRANSACTION", "type": "MERCHANT_PAYMENT"}
    ]

    for i, spec in enumerate(demo_specs):
        tx_id = spec["id"]
        scen_info = SCENARIOS[spec["scen"]]
        tx_time = datetime.now() - timedelta(hours=2 + i)
        events, comp_time = generate_event_timeline(tx_id, spec["scen"], tx_time, spec["amt"])

        tx_obj = {
            "transaction_id": tx_id,
            "customer_id": spec["cust"],
            "merchant_id": spec["merch"],
            "amount": spec["amt"],
            "transaction_type": spec["type"],
            "transaction_status": scen_info["status"],
            "failure_code": scen_info["failure_code"],
            "ground_truth_root_cause": spec["scen"],
            "created_at": tx_time,
            "completed_at": comp_time
        }
        transactions_data.append(tx_obj)
        events_data.extend(events)

    # Now generate the rest of transactions
    num_to_gen = num_transactions - len(demo_specs)
    for i in range(num_to_gen):
        tx_id = f"TX{20000 + i}"
        scen_name = random.choices(scenario_names, weights=scenario_weights)[0]
        scen_info = SCENARIOS[scen_name]

        cust_id = f"C{random.randint(100, 2500)}"
        merch_id = f"M{random.randint(10, 200)}" if scen_name != "SEND_MONEY" else None
        amt = round(random.choice([50, 100, 200, 500, 1000, 1500, 2500, 3000, 5000, 8000, 12000]) * (1.0 + random.uniform(-0.1, 0.1)), 2)
        if scen_name == "SUSPICIOUS_ACTIVITY":
            amt = round(random.choice([45000, 60000, 85000, 100000, 120000]), 2)

        tx_type = random.choice(TRANSACTION_TYPES)
        tx_time = base_time + timedelta(seconds=random.randint(0, 14 * 86400))
        events, comp_time = generate_event_timeline(tx_id, scen_name, tx_time, amt)

        transactions_data.append({
            "transaction_id": tx_id,
            "customer_id": cust_id,
            "merchant_id": merch_id,
            "amount": amt,
            "transaction_type": tx_type,
            "transaction_status": scen_info["status"],
            "failure_code": scen_info["failure_code"],
            "ground_truth_root_cause": scen_name,
            "created_at": tx_time,
            "completed_at": comp_time
        })
        events_data.extend(events)

    # Generate Complaints
    # Map scenarios to customer complaints
    # Predefined complaint for Demo Case 1
    complaints_data.append({
        "complaint_id": "CMP-DEMO-001",
        "customer_id": "C1024",
        "transaction_id": "TX10082",
        "complaint_text": "I paid ৳2,500 to the shop around 2:30 PM but they didn't receive it. Money was deducted and no reversal was received.",
        "category": "TRANSACTION_DISPUTE",
        "status": "INVESTIGATING",
        "created_at": datetime.now() - timedelta(hours=1)
    })
    # Predefined complaint for Demo Case 2
    complaints_data.append({
        "complaint_id": "CMP-DEMO-002",
        "customer_id": "C2050",
        "transaction_id": "TX10083",
        "complaint_text": "Can you check my payment of ৳1,200? The merchant was unsure if it went through.",
        "category": "TRANSACTION_DISPUTE",
        "status": "NEW",
        "created_at": datetime.now() - timedelta(minutes=45)
    })
    # Predefined complaint for Demo Case 3
    complaints_data.append({
        "complaint_id": "CMP-DEMO-003",
        "customer_id": "C9999",
        "transaction_id": "TX10084",
        "complaint_text": "My ৳75,000 cash out failed and account seems restricted with security alert! Unblock immediately.",
        "category": "FAILED_PAYMENT",
        "status": "NEW",
        "created_at": datetime.now() - timedelta(minutes=30)
    })

    # Generate remaining complaints
    category_map = {
        "MERCHANT_ACK_FAILURE": "TRANSACTION_DISPUTE",
        "MISSING_REVERSAL": "REFUND",
        "STATUS_SYNC_DELAY": "TRANSACTION_DISPUTE",
        "DUPLICATE_TRANSACTION": "DUPLICATE_PAYMENT",
        "NETWORK_TIMEOUT": "FAILED_PAYMENT",
        "INSUFFICIENT_BALANCE": "ACCOUNT_ISSUE",
        "SUSPICIOUS_ACTIVITY": "ACCOUNT_ISSUE",
        "UNKNOWN_FAILURE": "FAILED_PAYMENT",
        "SUCCESS": "OTHER"
    }

    problem_txs = [tx for tx in transactions_data if tx["ground_truth_root_cause"] != "SUCCESS"]

    for i in range(num_complaints - len(complaints_data)):
        target_tx = random.choice(problem_txs)
        scen = target_tx["ground_truth_root_cause"]
        template = random.choice(COMPLAINT_TEMPLATES[scen])
        time_str = target_tx["created_at"].strftime("%H:%M")
        merch_str = target_tx["merchant_id"] or "the merchant"

        complaint_text = template.format(
            amount=int(target_tx["amount"]),
            merchant_id=merch_str,
            time=time_str
        )

        # 30% of complaints do NOT specify transaction_id explicitly (triggers Phase 8 Transaction Matching!)
        include_tx = random.random() > 0.3

        complaints_data.append({
            "complaint_id": f"CMP-{10000 + i}",
            "customer_id": target_tx["customer_id"],
            "transaction_id": target_tx["transaction_id"] if include_tx else None,
            "complaint_text": complaint_text,
            "category": category_map.get(scen, "TRANSACTION_DISPUTE"),
            "status": random.choice(["NEW", "INVESTIGATING", "RESOLVED"]),
            "created_at": target_tx["created_at"] + timedelta(minutes=random.randint(5, 120))
        })

    # Save to SQLite / Supabase database in batches
    print(f"Persisting {len(transactions_data)} transactions and {len(events_data)} events to database...")
    db.query(Complaint).delete()
    db.query(TransactionEvent).delete()
    db.query(Transaction).delete()
    db.commit()

    # Batch insert transactions
    tx_models = [Transaction(**t) for t in transactions_data]
    db.bulk_save_objects(tx_models)
    db.commit()

    # Batch insert events (in chunks of 10,000 for SQLite memory efficiency)
    chunk_size = 10000
    for idx in range(0, len(events_data), chunk_size):
        chunk = events_data[idx:idx + chunk_size]
        event_models = [TransactionEvent(**e) for e in chunk]
        db.bulk_save_objects(event_models)
        db.commit()

    # Batch insert complaints
    cmp_models = [Complaint(**c) for c in complaints_data]
    db.bulk_save_objects(cmp_models)
    db.commit()
    db.close()

    # Also save CSV files for training models in backend/data/
    df_tx = pd.DataFrame(transactions_data)
    df_events = pd.DataFrame(events_data)
    df_comp = pd.DataFrame(complaints_data)

    df_tx.to_csv(settings.DATA_DIR / "transactions.csv", index=False)
    df_events.to_csv(settings.DATA_DIR / "transaction_events.csv", index=False)
    df_comp.to_csv(settings.DATA_DIR / "complaints.csv", index=False)

    print("Synthetic dataset successfully generated and saved to database & CSV files!")
    return len(transactions_data), len(events_data), len(complaints_data)


if __name__ == "__main__":
    generate_synthetic_dataset(num_transactions=15000, num_complaints=3000)
