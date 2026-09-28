import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API Key not found")
    exit(1)

client = genai.Client(api_key=api_key)

print("Available models:")
for model in client.models.list():
    if "flash" in model.name:
        print(f" - {model.name}")
