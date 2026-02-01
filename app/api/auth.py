from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from app.db.supabase_client import get_user_by_phone, create_user
from app.services.auth_service import (
    generate_otp, 
    store_otp, 
    verify_otp, 
    create_jwt_token,
    get_current_user
)
from app.services.whatsapp_service import send_whatsapp_message
from app.services import messages
import os

router = APIRouter()

# Phone Number ID for sending OTPs (from Meta Business)
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")


class OTPRequest(BaseModel):
    phone: str  # WhatsApp phone number (with country code, e.g., "919876543210")


class OTPVerify(BaseModel):
    phone: str
    otp: str


@router.post("/auth/request-otp")
async def request_otp(request: OTPRequest):
    """
    Send OTP to user's WhatsApp number for login.
    """
    phone = request.phone.strip()
    
    # Basic validation
    if not phone or len(phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    
    # Generate OTP
    otp = generate_otp()
    
    # Store OTP in database
    if not store_otp(phone, otp):
        raise HTTPException(status_code=500, detail="Failed to store OTP")
    
    # Send OTP via WhatsApp with bilingual message
    otp_msg = messages.otp_message(otp)
    
    if WHATSAPP_PHONE_NUMBER_ID:
        result = send_whatsapp_message(phone, otp_msg, WHATSAPP_PHONE_NUMBER_ID)
        if "error" in result:
            print(f"Auth: WhatsApp OTP send failed: {result}")
            # Don't fail - OTP is stored, user might retry or check logs
    else:
        print(f"Auth: [DEV MODE] OTP for {phone}: {otp}")
    
    return {
        "status": "otp_sent",
        "message": "Check your WhatsApp for the login code",
        # In dev mode, return OTP for testing (remove in production!)
        "dev_otp": otp if not WHATSAPP_PHONE_NUMBER_ID else None
    }


@router.post("/auth/verify-otp")
async def verify_otp_endpoint(request: OTPVerify):
    """
    Verify OTP and return JWT token for authenticated session.
    """
    phone = request.phone.strip()
    otp = request.otp.strip()
    
    if not phone or not otp:
        raise HTTPException(status_code=400, detail="Phone and OTP required")
    
    # Verify OTP
    if not verify_otp(phone, otp):
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    
    # Get or create user
    user = get_user_by_phone(phone)
    if not user:
        user = create_user(phone)
    
    if not user or not user.get("id"):
        raise HTTPException(status_code=500, detail="User creation failed")
    
    # Generate JWT
    token = create_jwt_token(user["id"], phone)
    
    return {
        "status": "authenticated",
        "token": token,
        "user": {
            "id": user["id"],
            "phone": phone,
            "business_name": user.get("business_name"),
            "gstin": user.get("gstin")
        }
    }


@router.get("/auth/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current authenticated user info.
    """
    user = get_user_by_phone(current_user["phone"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["id"],
        "phone": current_user["phone"],
        "business_name": user.get("business_name"),
        "gstin": user.get("gstin")
    }
