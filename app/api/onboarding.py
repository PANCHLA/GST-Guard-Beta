from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response
import urllib.parse
from app.services.messages import QR_PREFILL_MESSAGE

router = APIRouter()

# Your WhatsApp Business number (with country code, no +)
# This should match the number connected to your WhatsApp Business API
WHATSAPP_NUMBER = "+15551576195"  # Replace with your actual number


@router.get("/qr", response_class=HTMLResponse)
async def get_qr_page():
    """
    Returns an HTML page with the QR code for WhatsApp onboarding.
    Users scan this to start chatting with GST Guard.
    """
    # URL encode the pre-fill message
    encoded_message = urllib.parse.quote(QR_PREFILL_MESSAGE)
    whatsapp_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded_message}"
    
    # Generate QR code using a public API (no dependencies needed)
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(whatsapp_link)}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GST Guard - QR Code</title>
        <style>
            * {{ font-family: 'Segoe UI', sans-serif; }}
            body {{ 
                background: linear-gradient(135deg, #1e3a5f, #0f172a);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
                padding: 20px;
            }}
            .card {{
                background: white;
                border-radius: 24px;
                padding: 40px;
                text-align: center;
                max-width: 400px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{ color: #1e3a5f; margin-bottom: 10px; }}
            .subtitle {{ color: #64748b; margin-bottom: 30px; }}
            .qr-container {{
                background: #f8fafc;
                padding: 20px;
                border-radius: 16px;
                display: inline-block;
                margin-bottom: 20px;
            }}
            .qr-container img {{ display: block; }}
            .instructions {{
                background: #f0fdf4;
                border: 1px solid #86efac;
                border-radius: 12px;
                padding: 16px;
                margin-top: 20px;
                text-align: left;
            }}
            .instructions h3 {{ margin: 0 0 12px 0; color: #166534; }}
            .instructions ol {{ margin: 0; padding-left: 20px; color: #166534; }}
            .instructions li {{ margin-bottom: 8px; }}
            .btn {{
                display: inline-block;
                background: linear-gradient(135deg, #25D366, #128C7E);
                color: white;
                padding: 14px 28px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: bold;
                margin-top: 20px;
            }}
            .btn:hover {{ opacity: 0.9; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🛡️ GST Guard</h1>
            <p class="subtitle">ITC Recovery Assistant</p>
            
            <div class="qr-container">
                <img src="{qr_api_url}" alt="WhatsApp QR Code" width="300" height="300">
            </div>
            
            <p><strong>Scan with WhatsApp Camera</strong></p>
            <p style="color: #64748b;">or click the button below</p>
            
            <a href="{whatsapp_link}" target="_blank" class="btn">
                💬 Open WhatsApp
            </a>
            
            <div class="instructions">
                <h3>📱 कैसे शुरू करें / How to Start</h3>
                <ol>
                    <li>QR scan करें या button दबाएं</li>
                    <li>WhatsApp में message भेजें</li>
                    <li>Invoice photos forward करें</li>
                    <li>ITC बचाएं! 🎉</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/qr/image")
async def get_qr_image():
    """
    Returns just the QR code image (for embedding).
    """
    import httpx
    
    encoded_message = urllib.parse.quote(QR_PREFILL_MESSAGE)
    whatsapp_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded_message}"
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(whatsapp_link)}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(qr_api_url)
        return Response(content=response.content, media_type="image/png")
