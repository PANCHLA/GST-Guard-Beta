"""
PDF Invoice Extraction Service
Extracts invoice data from PDF files using pdfplumber (text extraction)
with regex-based parsing for common Indian invoice formats.
"""
import re
import tempfile
import pdfplumber
from typing import Optional, Dict, Any


def extract_text_from_pdf(pdf_bytes: bytes) -> Optional[str]:
    """
    Extract all text from a PDF file.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        Extracted text or None if extraction fails
    """
    try:
        # Write bytes to temp file (pdfplumber needs file path)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        
        # Extract text from all pages
        full_text = ""
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages[:3]:  # First 3 pages max
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        # Cleanup temp file
        import os
        os.unlink(tmp_path)
        
        return full_text if full_text.strip() else None
        
    except Exception as e:
        print(f"PDF Extract Error: {e}")
        return None


def parse_invoice_from_text(text: str) -> Dict[str, Any]:
    """
    Parse invoice fields from extracted PDF text using regex patterns.
    Works with common Indian invoice formats (Tally, Zoho, Busy, etc.)
    
    Returns:
        {
            "vendor_gstin": "...",
            "invoice_number": "...",
            "date": "...",
            "amount": 0.0
        }
    """
    result = {
        "vendor_gstin": "",
        "invoice_number": "",
        "date": "",
        "amount": 0.0
    }
    
    if not text:
        return result
    
    # Normalize text
    text_upper = text.upper()
    
    # --- GSTIN Pattern ---
    # Format: 2 digits (state) + 10 char PAN + 1 digit + Z + 1 char
    gstin_pattern = r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}[Z]{1}[0-9A-Z]{1}'
    gstin_matches = re.findall(gstin_pattern, text_upper)
    if gstin_matches:
        result["vendor_gstin"] = gstin_matches[0]
    
    # --- Invoice Number Pattern ---
    # Common patterns: INV-123, INV/123, Invoice No: 123, Bill No. 123
    inv_patterns = [
        r'(?:INVOICE\s*(?:NO|NUMBER|#)?[:\s.-]*)([\w/-]+)',
        r'(?:BILL\s*(?:NO|NUMBER|#)?[:\s.-]*)([\w/-]+)',
        r'(?:INV[:\s.-]*)([\w/-]+)',
        r'(?:VOUCHER\s*(?:NO)?[:\s.-]*)([\w/-]+)',
    ]
    for pattern in inv_patterns:
        match = re.search(pattern, text_upper)
        if match:
            result["invoice_number"] = match.group(1).strip()
            break
    
    # --- Date Pattern ---
    # Formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:DATE|DT)[:\s.-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text_upper)
        if match:
            date_str = match.group(1) if pattern.startswith('(') else match.group(1)
            # Convert to YYYY-MM-DD
            result["date"] = normalize_date(date_str)
            break
    
    # --- Total Amount Pattern ---
    # Look for Grand Total, Total Amount, Net Amount
    amount_patterns = [
        r'(?:GRAND\s*TOTAL|TOTAL\s*AMOUNT|NET\s*AMOUNT|TOTAL)[:\s₹Rs.]*([0-9,]+\.?\d*)',
        r'(?:AMOUNT\s*PAYABLE)[:\s₹Rs.]*([0-9,]+\.?\d*)',
        r'[₹][\s]*([0-9,]+\.?\d*)',
    ]
    for pattern in amount_patterns:
        matches = re.findall(pattern, text_upper)
        if matches:
            # Take the largest amount (likely the total)
            amounts = []
            for m in matches:
                try:
                    amt = float(m.replace(',', ''))
                    amounts.append(amt)
                except:
                    pass
            if amounts:
                result["amount"] = max(amounts)
                break
    
    return result


def normalize_date(date_str: str) -> str:
    """Convert DD/MM/YYYY or DD-MM-YYYY to YYYY-MM-DD"""
    try:
        parts = re.split(r'[/-]', date_str)
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = "20" + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except:
        pass
    return date_str


def analyze_pdf_invoice(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Main function: Extract and parse invoice data from PDF.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        Parsed invoice data dict
    """
    text = extract_text_from_pdf(pdf_bytes)
    
    if not text:
        print("PDF: No text extracted (might be scanned/image PDF)")
        return {
            "vendor_gstin": "ERROR",
            "invoice_number": "ERROR",
            "amount": 0.0,
            "date": "",
            "error": "Could not extract text from PDF"
        }
    
    result = parse_invoice_from_text(text)
    
    # Log extraction results
    print(f"PDF Parsed: GSTIN={result['vendor_gstin']}, Inv={result['invoice_number']}, Amt={result['amount']}")
    
    return result
