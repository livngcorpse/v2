import google.generativeai as genai
import os
from modules.file_manager import clean_code_blocks

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def generate_module_code(description: str, previous_error: str = None):
    prompt = f"Write a full Pyrogram Telegram bot module that implements: {description}..."
    if previous_error:
        prompt += f"\n\nPrevious error: {previous_error}"
    response = model.generate_content(prompt)
    return clean_code_blocks(response.text.strip())