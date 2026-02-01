"""
Media service for handling WhatsApp images and permanent storage.
- Downloads images from WhatsApp API
- Uploads to Supabase Storage for permanent access
- Returns both base64 for AI and permanent URL for dashboard
"""
import os
import httpx
import base64
import uuid
from typing import Optional, Tuple

WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase Storage bucket name
STORAGE_BUCKET = "invoices"


def get_media_url(media_id: str) -> Optional[str]:
    """
    Get the temporary URL for a media object from WhatsApp API.
    """
    if not WHATSAPP_API_TOKEN:
        return None
        
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}
    
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("url")
    except Exception as e:
        print(f"Media: Error getting URL: {e}")
    return None


def download_media_bytes(media_url: str) -> Optional[bytes]:
    """
    Download media as raw bytes.
    """
    headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}
    
    try:
        with httpx.Client() as client:
            response = client.get(media_url, headers=headers)
            if response.status_code == 200:
                return response.content
    except Exception as e:
        print(f"Media: Error downloading: {e}")
    return None


def download_media_as_base64(media_url: str) -> Optional[str]:
    """
    Download media bytes and convert to Base64 data URI.
    """
    headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}
    
    try:
        with httpx.Client() as client:
            response = client.get(media_url, headers=headers)
            if response.status_code == 200:
                b64_data = base64.b64encode(response.content).decode('utf-8')
                mime_type = response.headers.get("Content-Type", "image/jpeg")
                return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        print(f"Media: Error converting to base64: {e}")
    return None


def upload_to_supabase_storage(image_bytes: bytes, user_id: str, filename: str = None) -> Optional[str]:
    """
    Upload image to Supabase Storage and return permanent public URL.
    
    Args:
        image_bytes: Raw image bytes
        user_id: User ID for organizing files
        filename: Optional filename, auto-generated if not provided
    
    Returns:
        Public URL of uploaded image, or None on failure
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Media: Supabase not configured, skipping upload")
        return None
    
    if not filename:
        filename = f"{uuid.uuid4().hex}.jpg"
    
    # Path: invoices/{user_id}/{filename}
    file_path = f"{user_id}/{filename}"
    
    try:
        with httpx.Client() as client:
            # Supabase Storage upload endpoint
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{file_path}"
            
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "image/jpeg",
                "x-upsert": "true"  # Overwrite if exists
            }
            
            response = client.post(upload_url, headers=headers, content=image_bytes)
            
            if response.status_code in [200, 201]:
                # Return public URL
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{file_path}"
                print(f"Media: Uploaded to {public_url}")
                return public_url
            else:
                print(f"Media: Upload failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Media: Upload error: {e}")
    
    return None


def get_image_base64(media_id: str) -> Optional[str]:
    """
    Orchestrator: ID -> URL -> Base64 (for AI processing)
    """
    if not WHATSAPP_API_TOKEN:
        print("Media: Missing Token. Returning None.")
        return None

    try:
        url = get_media_url(media_id)
        if url:
            return download_media_as_base64(url)
    except Exception as e:
        print(f"Media Download Error: {e}")
    return None


def get_and_store_image(media_id: str, user_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Full pipeline: Download from WhatsApp, upload to Supabase, return both.
    
    Returns:
        (base64_data_uri, permanent_url)
        - base64 for AI processing
        - permanent_url for dashboard display
    """
    if not WHATSAPP_API_TOKEN:
        print("Media: Missing Token.")
        return None, None
    
    try:
        # Get temporary WhatsApp URL
        wa_url = get_media_url(media_id)
        if not wa_url:
            return None, None
        
        # Download bytes
        image_bytes = download_media_bytes(wa_url)
        if not image_bytes:
            return None, None
        
        # Convert to base64 for AI
        b64_data = base64.b64encode(image_bytes).decode('utf-8')
        base64_uri = f"data:image/jpeg;base64,{b64_data}"
        
        # Upload to permanent storage
        permanent_url = upload_to_supabase_storage(image_bytes, user_id, f"{media_id}.jpg")
        
        return base64_uri, permanent_url
        
    except Exception as e:
        print(f"Media Pipeline Error: {e}")
        return None, None


def get_document_bytes(media_id: str) -> Optional[bytes]:
    """
    Download a document (PDF) from WhatsApp API as raw bytes.
    
    Args:
        media_id: WhatsApp media ID for the document
        
    Returns:
        Raw bytes of the document, or None on failure
    """
    if not WHATSAPP_API_TOKEN:
        print("Media: Missing Token for document download")
        return None
    
    try:
        # Get temporary URL
        wa_url = get_media_url(media_id)
        if not wa_url:
            print(f"Media: Could not get URL for document {media_id}")
            return None
        
        # Download bytes
        doc_bytes = download_media_bytes(wa_url)
        if doc_bytes:
            print(f"Media: Downloaded document {media_id} ({len(doc_bytes)} bytes)")
        return doc_bytes
        
    except Exception as e:
        print(f"Media Document Error: {e}")
        return None
