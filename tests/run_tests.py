import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("Running Tests...")
    
    # 1. Health
    res = client.get("/health")
    assert res.status_code == 200
    print("[PASS] Health Check")

    # 2. Webhook Verify
    res = client.get("/api/webhook?hub.mode=subscribe&hub.verify_token=baba_ji_ki_jai&hub.challenge=12345")
    assert res.text == "12345"
    print("[PASS] Webhook Verify")

    # 3. New User Flow (Registration)
    # Using 9199999999 to register them first
    payload_new = {
        "entry": [{"changes": [{"value": {"messages": [{"from": "9199999999", "type": "text", "text": {"body": "Hi"}}]}}]}]
    }
    res = client.post("/api/webhook", json=payload_new)
    print(f"New User Response: {res.json()}")
    # It might be 'welcome_new_user' (if new) or 'reply_static_help' (if already exists from previous run)
    assert res.json().get("action") in ["welcome_new_user", "reply_static_help"]
    print("[PASS] User Registration Flow")

    # 4. Existing User Flow (Invoice)
    # Using 9199999999 to trigger existing user mock
    payload_invoice = {
        "entry": [{"changes": [{"value": {"messages": [{"from": "9199999999", "type": "image", "image": {"id": "img_123"}}]}}]}]
    }
    res = client.post("/api/webhook", json=payload_invoice)
    print(f"Invoice Response: {res.json()}")
    
    # Update: Now returns 'queued' immediately
    assert res.json().get("status") == "queued"
    assert res.json().get("action") == "invoice_processing_started"
    print("[PASS] Invoice Flow (Async Queued)")

if __name__ == "__main__":
    run_tests()
