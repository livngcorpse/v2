import google.generativeai as genai
import os
import json  # ADDED: for JSON parsing
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

# ADDED: New function for pure JSON code generation
def generate_code(description: str, previous_error: str = None):
    """Generate code and return in pure JSON format as required by text.txt"""
    prompt = f"""Write a full Pyrogram Telegram bot module that implements: {description}

IMPORTANT: Return ONLY pure JSON in this exact format with no markdown, no explanations, no examples:
{{"files": {{"sandbox/feature_name/handler.py": "your_complete_code_here"}}}}

The code should be complete, working Python code for a Pyrogram bot module."""
    
    if previous_error:
        prompt += f"\n\nPrevious error occurred, please fix: {previous_error}"
    
    response = model.generate_content(prompt)
    
    # Try to parse as JSON first (pure JSON format as required)
    try:
        return json.loads(response.text.strip())
    except json.JSONDecodeError:
        # Fallback: extract code and wrap in JSON format
        cleaned_code = clean_code_blocks(response.text.strip())
        
        # Generate a simple feature name from description
        feature_name = description.lower().replace(" ", "_")[:20]
        
        return {
            "files": {
                f"sandbox/{feature_name}/handler.py": cleaned_code
            }
        }

# ADDED: New function for conversation responses
def generate_conversation_response(text: str, chat_history: list = None):
    """Generate natural conversation response"""
    
    # Build context from chat history if provided
    context = ""
    if chat_history:
        for entry in chat_history[-10:]:  # Last 10 messages for context
            role = entry.get("role", "user")
            content = entry.get("content", "")
            context += f"{role}: {content}\n"
    
    prompt = f"""You are JARVIS, an intelligent AI assistant. Respond naturally and helpfully to the user's message.

{f"Previous conversation context:\n{context}" if context else ""}

User's current message: {text}

Respond as a helpful, intelligent assistant. Keep responses concise but informative."""
    
    response = model.generate_content(prompt)
    return response.text.strip()
