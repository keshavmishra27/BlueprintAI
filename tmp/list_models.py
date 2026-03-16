import os
import google.generativeai as genai
from dotenv import load_dotenv

# Add the project root to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Explicitly load .env from root
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available Gemini models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
