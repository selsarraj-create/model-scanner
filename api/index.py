from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import time
from typing import Optional
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# Load valid environment
load_dotenv()

# Import local utils (copying logic from previous files)
# Assuming vision_engine is available in api path or python path
# If vision_engine.py is in api/, we can import it
try:
    from vision_engine import analyze_image
except ImportError:
    # Fallback/Mock if missing (should be present)
    def analyze_image(img_data, mime_type):
        return {"suitability_score": 0, "market_categorization": "Unknown"}

from webhook_utils import send_webhook

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to get Supabase client
def get_supabase() -> Client:
    url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
    key = (
        os.getenv('BACKEND_SERVICE_KEY') or
        os.getenv('SUPABASE_SERVICE_ROLE_KEY') or 
        os.getenv('VITE_SUPABASE_ANON_KEY') or 
        os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY') or 
        os.getenv('SUPABASE_ANON_KEY') or 
        os.getenv('SUPABASE_PUBLISHABLE_KEY')
    )
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase credentials missing")
    return create_client(url, key)

@app.post("/api/lead")
async def create_lead(
    file: Optional[UploadFile] = File(None),
    first_name: str = Form(...),
    last_name: str = Form(...),
    age: str = Form(...),
    gender: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    city: str = Form(...),
    zip_code: str = Form(...),
    campaign: Optional[str] = Form(None),
    wants_assessment: Optional[str] = Form("false"), # Receiving as string from FormData
    analysis_data: Optional[str] = Form("{}")
):
    try:
        supabase = get_supabase()
        
        # 1. Duplicate Check
        existing = supabase.table('leads').select('id').or_(f"email.eq.{email},phone.eq.{phone}").execute()
        if existing.data and len(existing.data) > 0:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "This email or phone number has already been submitted."}
            )

        # 2. Image Upload
        image_url = None
        if file:
            try:
                content = await file.read()
                timestamp = int(time.time())
                clean_email = email.replace('@', '-at-').replace('.', '-')
                filename = f"{clean_email}_{timestamp}.jpg"
                
                # Upload
                supabase.storage.from_("lead-images").upload(
                    path=filename,
                    file=content,
                    file_options={"content-type": file.content_type}
                )
                
                # Construct URL
                # Assuming standard Supabase URL structure
                sb_url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
                image_url = f"{sb_url}/storage/v1/object/public/lead-images/{filename}"
            except Exception as e:
                print(f"Upload failed: {e}")
                pass

        # 3. Prepare Data
        try:
            analysis_json = json.loads(analysis_data)
        except:
            analysis_json = {}
            
        score = analysis_json.get('suitability_score', 0)
        market_data = analysis_json.get('market_categorization', {})
        category = market_data.get('primary', 'Unknown') if isinstance(market_data, dict) else str(market_data)
        
        # Insert Record
        lead_record = {
            'first_name': first_name,
            'last_name': last_name,
            'age': age,
            'gender': gender,
            'email': email,
            'phone': phone,
            'city': city,
            'zip_code': zip_code,
            'campaign': campaign,
            'wants_assessment': (wants_assessment == 'true'),
            'score': score,
            'category': category,
            'analysis_json': analysis_json,
            'image_url': image_url,
            'webhook_sent': False,
            'webhook_status': 'pending',
            'webhook_response': None
        }
        
        result = supabase.table('leads').insert(lead_record).execute()
        
        if not result.data:
            raise Exception("Insert failed")
            
        lead_id = result.data[0]['id']
        
        # 4. Webhook
        webhook_url = os.getenv('CRM_WEBHOOK_URL')
        if webhook_url:
            wb_resp = send_webhook(webhook_url, lead_record)
            status = 'success' if wb_resp and wb_resp.status_code < 300 else 'failed'
            resp_text = wb_resp.text if wb_resp else "Connection failed"
            
            supabase.table('leads').update({
                'webhook_sent': True,
                'webhook_status': status,
                'webhook_response': resp_text
            }).eq('id', lead_id).execute()
        else:
            supabase.table('leads').update({
                'webhook_status': 'not_configured',
                'webhook_response': 'CRM_WEBHOOK_URL not set'
            }).eq('id', lead_id).execute()
            
        return {
            "status": "success",
            "lead_id": lead_id,
            "message": "Lead saved successfully."
        }

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/analyze")
async def analyze_endpoint(file: UploadFile = File(...)):
    try:
        content = await file.read()
        mime_type = file.content_type or "image/jpeg"
        
        result = analyze_image(content, mime_type=mime_type)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class RetryRequest(BaseModel):
    lead_id: str

@app.post("/api/retry_webhook")
async def retry_webhook(req: RetryRequest):
    try:
        supabase = get_supabase()
        webhook_url = os.getenv('CRM_WEBHOOK_URL')
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="CRM_WEBHOOK_URL not configured")
            
        resp = supabase.table('leads').select('*').eq('id', req.lead_id).execute()
        if not resp.data:
             raise HTTPException(status_code=404, detail="Lead not found")
             
        lead_record = resp.data[0]
        wb_resp = send_webhook(webhook_url, lead_record)
        
        status = 'success' if wb_resp and wb_resp.status_code < 300 else 'failed'
        resp_text = wb_resp.text if wb_resp else "Connection failed"
        
        supabase.table('leads').update({
            'webhook_sent': True,
            'webhook_status': status,
            'webhook_response': resp_text
        }).eq('id', req.lead_id).execute()
        
        return {
            "status": "success", 
            "message": "Webhook retry attempted",
            "webhook_status": status
        }
    except Exception as e:
         return JSONResponse(status_code=500, content={"error": str(e)})
