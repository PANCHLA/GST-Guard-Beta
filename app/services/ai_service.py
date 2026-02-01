import os
from openai import OpenAI

# Initialize the client for OpenRouter
# OpenRouter uses the OpenAI client structure but with a different base URL
# Initialize the client for OpenRouter
# function will init client inside to ensure fresh env var usage or just keeping it global is fine, 
# but removing the "mock_key" override.

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def analyze_invoice_image(image_url: str):
    """
    Analyze an invoice image using OpenRouter (Gemini Flash or Llama Vision).
    Returns a dictionary with extracted fields.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    # Prompt for Indian Invoice Extraction
    system_prompt = """
    You are an expert data entry operator for Indian GST Invoices.
    Analyze the image and return a JSON object with these accurate fields:
    - vendor_gstin (Format: 15 chars, starts with state code e.g. 29, 27)
    - invoice_number (Look for 'Invoice No', 'Bill No')
    - date (YYYY-MM-DD format)
    - amount (Grand Total, float)
    
    If unreadable, return empty strings.
    """
    
    try:
        response = client.chat.completions.create(
          model="nvidia/nemotron-nano-12b-v2-vl:free", # Latest fast model
          messages=[
            {
              "role": "user",
              "content": [
                {"type": "text", "text": system_prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
              ]
            }
          ]
        )
        # Parse JSON from response
        # Note: In real prod, use structured output or Pydantic validation
        raw_text = response.choices[0].message.content
        import json
        # Simple cleanup to remove markdown fences if present
        cleaned_json = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_json)
        
    except Exception as e:
        print(f"AI Service Error: {e}")
        # Fallback for reliability
        return {
            "vendor_gstin": "ERROR",
            "invoice_number": "ERROR",
            "amount": 0.0,
            "date": ""
        }


def analyze_gst_certificate(image_url: str) -> dict:
    """
    Analyze a GST Certificate image to extract business registration details.
    Used for onboarding new users from their GST certificate photo.
    
    Returns:
        {
            "gstin": "29ABCDE1234F1Z5",
            "business_name": "ABC Traders",
            "address": "123 Main St, Bangalore",
            "valid": True,
            "error": None
        }
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("AI Service: No API key, returning mock certificate data")
        return {
            "gstin": "",
            "business_name": "",
            "address": "",
            "valid": False,
            "error": "AI service not configured"
        }
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    system_prompt = """
    You are analyzing an Indian GST Registration Certificate image.
    Extract the following information and return as JSON:
    
    - gstin: The 15-character GSTIN number (format: 2 digits state + 10 char PAN + 1 + Z + 1)
    - business_name: Legal name of the business
    - address: Principal place of business address
    
    If the image is NOT a GST certificate or is unreadable, return:
    {"gstin": "", "business_name": "", "address": "", "valid": false, "error": "Not a valid GST certificate"}
    
    If valid, include:
    {"gstin": "...", "business_name": "...", "address": "...", "valid": true, "error": null}
    """
    
    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-nano-12b-v2-vl:free",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
        )
        
        raw_text = response.choices[0].message.content
        import json
        cleaned_json = raw_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned_json)
        
        # Validate GSTIN format
        gstin = result.get("gstin", "")
        if gstin and len(gstin) == 15:
            result["valid"] = True
        else:
            result["valid"] = False
            result["error"] = "Could not extract valid GSTIN"
        
        return result
        
    except Exception as e:
        print(f"AI Certificate Error: {e}")
        return {
            "gstin": "",
            "business_name": "",
            "address": "",
            "valid": False,
            "error": str(e)
        }
