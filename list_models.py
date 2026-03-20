from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)

print("Listing available models...")
try:
    for model in client.models.list():
        # print only the fields that are likely to be useful
        print(f"Model: {model.name}, Display: {model.display_name}")
except Exception as e:
    print(f"Error listing models: {e}")
