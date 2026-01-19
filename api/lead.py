from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from supabase import create_client, Client
from webhook_utils import send_webhook

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get content length
            content_length = int(self.headers['Content-Length'])
            
            # Read and parse JSON body
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Initialize Supabase client
            supabase_url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
            # Prioritize Manual Service Key for backend to bypass RLS
            supabase_key = (
                os.getenv('BACKEND_SERVICE_KEY') or
                os.getenv('SUPABASE_SERVICE_ROLE_KEY') or 
                os.getenv('VITE_SUPABASE_ANON_KEY') or 
                os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY') or 
                os.getenv('SUPABASE_ANON_KEY') or 
                os.getenv('SUPABASE_PUBLISHABLE_KEY')
            )
            
            print(f"DEBUG: URL found: {bool(supabase_url)}, Key found: {bool(supabase_key)}")
            if supabase_key: 
                print(f"DEBUG: Key starts with: {supabase_key[:5]}...")
                print(f"DEBUG: Using BACKEND_SERVICE_KEY: {bool(os.getenv('BACKEND_SERVICE_KEY'))}")
            webhook_url = os.getenv('CRM_WEBHOOK_URL')
            
            if not supabase_url or not supabase_key:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Database not configured. Missing Supabase credentials."
                }).encode())
                return
            
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Extract analysis data
            # ... (rest of extraction logic same as before)
            analysis_data = data.get('analysis_data', {})
            score = analysis_data.get('suitability_score', 0)
            market_data = analysis_data.get('market_categorization', {})
            category = market_data.get('primary', 'Unknown') if isinstance(market_data, dict) else str(market_data)
            
            # Check for existing lead with same email or phone
            existing_lead = supabase.table('leads').select('id').or_(f"email.eq.{data.get('email')},phone.eq.{data.get('phone')}").execute()
            
            if existing_lead.data and len(existing_lead.data) > 0:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "This email or phone number has already been submitted."
                }).encode())
                return

            # Prepare lead data for Supabase
            lead_record = {
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'age': data.get('age'),
                'gender': data.get('gender'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'city': data.get('city'),
                'zip_code': data.get('zip_code'),
                'wants_assessment': data.get('wants_assessment', False),
                'score': score,
                'category': category,
                'analysis_json': analysis_data,
                'webhook_sent': False,
                'webhook_status': 'pending',
                'webhook_response': None
            }
            
            # Insert into Supabase
            result = supabase.table('leads').insert(lead_record).execute()
            
            if result.data:
                lead_id = result.data[0]['id']
                
                # Send webhook to CRM
                if webhook_url:
                    webhook_response = send_webhook(webhook_url, lead_record)
                    
                    # Update status
                    status = 'success' if webhook_response and webhook_response.status_code < 300 else 'failed'
                    response_text = webhook_response.text if webhook_response else "Connection failed"
                    
                    supabase.table('leads').update({
                        'webhook_sent': True,
                        'webhook_status': status,
                        'webhook_response': response_text
                    }).eq('id', lead_id).execute()
                else:
                     supabase.table('leads').update({
                        'webhook_status': 'not_configured',
                        'webhook_response': 'CRM_WEBHOOK_URL not set'
                    }).eq('id', lead_id).execute()
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "lead_id": lead_id,
                    "message": "Lead saved successfully."
                }).encode())
            else:
                raise Exception("Failed to insert lead into database")
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
