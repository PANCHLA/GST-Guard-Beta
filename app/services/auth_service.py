import os
import random
import string
import jwt
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_in_production_123!")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24 * 7  # 1 week

# OTP Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5

# Supabase config
url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_KEY", "")
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

security = HTTPBearer(auto_error=False)


def generate_otp() -> str:
    """Generate a random 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def create_jwt_token(user_id: str, phone: str) -> str:
    """Create a JWT token for authenticated user."""
    payload = {
        "user_id": user_id,
        "phone": phone,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# In-memory OTP storage for development/fallback
# Format: {phone: {"code": otp, "expires_at": datetime}}
_otp_memory_store: Dict[str, Dict[str, Any]] = {}


def store_otp(phone: str, otp: str) -> bool:
    """Store OTP. Uses Supabase if available, falls back to in-memory."""
    global _otp_memory_store
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Always store in memory as fallback
    _otp_memory_store[phone] = {
        "code": otp,
        "expires_at": expires_at
    }
    print(f"Auth: [MEMORY] Stored OTP {otp} for {phone}")
    
    if not url or not key:
        return True
    
    # Try Supabase storage
    try:
        with httpx.Client() as client:
            # Delete old OTPs
            client.delete(
                f"{url}/rest/v1/otp_codes",
                headers=headers,
                params={"phone": f"eq.{phone}"}
            )
            
            # Insert new OTP
            payload = {
                "phone": phone,
                "code": otp,
                "expires_at": expires_at.isoformat(),
                "used": False
            }
            response = client.post(
                f"{url}/rest/v1/otp_codes",
                headers=headers,
                json=payload
            )
            if response.status_code in [200, 201]:
                print(f"Auth: [SUPABASE] Stored OTP for {phone}")
                return True
            # Table might not exist - that's okay, we have memory fallback
            print(f"Auth: Supabase store failed ({response.status_code}), using memory fallback")
    except Exception as e:
        print(f"Auth: Supabase error ({e}), using memory fallback")
    
    return True  # Memory fallback is always available


def verify_otp(phone: str, otp: str) -> bool:
    """Verify OTP. Checks in-memory store first, then Supabase."""
    global _otp_memory_store
    
    # Check in-memory store first (always available)
    if phone in _otp_memory_store:
        stored = _otp_memory_store[phone]
        if stored["code"] == otp:
            if stored["expires_at"] > datetime.now(timezone.utc):
                # Remove used OTP
                del _otp_memory_store[phone]
                print(f"Auth: [MEMORY] Verified OTP for {phone}")
                return True
            else:
                print(f"Auth: [MEMORY] OTP expired for {phone}")
                del _otp_memory_store[phone]
                return False
    
    # Fallback to Supabase if configured
    if not url or not key:
        print(f"Auth: [MOCK] No OTP found for {phone}")
        return False
    
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{url}/rest/v1/otp_codes",
                headers=headers,
                params={
                    "phone": f"eq.{phone}",
                    "code": f"eq.{otp}",
                    "used": "eq.false",
                    "select": "*"
                }
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                data = response.json()
                if data and len(data) > 0:
                    record = data[0]
                    expires_at = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
                    
                    if expires_at > datetime.now(timezone.utc):
                        # Mark OTP as used
                        client.patch(
                            f"{url}/rest/v1/otp_codes",
                            headers=headers,
                            params={"id": f"eq.{record['id']}"},
                            json={"used": True}
                        )
                        print(f"Auth: [SUPABASE] Verified OTP for {phone}")
                        return True
                    else:
                        print(f"Auth: OTP expired for {phone}")
    except Exception as e:
        print(f"Auth: Error verifying OTP: {e}")
    
    return False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Dependency to get current authenticated user from JWT."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = verify_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "user_id": payload.get("user_id"),
        "phone": payload.get("phone")
    }


def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Optional[Dict[str, Any]]:
    """Optional auth - returns None if not authenticated."""
    if not credentials:
        return None
    
    payload = verify_jwt_token(credentials.credentials)
    return {
        "user_id": payload.get("user_id"),
        "phone": payload.get("phone")
    } if payload else None
