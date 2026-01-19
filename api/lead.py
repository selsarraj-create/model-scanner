from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get content length
            content_length = int(self.headers['Content-Length'])
            
            # Read and parse JSON body
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Get database connection
            postgres_url = os.getenv('POSTGRES_URL')
            
            if not postgres_url:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Database not configured. Please set up Vercel Postgres."
                }).encode())
                return
            
            # Initialize database if needed
            self._init_postgres_db(postgres_url)
            
            # Save lead
            lead_id = self._save_lead_postgres(postgres_url, data)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "lead_id": lead_id,
                "message": "Lead saved and report sent (mocked)."
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
    
    def _init_postgres_db(self, postgres_url):
        """Initialize Postgres database schema"""
        conn = psycopg2.connect(postgres_url)
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                gender TEXT,
                email TEXT,
                phone TEXT,
                city TEXT,
                zip_code TEXT,
                wants_assessment BOOLEAN,
                score INTEGER,
                category TEXT,
                analysis_json TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cur.close()
        conn.close()
    
    def _save_lead_postgres(self, postgres_url, lead_data):
        """Save lead to Postgres database"""
        conn = psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Extract score and category from analysis_data
        analysis_data = lead_data.get('analysis_data', {})
        score = analysis_data.get('suitability_score', 0)
        market_data = analysis_data.get('market_categorization', {})
        if isinstance(market_data, dict):
            category = market_data.get('primary', 'Unknown')
        else:
            category = str(market_data)
        
        cur.execute('''
            INSERT INTO leads (first_name, last_name, age, gender, email, phone, city, zip_code, wants_assessment, score, category, analysis_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            lead_data.get('first_name'),
            lead_data.get('last_name'),
            lead_data.get('age'),
            lead_data.get('gender'),
            lead_data.get('email'),
            lead_data.get('phone'),
            lead_data.get('city'),
            lead_data.get('zip_code'),
            lead_data.get('wants_assessment'),
            score,
            category,
            json.dumps(analysis_data)
        ))
        
        lead_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        
        return lead_id
