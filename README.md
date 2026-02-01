# GST Guard DEMO VERSION

WhatsApp-first GST ITC Recovery Assistant for Indian MSMEs.

**Track vendor invoices, reconcile with GSTR-2B, and send automated reminders via WhatsApp.**

> **⚠️ BETA / DEMO VERSION**  
> This application currently uses **simulated GST portal reconciliation** for demonstration purposes.  
> It does NOT connect to the real GST portal API. For production use, integration with a licensed GSP (GST Suvidha Provider) is required.

---

##  Features

-  **Image & PDF Processing** - Send invoices as photos or PDFs
-  **AI Extraction** - Auto-extracts GSTIN, invoice number, amount, and date
-  **GST Reconciliation** - Simulates GSTR-2B matching to identify ITC at risk
-  **Dashboard** - Mobile-first UI with stats, search, filters, and CSV export
-  **WhatsApp Reminders** - Send bilingual nudges to vendors who haven't filed
-  **Language Support** - Users can switch between Hindi and English
-  **Certificate Onboarding** - Auto-extract GSTIN from GST certificate photos
-  **Secure** - OTP authentication, JWT sessions, Row-Level Security

---

##  Quick Start

### Prerequisites
- Python 3.10+ (3.11 recommended)
- Supabase account
- OpenRouter API key (for AI)
- WhatsApp Business API access (optional for testing)

### Installation

```powershell
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/gst-guard.git
cd gst-guard

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
# Copy .env.example to .env and fill in your credentials

# 5. Run database setup (Supabase SQL Editor)
# Execute supabase_rls.sql in your Supabase dashboard

# 6. Start the server
uvicorn app.main:app --port 8000 --reload
```

### For WhatsApp Webhooks (Development)

```powershell
# Expose local server to internet
ngrok http 8000
```

Configure WhatsApp webhook URL: `https://your-ngrok-url.ngrok-free.app/api/webhook`

---

##  Environment Variables (.env)

```env
# Database (Required)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_service_role_key

# Authentication (Required)
JWT_SECRET=random_32_character_secret_key_here

# AI Service (Required)
OPENROUTER_API_KEY=your_openrouter_key

# WhatsApp (Optional in dev mode)
WHATSAPP_API_TOKEN=your_meta_access_token
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_id
WHATSAPP_VERIFY_TOKEN=baba_ji_ki_jai
```

---

## 📁 Project Structure

```
gst-guard/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── api/
│   │   ├── webhook.py             # WhatsApp message handler
│   │   ├── auth.py                # OTP login endpoints
│   │   ├── invoices.py            # Dashboard data API
│   │   ├── vendors.py             # Vendor list & reminders
│   │   └── onboarding.py          # QR code generation
│   ├── db/
│   │   └── supabase_client.py     # Database operations
│   └── services/
│       ├── ai_service.py          # Invoice & certificate analysis (Vision AI)
│       ├── pdf_service.py         # PDF text extraction & parsing
│       ├── auth_service.py        # JWT & OTP logic
│       ├── gst_service.py         # GSTIN validation & reconciliation
│       ├── media_service.py       # WhatsApp media download
│       ├── vendor_service.py      # Reminder templates
│       ├── messages.py            # Bilingual WhatsApp messages
│       └── whatsapp_service.py    # WhatsApp API client
├── frontend/
│   └── index.html                 # Dashboard UI (login + invoices + vendors)
├── supabase_rls.sql               # Database security policies
├── requirements.txt               # Python dependencies
└── .env                           # Environment configuration (DO NOT COMMIT)
```

---

##  Key URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:8000` | Dashboard (login first) |
| `http://localhost:8000/api/qr` | QR code for WhatsApp onboarding |
| `http://localhost:8000/docs` | API documentation (Swagger) |

---

##  How It Works

1. **New User Signup**
   - Scan QR code → Opens WhatsApp
   - Send GST certificate photo → AI extracts GSTIN and business name
   - Account created automatically

2. **Invoice Processing**
   - Forward invoice (image or PDF) to WhatsApp bot
   - AI extracts: GSTIN, invoice number, amount, date
   - **Mock GST reconciliation** simulates GSTR-2B matching (70% FILED, 20% NOT_FOUND, 10% MISMATCH)
   - Invoice saved with simulated status: FILED / NOT_FOUND / MISMATCH

3. **Dashboard**
   - Login with phone number (OTP via WhatsApp)
   - View stats: Total Processed, ITC Recovered, ITC at Risk
   - Search/filter invoices by GSTIN, status, date
   - Export to CSV

4. **Vendor Management**
   - View vendors grouped by GSTIN
   - See filed/not-found/mismatch counts
   - Send WhatsApp reminders to vendors with missing invoices

5. **Language Preference**
   - Text "Hindi" or "English" to switch language
   - All messages tailored to user preference

---

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  whatsapp_phone_number TEXT UNIQUE NOT NULL,
  gstin TEXT,
  business_name TEXT,
  preferred_language TEXT DEFAULT 'en',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Invoices Table
```sql
CREATE TABLE invoices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  vendor_gstin TEXT,
  invoice_number TEXT,
  amount NUMERIC(12,2),
  date DATE,
  image_url TEXT,
  reconciliation_status TEXT, -- FILED / NOT_FOUND / MISMATCH / PENDING
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Run `supabase_rls.sql` to enable Row-Level Security and create access policies.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Database | Supabase (PostgreSQL) |
| AI/Vision | OpenRouter (Gemini/LLaMA) |
| PDF Processing | pdfplumber |
| Authentication | OTP via WhatsApp + JWT |
| Frontend | HTML + Tailwind CSS + Vanilla JS |
| Messaging | WhatsApp Business API |

---

##  Security

- ✅ OTP-based authentication via WhatsApp
- ✅ JWT token sessions
- ✅ Row-Level Security (RLS) in Supabase
- ✅ Webhook signature verification
- ✅ Environment variables for secrets
- ✅ `.gitignore` configured to exclude `.env`

---

