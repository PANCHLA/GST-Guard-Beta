from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from app.db.supabase_client import get_user_by_phone, create_user, save_invoice, check_invoice_exists, update_user, update_user_language
from app.services.ai_service import analyze_invoice_image, analyze_gst_certificate
from app.services.gst_service import reconcile_invoice
from app.services.whatsapp_service import send_whatsapp_message
from app.services.security_service import verify_signature
from app.services.media_service import get_image_base64, get_document_bytes
from app.services.pdf_service import analyze_pdf_invoice
from app.services import messages

router = APIRouter()

# Default language for new users
DEFAULT_LANG = "en"


def get_user_lang(user: dict) -> str:
    """Get user's preferred language, default to English."""
    return user.get("preferred_language") or DEFAULT_LANG


@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Handle WhatsApp Webhook Verification
    """
    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.verify_token") == "baba_ji_ki_jai":
        return PlainTextResponse(content=request.query_params.get("hub.challenge"), status_code=200)
    return PlainTextResponse(content="Verification failed", status_code=403)


@router.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Incoming WhatsApp Messages
    """
    # 0. SECURITY: Verify Signature
    await verify_signature(request)

    try:
        data = await request.json()
        
        # Structure: entry[0].changes[0].value.messages[0]
        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            
            if "messages" not in value:
                return {"status": "ignored", "reason": "no_messages"}
                
            message = value["messages"][0]
            phone = message["from"]
            msg_type = message["type"]
            
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            
            # 1. Check if user exists
            user = get_user_by_phone(phone)
            
            if not user:
                # NEW USER - Create account
                print(f"Logic: New user detected ({phone}). Creating account.")
                user = create_user(phone)
                lang = DEFAULT_LANG
                
                # Send welcome + ask for certificate
                if phone_number_id:
                    send_whatsapp_message(phone, messages.welcome(lang), phone_number_id)
                    send_whatsapp_message(phone, messages.ask_certificate(lang), phone_number_id)
                
                return {"status": "processed", "action": "welcome_new_user"}
            
            # Get user's language preference
            lang = get_user_lang(user)
            user_gstin = user.get("gstin")
            needs_onboarding = not user_gstin or user_gstin == ""
            
            # 2. Handle language switching commands
            if msg_type == "text":
                text_body = message.get("text", {}).get("body", "").strip().lower()
                
                # Check for language switch commands
                if text_body in ["hindi", "हिंदी", "हिन्दी"]:
                    update_user_language(user["id"], "hi")
                    if phone_number_id:
                        send_whatsapp_message(phone, messages.language_changed("hi"), phone_number_id)
                    return {"status": "processed", "action": "language_changed_hindi"}
                
                elif text_body in ["english", "अंग्रेजी", "eng"]:
                    update_user_language(user["id"], "en")
                    if phone_number_id:
                        send_whatsapp_message(phone, messages.language_changed("en"), phone_number_id)
                    return {"status": "processed", "action": "language_changed_english"}
                
                # If needs onboarding, remind about certificate
                if needs_onboarding:
                    if phone_number_id:
                        send_whatsapp_message(phone, messages.ask_certificate(lang), phone_number_id)
                else:
                    if phone_number_id:
                        send_whatsapp_message(phone, messages.send_photo_only(lang), phone_number_id)
                
                return {"status": "processed", "action": "reply_static_help"}
            
            # 3. Handle image messages
            if msg_type == "image":
                image_id = message["image"].get("id", "unknown_id")
                
                if needs_onboarding:
                    # Process as GST Certificate
                    print(f"Logic: Certificate photo from {phone}. Processing for onboarding.")
                    background_tasks.add_task(
                        process_certificate_async,
                        user["id"],
                        image_id,
                        phone,
                        phone_number_id,
                        lang
                    )
                    return {"status": "queued", "action": "certificate_processing"}
                else:
                    # Process as Invoice
                    print(f"Logic: Image received from {phone}. Queuing invoice processing.")
                    background_tasks.add_task(
                        process_invoice_async, 
                        user["id"], 
                        image_id, 
                        phone, 
                        phone_number_id,
                        lang
                    )
                    return {"status": "queued", "action": "invoice_processing_started"}
            
            # 4. Handle document messages (PDFs)
            elif msg_type == "document":
                doc_info = message.get("document", {})
                doc_id = doc_info.get("id", "unknown_id")
                mime_type = doc_info.get("mime_type", "")
                
                # Only process PDFs
                if "pdf" in mime_type.lower():
                    print(f"Logic: PDF received from {phone}. Queuing PDF processing.")
                    background_tasks.add_task(
                        process_pdf_invoice_async,
                        user["id"],
                        doc_id,
                        phone,
                        phone_number_id,
                        lang
                    )
                    return {"status": "queued", "action": "pdf_processing_started"}
                else:
                    # Non-PDF document - tell user to send PDF or image
                    if phone_number_id:
                        send_whatsapp_message(phone, messages.send_photo_only(lang), phone_number_id)
                    return {"status": "processed", "action": "unsupported_document_type"}
                
        except (KeyError, IndexError) as e:
            return {"status": "error", "message": "Invalid payload format"}

        return {"status": "received"}
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}


async def process_certificate_async(user_id: str, image_id: str, phone: str, phone_number_id: str, lang: str = DEFAULT_LANG):
    """
    Background Task: Process GST Certificate, extract GSTIN, update user profile.
    """
    print(f"Certificate: Processing for {phone}, Image {image_id}")
    try:
        # 1. Download image
        image_base64 = get_image_base64(image_id)
        
        if not image_base64:
            print(f"Certificate: Failed to download image {image_id}")
            if phone_number_id:
                send_whatsapp_message(phone, messages.certificate_error(lang), phone_number_id)
            return
        
        # 2. Analyze certificate
        cert_data = analyze_gst_certificate(image_base64)
        
        if not cert_data.get("valid"):
            print(f"Certificate: Invalid - {cert_data.get('error')}")
            if phone_number_id:
                send_whatsapp_message(phone, messages.certificate_invalid(lang), phone_number_id)
            return
        
        # 3. Update user profile
        gstin = cert_data.get("gstin", "")
        business_name = cert_data.get("business_name", "")
        
        update_user(user_id, gstin=gstin, business_name=business_name)
        
        # 4. Send success message
        if phone_number_id:
            success_msg = messages.certificate_success(gstin, business_name or "Your Business", lang)
            send_whatsapp_message(phone, success_msg, phone_number_id)
        
        print(f"Certificate: Success for {phone} - GSTIN: {gstin}")
        
    except Exception as e:
        print(f"Certificate Error: {e}")
        if phone_number_id:
            send_whatsapp_message(phone, messages.certificate_error(lang), phone_number_id)


async def process_invoice_async(user_id: str, image_id: str, phone: str, phone_number_id: str, lang: str = DEFAULT_LANG):
    """
    Background Task: Process Invoice, Reconcile, Save, Notify.
    """
    print(f"Background: Starting for {phone}, Image {image_id}")
    try:
        # 1. Download Real Image (Base64)
        image_base64 = get_image_base64(image_id)
        
        if not image_base64:
            print(f"Background: Failed to download image {image_id}")
            if phone_number_id:
                send_whatsapp_message(phone, messages.error_download(lang), phone_number_id)
            return

        # 2. Analyze using AI Service
        invoice_data = analyze_invoice_image(image_base64)
        
        # DUPLICATE CHECK
        vendor_gstin = invoice_data.get("vendor_gstin")
        invoice_number = invoice_data.get("invoice_number")
        
        if check_invoice_exists(vendor_gstin, invoice_number):
            print(f"Background: Duplicate detected for {vendor_gstin} - {invoice_number}")
            if phone_number_id:
                send_whatsapp_message(
                    phone, 
                    messages.duplicate_invoice(invoice_number, vendor_gstin, lang), 
                    phone_number_id
                )
            return

        # Reconcile with GST Portal
        final_data = reconcile_invoice(invoice_data)
        
        # Save to DB
        stored_image_ref = f"whatsapp_media_id:{image_id}"
        save_invoice(user_id, final_data, stored_image_ref)
        
        # Reply to User
        if phone_number_id:
            reply_msg = messages.invoice_processed(
                vendor_gstin=final_data.get('vendor_gstin', 'N/A'),
                invoice_number=final_data.get('invoice_number', 'N/A'),
                amount=float(final_data.get('amount', 0)),
                status=final_data.get('reconciliation_status', 'PENDING'),
                lang=lang,
                notes=final_data.get('notes', '')
            )
            send_whatsapp_message(phone, reply_msg, phone_number_id)
            
        print(f"Background: Finished for {phone}. Status: {final_data.get('reconciliation_status')}")
    except Exception as e:
        print(f"Background Error: {e}")
        if phone_number_id:
            send_whatsapp_message(phone, messages.error_generic(lang), phone_number_id)


async def process_pdf_invoice_async(user_id: str, doc_id: str, phone: str, phone_number_id: str, lang: str = DEFAULT_LANG):
    """
    Background Task: Process PDF invoice, extract data, reconcile, save.
    """
    print(f"PDF Background: Starting for {phone}, Doc {doc_id}")
    try:
        # 1. Download PDF
        pdf_bytes = get_document_bytes(doc_id)
        
        if not pdf_bytes:
            print(f"PDF Background: Failed to download {doc_id}")
            if phone_number_id:
                send_whatsapp_message(phone, messages.error_download(lang), phone_number_id)
            return
        
        # 2. Extract data using PDF service
        invoice_data = analyze_pdf_invoice(pdf_bytes)
        
        # Check for extraction errors
        if invoice_data.get("vendor_gstin") == "ERROR" or invoice_data.get("error"):
            print(f"PDF Background: Extraction failed - {invoice_data.get('error')}")
            # PDF might be scanned - tell user to send image instead
            if phone_number_id:
                send_whatsapp_message(phone, messages.send_photo_only(lang), phone_number_id)
            return
        
        # DUPLICATE CHECK
        vendor_gstin = invoice_data.get("vendor_gstin")
        invoice_number = invoice_data.get("invoice_number")
        
        if check_invoice_exists(vendor_gstin, invoice_number):
            print(f"PDF Background: Duplicate detected for {vendor_gstin} - {invoice_number}")
            if phone_number_id:
                send_whatsapp_message(
                    phone, 
                    messages.duplicate_invoice(invoice_number, vendor_gstin, lang), 
                    phone_number_id
                )
            return
        
        # Reconcile with GST Portal
        final_data = reconcile_invoice(invoice_data)
        
        # Save to DB
        stored_ref = f"whatsapp_doc_id:{doc_id}"
        save_invoice(user_id, final_data, stored_ref)
        
        # Reply to User
        if phone_number_id:
            reply_msg = messages.invoice_processed(
                vendor_gstin=final_data.get('vendor_gstin', 'N/A'),
                invoice_number=final_data.get('invoice_number', 'N/A'),
                amount=float(final_data.get('amount', 0)),
                status=final_data.get('reconciliation_status', 'PENDING'),
                lang=lang,
                notes=final_data.get('notes', '')
            )
            send_whatsapp_message(phone, reply_msg, phone_number_id)
        
        print(f"PDF Background: Finished for {phone}. Status: {final_data.get('reconciliation_status')}")
    except Exception as e:
        print(f"PDF Background Error: {e}")
        if phone_number_id:
            send_whatsapp_message(phone, messages.error_generic(lang), phone_number_id)
