import os
import httpx
from typing import Optional, Dict, Any, List

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_KEY", "")

# Headers for Supabase REST API
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def get_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user by WhatsApp phone number using Supabase Rest API.
    """
    if not url or not key or "your_supabase_url" in url:
        # Mock Logic for Testing
        if phone == "9199999999":
            return {"id": "mock_existing_user", "whatsapp_phone_number": phone}
        print(f"DB: [MOCK] Checking user for {phone} -> Not Found")
        return None

    try:
        # GET /rest/v1/users?whatsapp_phone_number=eq.val&select=*
        with httpx.Client() as client:
            response = client.get(
                f"{url}/rest/v1/users", 
                headers=headers, 
                params={"whatsapp_phone_number": f"eq.{phone}", "select": "*"}
            )
            # Check for success
            if response.status_code >= 200 and response.status_code < 300:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0]
            else:
                print(f"DB Error response: {response.text}")
    except Exception as e:
        print(f"DB Error: {e}")
    return None

def create_user(phone: str, business_name: str = None, gstin: str = None) -> Dict[str, Any]:
    """
    Create a new user.
    """
    if not url or not key or "your_supabase_url" in url:
        print(f"DB: [MOCK] Creating user {phone}")
        return {"id": "mock_user_id", "whatsapp_phone_number": phone}
        
    payload = {"whatsapp_phone_number": phone, "business_name": business_name, "gstin": gstin}
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{url}/rest/v1/users",
                headers=headers,
                json=payload
            )
            if response.status_code >= 200 and response.status_code < 300:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0]
    except Exception as e:
        print(f"DB Error: {e}")
    return {}

def save_invoice(user_id: str, data: Dict[str, Any], image_url: str):
    """
    Save invoice data.
    """
    if not url or not key or "your_supabase_url" in url:
        print(f"DB: [MOCK] Saved invoice for {user_id}: {data}")
        return

    payload = {
        "user_id": user_id,
        "vendor_gstin": data.get("vendor_gstin"),
        "invoice_number": data.get("invoice_number"),
        "amount": data.get("amount"),
        "date": data.get("date"),
        "image_url": image_url,
        "reconciliation_status": data.get("reconciliation_status", "PENDING")
    }
    try:
         with httpx.Client() as client:
            response = client.post(
                f"{url}/rest/v1/invoices",
                headers=headers,
                json=payload
            )
            if response.status_code not in [200, 201]:
                print(f"DB Error (Save Invoice): {response.status_code} - {response.text}")
    except Exception as e:
        print(f"DB Error: {e}")

def check_invoice_exists(vendor_gstin: str, invoice_number: str) -> bool:
    """
    Check if an invoice with the same Vendor GSTIN and Invoice Number already exists.
    """
    if not url or not key or "your_supabase_url" in url:
        return False # Mock mode assumption
    
    # If AI failed to extract them, we can't check duplicates properly.
    if not vendor_gstin or not invoice_number or vendor_gstin == "ERROR":
        return False

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{url}/rest/v1/invoices",
                headers=headers,
                params={
                    "vendor_gstin": f"eq.{vendor_gstin}",
                    "invoice_number": f"eq.{invoice_number}",
                    "select": "id"
                }
            )
            if response.status_code >= 200 and response.status_code < 300:
                data = response.json()
                if data and len(data) > 0:
                    return True
    except Exception as e:
        print(f"DB Error checking duplicate: {e}")
    return False


def update_user(user_id: str, gstin: str = None, business_name: str = None) -> bool:
    """
    Update user profile with GSTIN and business name from certificate.
    """
    if not url or not key or "your_supabase_url" in url:
        print(f"DB: [MOCK] Updated user {user_id} with GSTIN={gstin}, business={business_name}")
        return True
    
    updates = {}
    if gstin:
        updates["gstin"] = gstin
    if business_name:
        updates["business_name"] = business_name
    
    if not updates:
        return False
    
    try:
        with httpx.Client() as client:
            response = client.patch(
                f"{url}/rest/v1/users",
                headers=headers,
                params={"id": f"eq.{user_id}"},
                json=updates
            )
            if response.status_code >= 200 and response.status_code < 300:
                print(f"DB: Updated user {user_id}")
                return True
            else:
                print(f"DB Error updating user: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"DB Error: {e}")
    return False


def update_user_language(user_id: str, language: str) -> bool:
    """
    Update user's preferred language (hi or en).
    """
    if language not in ["hi", "en"]:
        language = "en"
        
    if not url or not key or "your_supabase_url" in url:
        print(f"DB: [MOCK] Updated user {user_id} language to {language}")
        return True
    
    try:
        with httpx.Client() as client:
            response = client.patch(
                f"{url}/rest/v1/users",
                headers=headers,
                params={"id": f"eq.{user_id}"},
                json={"preferred_language": language}
            )
            if response.status_code >= 200 and response.status_code < 300:
                print(f"DB: Updated user {user_id} language to {language}")
                return True
    except Exception as e:
        print(f"DB Error: {e}")
    return False
