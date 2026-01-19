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
            
            lead_id = data.get('lead_id')
            
            if not lead_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing lead_id"}).encode())
                return
            
            # Initialize Supabase client
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = (
                os.getenv('SUPABASE_SERVICE_ROLE_KEY') or
                os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY') or 
                os.getenv('SUPABASE_ANON_KEY') or 
                os.getenv('SUPABASE_PUBLISHABLE_KEY')
            )
            webhook_url = os.getenv('CRM_WEBHOOK_URL')
            
            if not supabase_url or not supabase_key:
                self.send_response(500)
                self.wfile.write(json.dumps({"error": "Supabase credentials missing"}).encode())
                return

            if not webhook_url:
                self.send_response(400)
                self.wfile.write(json.dumps({"error": "CRM_WEBHOOK_URL not configured"}).encode())
                return
            
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Fetch the lead
            response = supabase.table('leads').select('*').eq('id', lead_id).execute()
            
            if not response.data or len(response.data) == 0:
                self.send_response(404)
                self.wfile.write(json.dumps({"error": "Lead not found"}).encode())
                return
                
            lead_record = response.data[0]
            
            # Resend webhook
            webhook_response = send_webhook(webhook_url, lead_record)
            
            # Update status
            status = 'success' if webhook_response and webhook_response.status_code < 300 else 'failed'
            response_text = webhook_response.text if webhook_response else "Connection failed"
            
            supabase.table('leads').update({
                'webhook_sent': True,
                'webhook_status': status,
                'webhook_response': response_text
            }).eq('id', lead_id).execute()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success", 
                "message": "Webhook retry attempted",
                "webhook_status": status
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
