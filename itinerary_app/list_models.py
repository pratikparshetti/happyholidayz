import google.generativeai as genai
import os

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    # Fallback for testing if env var isn't set in this session context
    # Ideally user sets it, but for this diagnostics script we might need to ask or rely on them setting it.
    print("GEMINI_API_KEY not found in environment.")
else:
    genai.configure(api_key=api_key)
    print("Listing available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
