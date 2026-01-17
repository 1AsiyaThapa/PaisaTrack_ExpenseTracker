from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

def generate_text(prompt: str, model: str = "gemini-2.5-flash") -> str:

    if not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
        ),
    )

    return response.text.strip()

if __name__ == "__main__":
    print(generate_text("Hello, how are you?"))

