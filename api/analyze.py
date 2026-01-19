from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from vision_engine import analyze_image

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get content length
            content_length = int(self.headers['Content-Length'])
            
            # Read the body
            body = self.rfile.read(content_length)
            
            # For now, we'll handle multipart form data
            # In production, you'd want proper multipart parsing
            
            # Parse multipart boundary
            content_type = self.headers.get('Content-Type', '')
            
            if 'multipart/form-data' not in content_type:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Must be multipart/form-data"}).encode())
                return
            
            # Extract boundary
            boundary = content_type.split('boundary=')[1].encode()
            
            # Split by boundary
            parts = body.split(b'--' + boundary)
            
            image_data = None
            mime_type = "image/jpeg"
            
            for part in parts:
                if b'Content-Type: image/' in part:
                    # Extract mime type
                    for line in part.split(b'\r\n'):
                        if line.startswith(b'Content-Type: image/'):
                            mime_type = line.decode().split(': ')[1]
                            break
                    
                    # Extract image data (after double CRLF)
                    image_data = part.split(b'\r\n\r\n', 1)[1].rstrip(b'\r\n')
                    break
            
            if not image_data:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No image data found"}).encode())
                return
            
            # Analyze the image
            result = analyze_image(image_data, mime_type=mime_type)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
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
