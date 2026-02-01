from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
import httpx
import os

from app.services.auth_service import get_current_user

router = APIRouter()

# Supabase config
url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_KEY", "")
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}


@router.get("/invoices")
async def get_invoices(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0)
) -> Dict[str, Any]:
    """
    Get invoices for the authenticated user only.
    """
    user_id = current_user.get("user_id")
    
    if not url or not key:
        # Mock data for development
        return {
            "invoices": [
                {
                    "id": "mock_1",
                    "vendor_gstin": "29AABCT1332L1ZH",
                    "invoice_number": "INV-001",
                    "amount": 15000.00,
                    "date": "2026-01-15",
                    "reconciliation_status": "FILED"
                },
                {
                    "id": "mock_2",
                    "vendor_gstin": "27AADCB2230M1ZO",
                    "invoice_number": "INV-002",
                    "amount": 8500.50,
                    "date": "2026-01-20",
                    "reconciliation_status": "NOT_FOUND"
                }
            ],
            "total": 2
        }
    
    try:
        with httpx.Client() as client:
            # Get invoices for this user only
            response = client.get(
                f"{url}/rest/v1/invoices",
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                    "select": "*",
                    "order": "created_at.desc",
                    "limit": limit,
                    "offset": offset
                }
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                invoices = response.json()
                
                # Get count for pagination
                count_response = client.get(
                    f"{url}/rest/v1/invoices",
                    headers={**headers, "Prefer": "count=exact"},
                    params={
                        "user_id": f"eq.{user_id}",
                        "select": "id"
                    }
                )
                
                total = 0
                if "content-range" in count_response.headers:
                    # Parse "0-9/100" format
                    range_header = count_response.headers["content-range"]
                    if "/" in range_header:
                        total = int(range_header.split("/")[1])
                else:
                    total = len(invoices)
                
                return {
                    "invoices": invoices,
                    "total": total
                }
            else:
                print(f"Invoices API Error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail="Failed to fetch invoices")
                
    except httpx.RequestError as e:
        print(f"Invoices API Request Error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")


@router.get("/invoices/summary")
async def get_invoice_summary(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get summary stats for user's invoices.
    """
    user_id = current_user.get("user_id")
    
    if not url or not key:
        # Mock summary for development
        return {
            "total_amount": 23500.50,
            "total_invoices": 2,
            "filed_count": 1,
            "not_found_count": 1,
            "pending_count": 0,
            "itc_recovered": 15000.00,
            "itc_at_risk": 8500.50
        }
    
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{url}/rest/v1/invoices",
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                    "select": "amount,reconciliation_status"
                }
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                invoices = response.json()
                
                total_amount = 0.0
                filed_count = 0
                not_found_count = 0
                pending_count = 0
                itc_recovered = 0.0
                itc_at_risk = 0.0
                
                for inv in invoices:
                    amount = float(inv.get("amount") or 0)
                    total_amount += amount
                    status = inv.get("reconciliation_status", "PENDING")
                    
                    if status == "FILED":
                        filed_count += 1
                        itc_recovered += amount
                    elif status == "NOT_FOUND":
                        not_found_count += 1
                        itc_at_risk += amount
                    else:
                        pending_count += 1
                
                return {
                    "total_amount": round(total_amount, 2),
                    "total_invoices": len(invoices),
                    "filed_count": filed_count,
                    "not_found_count": not_found_count,
                    "pending_count": pending_count,
                    "itc_recovered": round(itc_recovered, 2),
                    "itc_at_risk": round(itc_at_risk, 2)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch summary")
                
    except httpx.RequestError as e:
        print(f"Summary API Request Error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
