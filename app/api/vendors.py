"""
API endpoints for vendor management and reminders.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import httpx
import os

from app.services.auth_service import get_current_user
from app.services.vendor_service import (
    get_vendors_from_invoices,
    get_vendors_needing_reminder,
    send_vendor_reminder
)

router = APIRouter()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}


class ReminderRequest(BaseModel):
    vendor_gstin: str
    vendor_phone: str  # WhatsApp number with country code


@router.get("/vendors")
async def get_vendors(
    current_user: Dict[str, Any] = Depends(get_current_user),
    filter: Optional[str] = Query(default=None, description="Filter: needs_reminder, all")
) -> Dict[str, Any]:
    """
    Get list of vendors grouped by GSTIN with invoice stats.
    """
    user_id = current_user.get("user_id")
    
    if not url or not key:
        # Mock data
        mock_vendors = [
            {
                "gstin": "29AABCT1332L1ZH",
                "invoices": [{"invoice_number": "INV-001", "amount": 15000, "reconciliation_status": "FILED"}],
                "total_amount": 15000,
                "filed_count": 1,
                "not_found_count": 0,
                "mismatch_count": 0,
                "needs_reminder": False
            },
            {
                "gstin": "27AADCB2230M1ZO",
                "invoices": [{"invoice_number": "INV-002", "amount": 8500, "reconciliation_status": "NOT_FOUND"}],
                "total_amount": 8500,
                "filed_count": 0,
                "not_found_count": 1,
                "mismatch_count": 0,
                "needs_reminder": True
            }
        ]
        
        if filter == "needs_reminder":
            mock_vendors = [v for v in mock_vendors if v["needs_reminder"]]
        
        return {
            "vendors": mock_vendors,
            "total": len(mock_vendors)
        }
    
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{url}/rest/v1/invoices",
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                    "select": "*",
                    "order": "created_at.desc"
                }
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                invoices = response.json()
                vendors_dict = get_vendors_from_invoices(invoices)
                vendors_list = list(vendors_dict.values())
                
                if filter == "needs_reminder":
                    vendors_list = [v for v in vendors_list if v["needs_reminder"]]
                
                return {
                    "vendors": vendors_list,
                    "total": len(vendors_list)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch invoices")
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail="Database connection error")


@router.post("/reminders/send")
async def send_reminder(
    request: ReminderRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send WhatsApp reminder to a vendor about unfiled invoices.
    """
    user_id = current_user.get("user_id")
    
    if not url or not key:
        # Mock mode
        return {
            "success": True,
            "message": f"[DEV] Reminder would be sent to {request.vendor_phone} for GSTIN {request.vendor_gstin}",
            "mock": True
        }
    
    try:
        # Get invoices for this vendor
        with httpx.Client() as client:
            response = client.get(
                f"{url}/rest/v1/invoices",
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                    "vendor_gstin": f"eq.{request.vendor_gstin}",
                    "select": "*"
                }
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                invoices = response.json()
                
                if not invoices:
                    raise HTTPException(status_code=404, detail="No invoices found for this vendor")
                
                result = send_vendor_reminder(
                    vendor_phone=request.vendor_phone,
                    vendor_gstin=request.vendor_gstin,
                    invoices=invoices
                )
                
                return result
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch invoices")
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail="Database connection error")
