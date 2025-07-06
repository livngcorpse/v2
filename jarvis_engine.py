import google.generativeai as genai
import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from modules.file_manager import clean_code_blocks


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class JarvisEngine:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.conversation_model = genai.GenerativeModel("gemini-1.5-flash")
        
    def generate_code(self, description: str, previous_error: str = None, task_type: str = "CREATE") -> Dict[str, Any]:
        """Generate code based on description and return structured response"""
        
        base_prompt = f"""
        You are JARVIS, an AI that generates Pyrogram Telegram bot modules.
    
        Task: {description}
        Type: {task_type}
    
        CRITICAL RULES:
        1. Output ONLY valid JSON in this exact format:
        {{
          "files": {{
            "sandbox/module_name/handler.py": "python_code_here",
            "sandbox/module_name/utils.py": "python_code_here_if_needed"
          }}
        }}
    
        2. NO markdown formatting, NO explanations, NO examples
        3. Code must be complete and working Pyrogram handlers
        4. Use register_handlers(app, bot) function to register commands
        5. Import required modules at top of file
        """
        
        if previous_error:
            base_prompt += f"\n\nPrevious error to fix: {previous_error}"
        
        if task_type == "EDIT":
            base_prompt += "\n\nThis is an edit request. Modify existing code accordingly."
        elif task_type == "RECODE":
            base_prompt += "\n\nThis is a complete recode request. Rewrite from scratch."
        
        try:
            response = self.model.generate_content(base_prompt)
            response_text = response.text.strip()
    
            # Clean and parse JSON response
            cleaned_response = self._clean_json_response(response_text)
            result = json.loads(cleaned_response)
    
            # Log AI activity
            self._log_ai_activity(description, response_text, task_type)
    
            # Run quality checks on each generated file
            if "files" in result:
                result["quality_issues"] = {}  # Store issues file-wise
                for file_path, content in result["files"].items():
                    # Save as temporary file for checking
                    temp_file = f"temp_{file_path.replace('/', '_')}"
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(content)
    
                    check_result = regression_checker.comprehensive_check(temp_file)
                    if not check_result.passed:
                        result["quality_issues"][file_path] = {
                            "score": check_result.score,
                            "errors": check_result.errors,
                            "warnings": check_result.warnings
                        }
    
                    os.remove(temp_file)  # Clean up
    
            return result
    
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return {"error": str(e), "files": {}}

    
    def generate_module_code(self, description: str, previous_error: str = None) -> str:
        """Generate module code and return as string (legacy compatibility)"""
        
        prompt = f"Write a full Pyrogram Telegram bot module that implements: {description}..."
        if previous_error:
            prompt += f"\n\nPrevious error: {previous_error}"
        
        try:
            response = self.model.generate_content(prompt)
            return clean_code_blocks(response.text.strip())
        except Exception as e:
            logger.error(f"Module generation error: {e}")
            return f"# Error generating module: {e}"
    
    def generate_conversation_response(self, user_message: str, chat_history: list = None) -> str:
        """Generate natural conversation response"""
        
        prompt = f"""
        You are JARVIS, an intelligent AI assistant for a Telegram bot.
        
        User message: {user_message}
        
        Respond naturally and helpfully. You can:
        - Answer questions
        - Provide explanations
        - Help with general topics
        - Be conversational and friendly
        
        Keep responses concise but informative.
        """
        
        if chat_history:
            history_text = "\n".join([f"User: {msg.get('content', '')}" for msg in chat_history[-5:] if msg.get('role') == 'user'])
            prompt += f"\n\nRecent conversation:\n{history_text}"
        
        try:
            response = self.conversation_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Conversation generation error: {e}")
            return "I apologize, but I'm having trouble processing your request right now."
    
    def review_code(self, file_path: str, code_content: str) -> str:
        """Review code and provide suggestions"""
        
        prompt = f"""
        Review this Pyrogram bot code and provide concise suggestions for improvement:
        
        File: {file_path}
        Code:
        {code_content}
        
        Focus on:
        - Code quality and best practices
        - Potential bugs or issues
        - Performance improvements
        - Security considerations
        - Pyrogram-specific optimizations
        
        Keep response concise and actionable.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Code review error: {e}")
            return f"Error reviewing code: {e}"
    
    def debug_error(self, error_traceback: str, code_context: str = None) -> str:
        """Generate debug suggestions for errors"""
        
        prompt = f"""
        Analyze this error and provide debugging suggestions:
        
        Error:
        {error_traceback}
        
        """
        
        if code_context:
            prompt += f"\nCode context:\n{code_context}"
        
        prompt += "\nProvide specific steps to fix this error."
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Debug generation error: {e}")
            return f"Error generating debug suggestions: {e}"
    
    def _clean_json_response(self, response: str) -> str:
        """Clean AI response to extract valid JSON"""
        
        # Remove markdown formatting
        response = clean_code_blocks(response)
        
        # Find JSON content
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            return response[start_idx:end_idx+1]
        
        return response
    
    def _log_ai_activity(self, prompt: str, response: str, task_type: str):
        """Log AI interactions"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response[:500] + "..." if len(response) > 500 else response,
            "task_type": task_type
        }
        
        log_file = "logs/ai_activity.log"
        os.makedirs("logs", exist_ok=True)
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

# Global instance
jarvis_engine = JarvisEngine()
