from google import genai
from google.genai import types
import os
import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Fallback or load from environment
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in environment.")

client = genai.Client(api_key=API_KEY)

# Define Pydantic models for the response schema
class FaceGeometry(BaseModel):
    primary_shape: str
    jawline_definition: str
    structural_note: str

class MarketCategorization(BaseModel):
    primary: str
    rationale: str

class AestheticAudit(BaseModel):
    lighting_quality: str
    professional_readiness: str
    technical_flaw: str

class AnalysisResult(BaseModel):
    face_geometry: FaceGeometry
    market_categorization: MarketCategorization
    aesthetic_audit: AestheticAudit
    suitability_score: int
    scout_feedback: str

def analyze_image(image_bytes, mime_type="image/jpeg"):
    """
    Analyzes an image using Gemini to extract technical industry markers.
    Used google-genai SDK (v1.0+).
    """
    try:
        # Prompt Pivot: Professional Technical Audit
        prompt = """
        ACT AS: A Senior Global Model Scout for a top-tier agency (e.g., IMG, Elite). 

        TASK: Perform a high-fidelity structural audit of the provided image.

        REASONING STEPS (Internal Process):
        1. Observe the lighting: Identify shadows, light source, and skin texture clarity.
        2. Map facial geometry: Identify the 3 most dominant bone structure markers.
        3. Categorize: Cross-reference findings against 2026 fashion industry standards.

        OUTPUT DATA (JSON Format only):
        {
          "face_geometry": {
            "primary_shape": "[Heart, Square, Oval, Round, Diamond, Oblong, Triangular]",
            "jawline_definition": "[Soft, Sharp, Chiseled, Defined, Angular]",
            "structural_note": "Technical observation of cheekbone height and symmetry."
          },
          "market_categorization": {
            "primary": "[High Fashion, Commercial/Lifestyle, Fitness]",
            "rationale": "Why does this face fit this specific market?"
          },
          "aesthetic_audit": {
            "lighting_quality": "[Natural, Studio, Poor, Harsh]",
            "professional_readiness": "[Selfie, Amateur, Semi-Pro, Portfolio-Ready]",
            "technical_flaw": "Specific issue like 'motion blur', 'under-eye shadows', or 'distorting lens angle'."
          },
          "suitability_score": "Integer 0-100",
          "scout_feedback": "A professional, direct 1-sentence assessment of the model's market potential."
        }

        CONSTRAINTS: 
        - Be brutally honest about 'Professional Readiness'. If it's a bathroom selfie, the score must reflect that.
        - Use precise industry terminology (e.g., 'high-fashion edge', 'relatable commercial appeal').
        """
        
        # Validating input type
        if not image_bytes:
            raise ValueError("No image data provided")
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp', # Using newest available model
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=AnalysisResult,
                temperature=0.4,
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                ]
            )
        )
        
        # Check validation
        try:
             # If parsed successfully by SDK
             if response.parsed:
                 return response.parsed.model_dump()
             else:
                 # Fallback to text parsing if response.parsed is None (rare with schema)
                 return json.loads(response.text)
        except Exception as e:
            print(f"Parsing error: {e}. Raw text: {response.text}")
            raise e

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in Gemini analysis: {e}")
        # Return a mock response if API fails
        return {
            "error": f"{str(e)}",
            "suitability_score": 0,
            "market_categorization": {"primary": "Unknown", "rationale": "Analysis failed."},
            "face_geometry": {"primary_shape": "Unknown", "jawline_definition": "Unknown", "structural_note": "N/A"},
            "aesthetic_audit": {"lighting_quality": "Unknown", "professional_readiness": "Unknown", "technical_flaw": "Analysis Error"},
            "scout_feedback": f"Analysis failed: {str(e)}"
        }
