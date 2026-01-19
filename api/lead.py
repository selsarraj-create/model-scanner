from http.server import BaseHTTPRequestHandler
import json
import os
from supabase import create_client, Client

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get content length
            content_length = int(self.headers['Content-Length'])
            
            # Read and parse JSON body
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Initialize Supabase client
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_PUBLISHABLE_KEY')
            
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
            analysis_data = data.get('analysis_data', {})
            score = analysis_data.get('suitability_score', 0)
            market_data = analysis_data.get('market_categorization', {})
            category = market_data.get('primary', 'Unknown') if isinstance(market_data, dict) else str(market_data)
            
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
                
                # TODO: Send webhook to CRM here
                # webhook_url = os.getenv('CRM_WEBHOOK_URL')
                # if webhook_url:
                #     webhook_response = send_to_crm(webhook_url, lead_record)
                #     # Update webhook status
                #     supabase.table('leads').update({
                #         'webhook_sent': True,
                #         'webhook_status': 'success' if webhook_response.ok else 'failed',
                #         'webhook_response': webhook_response.text
                #     }).eq('id', lead_id).execute()
                
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
