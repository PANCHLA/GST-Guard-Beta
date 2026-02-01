import os
import httpx
import json

WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")

def send_whatsapp_message(to_phone: str, message_body: str, phone_number_id: str):
    """
    Send a text message via WhatsApp Cloud API.
    """
    if not WHATSAPP_API_TOKEN:
        print(f"WhatsApp: [MOCK] Sending to {to_phone}: {message_body}")
        return {"status": "mock_sent"}

    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message_body}
    }
    
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code not in [200, 201]:
            print(f"WhatsApp Error {response.status_code}: {response.text}")
        return response.json()
    except Exception as e:
        print(f"WhatsApp Exception: {e}")
        return {"error": str(e)}
