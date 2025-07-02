import os
import json
import logging
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

class JarvisEngine:
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.system_prompt = self.load_system_prompt()

    def load_system_prompt(self):
        """Load system prompt for AI"""
        return """You are JARVIS v2, a self-evolving AI Telegram bot assistant. 

CRITICAL RESPONSE FORMAT:
- You MUST respond with PURE JSON ONLY when creating/modifying files
- Use this exact format: {"files": {"path/file.py": "content", "another/file.py": "content"}}
- NO markdown, NO explanations, NO extra text - ONLY JSON
- For conversations without file operations, respond normally

CAPABILITIES:
- Build bots, games, features from natural language prompts
- Create Python modules with proper structure
- Generate command handlers for Telegram bots
- Create JSON databases for features
- Implement complete functional systems

Always create working, complete code with proper error handling."""

    async def process_prompt(self, prompt):
        """Process a text prompt"""
        try:
            full_prompt = f"{self.system_prompt}\n\nUser Request: {prompt}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_url}?key={self.gemini_api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['candidates'][0]['content']['parts'][0]['text']
                        
                        # Try to parse as JSON for file operations
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            # Return as regular response if not JSON
                            return content
                    else:
                        logger.error(f"Gemini API error: {response.status}")
                        return "❌ AI service unavailable"
                        
        except Exception as e:
            logger.error(f"Error in process_prompt: {e}")
            return f"❌ Error processing request: {str(e)}"

    async def process_file_prompt(self, instruction, file_content):
        """Process a prompt with file context"""
        try:
            full_prompt = f"{self.system_prompt}\n\nFile Content:\n{file_content}\n\nInstruction: {instruction}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_url}?key={self.gemini_api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['candidates'][0]['content']['parts'][0]['text']
                        
                        # Try to parse as JSON for file operations
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            return content
                    else:
                        logger.error(f"Gemini API error: {response.status}")
                        return "❌ AI service unavailable"
                        
        except Exception as e:
            logger.error(f"Error in process_file_prompt: {e}")
            return f"❌ Error processing file request: {str(e)}"