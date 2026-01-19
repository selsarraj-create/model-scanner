from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from supabase import create_client, Client
from webhook_utils import send_webhook

class handler(BaseHTTPRequestHandler):
            # Parse multipart/form-data using cgi.FieldStorage
            # cgi.FieldStorage requires the request headers and input stream
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                # Fallback to JSON if not multipart (for legacy/testing)
                try:
                    content_length = int(self.headers['Content-Length'])
                    body = self.rfile.read(content_length)
                    data = json.loads(body.decode('utf-8'))
                except:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid Content-Type or JSON"}).encode())
                    return
            else:
                import cgi
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                # Extract fields
                data = {}
                # Simple fields
                for field in ['first_name', 'last_name', 'age', 'gender', 'email', 'phone', 'city', 'zip_code', 'campaign']:
                    if field in form:
                        data[field] = form[field].value
                
                # Checkbox
                data['wants_assessment'] = False
                if 'wants_assessment' in form and form['wants_assessment'].value == 'true':
                    data['wants_assessment'] = True
                    
                # Analysis JSON (passed as string)
                analysis_data = {}
                if 'analysis_data' in form:
                    try:
                        analysis_data = json.loads(form['analysis_data'].value)
                    except:
                        pass
                
                # Image handling
                image_url = None
                if 'file' in form and form['file'].filename:
                    file_item = form['file']
                    if file_item.file:
                        file_data = file_item.file.read()
                        
                        # Upload to Supabase Storage
                        import time
                        timestamp = int(time.time())
                        clean_email = data.get('email', 'unknown').replace('@', '-at-').replace('.', '-')
                        filename = f"{clean_email}_{timestamp}.jpg"
                        
                        try:
                            # Using the standard client for storage upload
                            supabase.storage.from_("lead-images").upload(
                                path=filename,
                                file=file_data,
                                file_options={"content-type": file_item.type}
                            )
                            # Get Public URL
                            # Construct manually for speed or use client method
                            # public_url = supabase.storage.from_("lead-images").get_public_url(filename)
                            # The client method might vary by version, standard construction:
                            project_id = supabase_url.split('//')[1].split('.')[0]
                            image_url = f"{supabase_url}/storage/v1/object/public/lead-images/{filename}"
                            
                        except Exception as e:
                            print(f"Storage Error: {e}")
                            # Continue without image if upload fails? Or error?
                            # Let's log it but continue processing the lead
                            pass

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
            
            if not supabase_url or not supabase_key:
                self.send_response(500)
                # ... (error handling)
                return

            supabase: Client = create_client(supabase_url, supabase_key)

            # ... Duplicate Check ...
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
            
            # Extract analysis data (if not multipart, it was parsed above)
            if 'analysis_data' not in locals(): # If JSON path was taken
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
                'image_url': locals().get('image_url'), # Add image_url if exists
                'campaign': data.get('campaign'),
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
