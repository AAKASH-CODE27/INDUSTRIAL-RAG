import os
import sys
from dotenv import load_dotenv

# Ensure the app module can be found
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

load_dotenv()
from app.services.gemini_provider import GeminiProvider

def test_generation():
    provider = GeminiProvider()
    print(f"Testing model: {provider.model}")
    try:
        response = provider.generate_text("Say 'Hello, Gemini is working!'")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_generation()
