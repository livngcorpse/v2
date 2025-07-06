import re
from typing import Tuple, Dict, Any
from memory.memory_manager import get_pending_tasks

class IntentClassifier:
    def __init__(self):
        self.create_keywords = [
            "create", "make", "build", "generate", "develop", "write", "code",
            "implement", "add", "new", "design", "construct"
        ]
        
        self.edit_keywords = [
            "edit", "modify", "change", "update", "alter", "fix", "adjust",
            "improve", "enhance", "refactor", "revise"
        ]
        
        self.recode_keywords = [
            "recode", "rewrite", "redo", "start over", "from scratch",
            "completely rewrite", "rebuild"
        ]
        
        self.integration_keywords = [
            "integrate", "add it", "confirm", "approve", "accept", "deploy",
            "move to plugins", "make it live", "activate"
        ]
        
        self.question_keywords = [
            "how", "what", "why", "when", "where", "explain", "tell me",
            "can you help", "could you help", "would you help", "help me understand"
        ]
        
        self.conversation_keywords = [
            "hello", "hi", "hey", "thanks", "thank you", "goodbye", "bye",
            "your name", "who are you", "what are you"
        ]
    
    def classify_intent(self, text: str, user_id: int, is_dev: bool = False) -> Tuple[str, Dict[str, Any]]:
        """
        Classify user intent and return intent type with metadata
        
        Returns:
            Tuple[str, Dict]: (intent_type, metadata)
        """
        
        text_lower = text.lower().strip()
        
        # Check for integration intent first (high priority)
        if self._has_integration_intent(text_lower):
            pending_tasks = get_pending_tasks(user_id)
            if pending_tasks:
                return "INTEGRATE", {
                    "pending_tasks": pending_tasks,
                    "confident": True
                }
            else:
                return "INTEGRATE_NO_PENDING", {
                    "message": "No pending tasks to integrate"
                }
        
        # Check for explicit conversation/question patterns
        if self._is_conversation(text_lower):
            return "CONVERSATION", {"confident": True}
        
        if self._is_question(text_lower):
            return "QUESTION", {"confident": True}
        
        # Check for development intents (only for devs)
        if is_dev:
            if self._has_recode_intent(text_lower):
                return "RECODE", {"confident": True}
            
            if self._has_edit_intent(text_lower):
                return "EDIT", {"confident": True}
                
            if self._has_create_intent(text_lower):
                return "CREATE", {"confident": True}
        
        # Ambiguous cases that need clarification
        if self._is_ambiguous_request(text_lower) and is_dev:
            return "CLARIFY", {
                "possible_intents": self._get_possible_intents(text_lower),
                "question": "Would you like me to:\n1. Create/build this feature\n2. Explain how to do it\n3. Just have a conversation about it"
            }
        
        # Default to conversation for non-devs or unclear intent
        return "CONVERSATION", {"confident": False}
    
    def _has_create_intent(self, text: str) -> bool:
        """Check if text indicates creation intent"""
        return any(keyword in text for keyword in self.create_keywords)
    
    def _has_edit_intent(self, text: str) -> bool:
        """Check if text indicates edit intent"""
        return any(keyword in text for keyword in self.edit_keywords)
    
    def _has_recode_intent(self, text: str) -> bool:
        """Check if text indicates recode intent"""
        return any(keyword in text for keyword in self.recode_keywords)
    
    def _has_integration_intent(self, text: str) -> bool:
        """Check if text indicates integration intent"""
        return any(keyword in text for keyword in self.integration_keywords)
    
    def _is_question(self, text: str) -> bool:
        """Check if text is a question"""
        return (
            text.endswith('?') or 
            any(keyword in text for keyword in self.question_keywords) or
            text.startswith(('how', 'what', 'why', 'when', 'where', 'can you', 'could you', 'would you'))
        )
    
    def _is_conversation(self, text: str) -> bool:
        """Check if text is casual conversation"""
        return any(keyword in text for keyword in self.conversation_keywords)
    
    def _is_ambiguous_request(self, text: str) -> bool:
        """Check if request is ambiguous and needs clarification"""
        
        # Patterns like "help me with X" or "can you help me make X"
        ambiguous_patterns = [
            r"help me (?:with|make|build|create)",
            r"can you help",
            r"could you help",
            r"would you help",
            r"assist me",
            r"i need help",
            r"how do i make",
            r"how to create"
        ]
        
        return any(re.search(pattern, text) for pattern in ambiguous_patterns)
    
    def _get_possible_intents(self, text: str) -> list:
        """Get list of possible intents for ambiguous text"""
        possible = []
        
        if self._has_create_intent(text):
            possible.append("CREATE")
        if self._has_edit_intent(text):
            possible.append("EDIT")
        if self._is_question(text):
            possible.append("QUESTION")
            
        return possible if possible else ["CONVERSATION"]
    
    def extract_feature_name(self, text: str) -> str:
        """Extract feature name from creation request"""
        
        # Common patterns for feature extraction
        patterns = [
            r"(?:create|make|build|generate|develop|write|code|implement|add|new|design|construct)\s+(?:a\s+)?(?:new\s+)?(.+?)(?:\s+(?:for|in|with|using|that|which)|$)",
            r"(?:help me|can you help me|could you help me|would you help me)\s+(?:create|make|build|generate|develop|write|code|implement|add|new|design|construct)\s+(?:a\s+)?(?:new\s+)?(.+?)(?:\s+(?:for|in|with|using|that|which)|$)",
            r"i want to (?:create|make|build|generate|develop|write|code|implement|add|new|design|construct)\s+(?:a\s+)?(?:new\s+)?(.+?)(?:\s+(?:for|in|with|using|that|which)|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                feature_name = match.group(1).strip()
                # Clean up common words
                feature_name = re.sub(r'\b(?:the|a|an|some|my|our|your|their)\b', '', feature_name).strip()
                return feature_name
        
        # Fallback: return first few words
        words = text.split()
        if len(words) > 3:
            return ' '.join(words[:3])
        
        return text[:30]  # Fallback to first 30 chars

# Global instance
intent_classifier = IntentClassifier()

# Backward compatibility functions
def determine_intent(text: str, user_id: int = 0, is_dev: bool = False) -> str:
    """Legacy function for backward compatibility"""
    intent, metadata = intent_classifier.classify_intent(text, user_id, is_dev)
    return intent
