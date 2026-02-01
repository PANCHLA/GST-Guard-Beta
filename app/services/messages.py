"""
WhatsApp message templates with language preference support.
Users can choose Hindi (hi) or English (en).
Default: English
"""

# Language constants
LANG_HI = "hi"
LANG_EN = "en"
DEFAULT_LANG = LANG_EN

# ============ MESSAGE TEMPLATES ============

MESSAGES = {
    "welcome": {
        "hi": """🛡️ *नमस्ते! GST Guard में आपका स्वागत है!*

मैं आपको Vendor Bills track करने और ITC बचाने में मदद करूंगा।

📱 *कैसे शुरू करें:*
1️⃣ Vendor से Bill आए → यहां Forward करें
2️⃣ मैं details निकाल लूंगा
3️⃣ Dashboard पर सब देखें

*अभी शुरू करने के लिए कोई Invoice भेजें!* 📸

💡 Language बदलने के लिए "English" लिखें""",
        
        "en": """🛡️ *Welcome to GST Guard!*

I'll help you track vendor bills and save ITC.

📱 *How to start:*
1️⃣ Forward vendor bills here
2️⃣ I'll extract the details
3️⃣ View everything on dashboard

*Send any invoice photo to get started!* 📸

💡 Type "Hindi" to switch language"""
    },
    
    "send_photo_only": {
        "hi": """📸 *कृपया Invoice की फोटो भेजें*

मैं सिर्फ फोटो process कर सकता हूं, text नहीं।

💡 *Tip:* Vendor से Bill WhatsApp पर आया? बस यहां Forward करें!""",
        
        "en": """📸 *Please send a photo of the invoice*

I can only process photos, not text messages.

💡 *Tip:* Got a bill on WhatsApp from vendor? Just forward it here!"""
    },
    
    "error_download": {
        "hi": """❌ *Image Download में Error*

कृपया फिर से भेजें।""",
        
        "en": """❌ *Error downloading image*

Please try sending again."""
    },
    
    "error_generic": {
        "hi": """❌ *कुछ गलती हुई*

कृपया फिर से कोशिश करें।""",
        
        "en": """❌ *Something went wrong*

Please try again."""
    },
    
    "ask_certificate": {
        "hi": """📋 *अपना GST Certificate भेजें*

Quick Setup के लिए, अपने GST Registration Certificate की photo भेजें।

मैं आपका GSTIN और Business Name automatic extract कर लूंगा! ✨

💡 *Tip:* Certificate Govt. GST Portal से download करें।""",
        
        "en": """📋 *Send your GST Certificate*

For quick setup, send a photo of your GST Registration Certificate.

I'll automatically extract your GSTIN and Business Name! ✨

💡 *Tip:* Download certificate from GST Portal."""
    },
    
    "certificate_error": {
        "hi": """❌ *Certificate नहीं पढ़ पाया*

कृपया clear photo भेजें जिसमें GSTIN दिखे।

💡 *Tips:*
• Photo में पूरा certificate हो
• अच्छी lighting में लें
• Blur न हो""",
        
        "en": """❌ *Could not read the certificate*

Please send a clear photo where GSTIN is visible.

💡 *Tips:*
• Include full certificate in photo
• Good lighting
• No blur"""
    },
    
    "certificate_invalid": {
        "hi": """⚠️ *यह GST Certificate नहीं लगता*

कृपया अपने official GST Registration Certificate की photo भेजें।

📥 GST Portal से download करें: https://gst.gov.in""",
        
        "en": """⚠️ *This doesn't appear to be a GST Certificate*

Please send a photo of your official GST Registration Certificate.

📥 Download from GST Portal: https://gst.gov.in"""
    },
    
    "language_changed": {
        "hi": """✅ *भाषा बदल गई: हिंदी*

अब सभी messages हिंदी में आएंगे।""",
        
        "en": """✅ *Language changed: English*

All messages will now be in English."""
    }
}


# ============ MESSAGE FUNCTIONS ============

def get_message(key: str, lang: str = DEFAULT_LANG) -> str:
    """Get a message in the specified language."""
    lang = lang if lang in [LANG_HI, LANG_EN] else DEFAULT_LANG
    return MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get(DEFAULT_LANG, ""))


def welcome(lang: str = DEFAULT_LANG) -> str:
    return get_message("welcome", lang)


def send_photo_only(lang: str = DEFAULT_LANG) -> str:
    return get_message("send_photo_only", lang)


def error_download(lang: str = DEFAULT_LANG) -> str:
    return get_message("error_download", lang)


def error_generic(lang: str = DEFAULT_LANG) -> str:
    return get_message("error_generic", lang)


def ask_certificate(lang: str = DEFAULT_LANG) -> str:
    return get_message("ask_certificate", lang)


def certificate_error(lang: str = DEFAULT_LANG) -> str:
    return get_message("certificate_error", lang)


def certificate_invalid(lang: str = DEFAULT_LANG) -> str:
    return get_message("certificate_invalid", lang)


def language_changed(lang: str = DEFAULT_LANG) -> str:
    return get_message("language_changed", lang)


def invoice_processed(vendor_gstin: str, invoice_number: str, amount: float, status: str, lang: str = DEFAULT_LANG, notes: str = "") -> str:
    """Generate invoice processed message."""
    if lang == LANG_HI:
        status_text = "दाखिल ✅" if status == "FILED" else "नहीं मिला ⚠️" if status == "NOT_FOUND" else "Mismatch ❌"
        return f"""*Invoice Process हो गया* ✅

📋 *Details:*
• Vendor GSTIN: `{vendor_gstin}`
• Invoice No: `{invoice_number}`
• Amount: ₹{amount:,.2f}
• Status: {status_text}
{f'• Note: {notes}' if notes else ''}

🔗 Dashboard पर details देखें।"""
    else:
        status_text = "Filed ✅" if status == "FILED" else "Not Found ⚠️" if status == "NOT_FOUND" else "Mismatch ❌"
        return f"""*Invoice Processed* ✅

📋 *Details:*
• Vendor GSTIN: `{vendor_gstin}`
• Invoice No: `{invoice_number}`
• Amount: ₹{amount:,.2f}
• Status: {status_text}
{f'• Note: {notes}' if notes else ''}

🔗 View details on dashboard."""


def duplicate_invoice(invoice_number: str, vendor_gstin: str, lang: str = DEFAULT_LANG) -> str:
    """Generate duplicate invoice message."""
    if lang == LANG_HI:
        return f"""⚠️ *Duplicate Invoice!*

Invoice `{invoice_number}` from `{vendor_gstin}` पहले से process हो चुका है।

दोबारा save नहीं किया गया।"""
    else:
        return f"""⚠️ *Duplicate Invoice!*

Invoice `{invoice_number}` from `{vendor_gstin}` has already been processed.

Not saved again."""


def otp_message(otp: str, lang: str = DEFAULT_LANG) -> str:
    """Generate OTP message."""
    if lang == LANG_HI:
        return f"""🔐 *GST Guard Login Code*

आपका OTP है: *{otp}*

⏱️ यह code 5 मिनट में expire होगा।
⚠️ किसी से share न करें!"""
    else:
        return f"""� *GST Guard Login Code*

Your OTP is: *{otp}*

⏱️ This code expires in 5 minutes.
⚠️ Do not share with anyone!"""


def certificate_success(gstin: str, business_name: str, lang: str = DEFAULT_LANG) -> str:
    """Generate certificate success message."""
    if lang == LANG_HI:
        return f"""✅ *Registration Complete!*

🏢 *Business:* {business_name}
📋 *GSTIN:* `{gstin}`

अब आप Invoice photos भेज सकते हैं और ITC track कर सकते हैं!

📱 Dashboard पर Login करें"""
    else:
        return f"""✅ *Registration Complete!*

🏢 *Business:* {business_name}
📋 *GSTIN:* `{gstin}`

Now you can send invoice photos and track your ITC!

📱 Login to Dashboard"""


# QR code pre-filled message (always Hindi for cultural context)
QR_PREFILL_MESSAGE = "मुझे GST बचाओ 🛡️"


# Legacy constants for backward compatibility
WELCOME = welcome(DEFAULT_LANG)
SEND_PHOTO_ONLY = send_photo_only(DEFAULT_LANG)
ERROR_DOWNLOAD = error_download(DEFAULT_LANG)
ERROR_GENERIC = error_generic(DEFAULT_LANG)
ASK_FOR_CERTIFICATE = ask_certificate(DEFAULT_LANG)
CERTIFICATE_ERROR = certificate_error(DEFAULT_LANG)
CERTIFICATE_INVALID = certificate_invalid(DEFAULT_LANG)
