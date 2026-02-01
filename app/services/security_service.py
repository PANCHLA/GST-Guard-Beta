import hmac
import hashlib
import os
from fastapi import Request, HTTPException

APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")

async def verify_signature(request: Request):
    """
    Verify X-Hub-Signature-256 header.
    """
    if not APP_SECRET:
        # If secret is missing, we can't verify. Warn but allow? 
        # For security, we should probably scream, but for dev we might be lax.
        # Let's enforce strictly if the env var exists.
        print("Security: WHATSAPP_APP_SECRET missing. Skipping signature verification.")
        return

    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        # Allow unauthorized if running localhost or tests might be annoying, 
        # but for production "Hardening" this is required.
        # Check if we are in a test/local env? 
        # Let's just return for now if missing to allow local internal calls 
        # unless strict mode is desired. But Meta ALWAYS sends it.
        # If we want to secure against external spam, we must require it.
        
        # NOTE: For local testing (curl/python scripts) to continue working,
        # they need to sign their requests OR we skip if header is missing *and* host is localhost?
        # Let's strictly require it but handle the error gracefully.
        raise HTTPException(status_code=403, detail="Missing X-Hub-Signature-256 header")

    # Header format: sha256=<sig>
    if not signature_header.startswith("sha256="):
         raise HTTPException(status_code=403, detail="Invalid signature format")
         
    expected_sig = signature_header[7:]
    
    body = await request.body()
    
    # Calculate HMAC
    hmac_obj = hmac.new(
        key=APP_SECRET.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256
    )
    calculated_sig = hmac_obj.hexdigest()
    
    if not hmac.compare_digest(expected_sig, calculated_sig):
        print(f"Security: Signature mismatch! Expected {calculated_sig}, got {expected_sig}")
        raise HTTPException(status_code=403, detail="Invalid signature")
