"""
Vendor reminder service for GST Guard.
Sends WhatsApp reminders to vendors who haven't filed invoices.
"""
from typing import List, Dict, Any
from app.services.whatsapp_service import send_whatsapp_message
from app.services import messages
import os

WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")


def get_vendors_from_invoices(invoices: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Group invoices by vendor GSTIN and summarize.
    Returns: {gstin: {invoices: [...], total_amount: float, status_counts: {...}}}
    """
    vendors = {}
    
    for inv in invoices:
        gstin = inv.get("vendor_gstin", "UNKNOWN")
        
        if gstin not in vendors:
            vendors[gstin] = {
                "gstin": gstin,
                "invoices": [],
                "total_amount": 0,
                "filed_count": 0,
                "not_found_count": 0,
                "mismatch_count": 0,
                "needs_reminder": False
            }
        
        vendors[gstin]["invoices"].append(inv)
        vendors[gstin]["total_amount"] += float(inv.get("amount", 0))
        
        status = inv.get("reconciliation_status", "PENDING")
        if status == "FILED":
            vendors[gstin]["filed_count"] += 1
        elif status == "NOT_FOUND":
            vendors[gstin]["not_found_count"] += 1
            vendors[gstin]["needs_reminder"] = True
        elif status == "MISMATCH":
            vendors[gstin]["mismatch_count"] += 1
            vendors[gstin]["needs_reminder"] = True
    
    return vendors


def get_vendors_needing_reminder(invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get list of vendors who have NOT_FOUND or MISMATCH invoices.
    """
    vendors = get_vendors_from_invoices(invoices)
    return [v for v in vendors.values() if v["needs_reminder"]]


# Reminder message templates (bilingual)
REMINDER_MESSAGE_TEMPLATE = """🛡️ *GST Guard - कृपया GSTR-1 में file करें*

नमस्ते,

आपके customer ने निम्नलिखित invoice report किया है जो GSTR-2B में नहीं मिला:

📋 *Invoice Details:*
{invoice_details}

💰 *Total Amount:* ₹{total_amount:,.2f}

कृपया अपने GSTR-1 में इसे file करें ताकि customer को ITC मिल सके।

---
_Hello,_

_Your customer has reported the following invoice(s) not found in GSTR-2B:_

_Please file in your GSTR-1 so your customer can claim ITC._

🙏 धन्यवाद / Thank you"""


def format_invoice_details(invoices: List[Dict[str, Any]]) -> str:
    """Format invoice list for reminder message."""
    lines = []
    for inv in invoices[:5]:  # Limit to 5 invoices per message
        inv_no = inv.get("invoice_number", "N/A")
        date = inv.get("date", "N/A")
        amount = float(inv.get("amount", 0))
        lines.append(f"• {inv_no} | {date} | ₹{amount:,.2f}")
    
    if len(invoices) > 5:
        lines.append(f"... और {len(invoices) - 5} और invoices")
    
    return "\n".join(lines)


def send_vendor_reminder(
    vendor_phone: str,
    vendor_gstin: str,
    invoices: List[Dict[str, Any]],
    phone_number_id: str = None
) -> Dict[str, Any]:
    """
    Send WhatsApp reminder to vendor about unfiled invoices.
    
    Args:
        vendor_phone: Vendor's WhatsApp number (with country code)
        vendor_gstin: Vendor's GSTIN
        invoices: List of invoices that need filing
        phone_number_id: WhatsApp Business phone number ID
    
    Returns:
        {success: bool, message: str}
    """
    if not vendor_phone:
        return {"success": False, "message": "Vendor phone number not provided"}
    
    phone_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID
    
    if not phone_id:
        print(f"Reminder: [MOCK] Would send reminder to {vendor_phone} for GSTIN {vendor_gstin}")
        return {
            "success": True,
            "message": "Reminder logged (dev mode)",
            "mock": True
        }
    
    # Filter only NOT_FOUND/MISMATCH invoices
    pending_invoices = [
        inv for inv in invoices 
        if inv.get("reconciliation_status") in ["NOT_FOUND", "MISMATCH"]
    ]
    
    if not pending_invoices:
        return {"success": False, "message": "No pending invoices for this vendor"}
    
    total = sum(float(inv.get("amount", 0)) for inv in pending_invoices)
    
    message = REMINDER_MESSAGE_TEMPLATE.format(
        invoice_details=format_invoice_details(pending_invoices),
        total_amount=total
    )
    
    result = send_whatsapp_message(vendor_phone, message, phone_id)
    
    if "error" in result:
        return {"success": False, "message": f"WhatsApp error: {result['error']}"}
    
    return {
        "success": True,
        "message": f"Reminder sent to {vendor_phone}",
        "invoices_count": len(pending_invoices),
        "total_amount": total
    }
