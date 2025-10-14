"""
AI Chat Response Generator
Generates intelligent responses for Upwork messages using various AI models
"""

import torch
import logging
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)

class ChatResponseGenerator:
    """AI-powered chat response generator for Upwork messages"""
    
    def __init__(self):
        self.model_name = "microsoft/DialoGPT-medium"  # Good for conversations
        self.tokenizer = None
        self.model = None
        self.model_loaded = False
        
        # Template responses for common scenarios
        self.templates = {
            'project_inquiry': [
                "Thank you for your interest! I'd be happy to discuss your project. When would be a good time for a brief call?",
                "I've reviewed your project requirements and I'm confident I can help. Let me share some relevant examples from my portfolio.",
                "Your project sounds interesting! I have experience with similar work. Would you like to see some case studies?",
                "I'm excited about the opportunity to work on your project. Could we schedule a quick call to discuss the details?",
                "Thank you for reaching out! I have the perfect skillset for this project. Let me know when we can connect."
            ],
            'price_question': [
                "I'd be happy to provide a detailed quote. Could you share more specifics about the scope?",
                "My rates are competitive and depend on the project complexity. Let's discuss your specific needs.",
                "I can work within your budget. Let me break down the pricing based on your requirements.",
                "I offer flexible pricing based on project scope. Would you like to discuss your budget range?",
                "I'd like to understand your requirements better to provide accurate pricing. Can we schedule a call?"
            ],
            'timeline_question': [
                "I can typically deliver this type of project within [X] days. Would that timeline work for you?",
                "I'm available to start immediately and can commit to your deadline.",
                "Let me review the scope and provide you with a realistic timeline that ensures quality delivery.",
                "I have availability to start right away. What's your preferred timeline for completion?",
                "I can accommodate urgent timelines. Let's discuss what you need and when."
            ],
            'follow_up': [
                "I wanted to follow up on our previous conversation. Are you still looking for help with this project?",
                "Hi! Just checking in to see if you have any questions about my proposal.",
                "I hope you're doing well. I'm still very interested in working on your project. Any updates?",
                "Following up on our discussion - I'm available whenever you're ready to move forward.",
                "Hi there! Just wanted to touch base about the project we discussed. Let me know your thoughts!"
            ],
            'project_completion': [
                "Great! I've completed the work as discussed. Please review and let me know if you need any adjustments.",
                "The project is finished and ready for your review. I'm happy to make any necessary revisions.",
                "I've delivered the completed work. Please take a look and let me know if everything meets your expectations.",
                "Project completed! I've attached the final deliverables. Looking forward to your feedback.",
                "All done! The work is complete and ready for your review. Thank you for the opportunity!"
            ],
            'general': [
                "Thank you for reaching out! I'm looking forward to working with you.",
                "I appreciate your message. Let me get back to you with a detailed response.",
                "Great question! Let me provide you with all the details you need.",
                "Thank you for your interest in my services. I'm excited to discuss this opportunity.",
                "I'm happy to help! Let me know if you need any additional information."
            ]
        }
    
    def load_model(self) -> bool:
        """Load the AI model for response generation"""
        try:
            # For now, we'll use template-based responses
            # In the future, can integrate actual transformer models
            logger.info("AI Chat model initialized with template responses")
            self.model_loaded = True
            return True
        except Exception as e:
            logger.error(f"Failed to load chat model: {e}")
            return False
    
    def classify_message_intent(self, message_content: str) -> str:
        """Classify the intent of incoming message"""
        content_lower = message_content.lower()
        
        # Project inquiry keywords
        project_keywords = ['project', 'work', 'job', 'task', 'hire', 'need help', 'looking for']
        if any(word in content_lower for word in project_keywords):
            return 'project_inquiry'
        
        # Price/budget keywords
        price_keywords = ['price', 'cost', 'budget', 'rate', 'fee', 'how much', 'payment', 'charge']
        if any(word in content_lower for word in price_keywords):
            return 'price_question'
        
        # Timeline keywords  
        timeline_keywords = ['timeline', 'deadline', 'when', 'time', 'schedule', 'delivery', 'complete']
        if any(word in content_lower for word in timeline_keywords):
            return 'timeline_question'
        
        # Follow-up keywords
        followup_keywords = ['follow up', 'checking in', 'any update', 'still interested', 'status']
        if any(word in content_lower for word in followup_keywords):
            return 'follow_up'
        
        # Completion keywords
        completion_keywords = ['done', 'finished', 'complete', 'delivered', 'ready', 'final']
        if any(word in content_lower for word in completion_keywords):
            return 'project_completion'
        
        return 'general'
    
    def suggest_reply_templates(self, message_content: str) -> List[str]:
        """Suggest template responses based on message content"""
        if not message_content:
            return self.templates['general']
        
        intent = self.classify_message_intent(message_content)
        return self.templates.get(intent, self.templates['general'])
    
    def generate_personalized_response(self, message_history: List[Dict], client_context: str = "") -> str:
        """Generate a personalized response based on conversation history"""
        if not message_history:
            return "Thank you for your message! I'm looking forward to discussing your project."
        
        latest_message = message_history[0] if message_history else {}
        latest_content = latest_message.get('content', '')
        
        intent = self.classify_message_intent(latest_content)
        templates = self.templates.get(intent, self.templates['general'])
        
        # Get the first template and try to personalize it
        base_response = templates[0] if templates else "Thank you for your message!"
        
        # Add personalization based on client context
        if client_context:
            if 'Client:' in client_context:
                client_name = client_context.split('Client:')[1].split(',')[0].strip()
                if client_name and client_name != 'Unknown':
                    base_response = f"Hi {client_name}! " + base_response
        
        # Add context-aware modifications
        if intent == 'project_inquiry':
            # Look for project type in message
            if 'website' in latest_content.lower():
                base_response += " I specialize in web development and have built similar websites."
            elif 'mobile' in latest_content.lower() or 'app' in latest_content.lower():
                base_response += " I have extensive experience in mobile app development."
            elif 'data' in latest_content.lower() or 'analysis' in latest_content.lower():
                base_response += " I specialize in data analysis and visualization projects."
        
        return base_response
    
    def get_conversation_insights(self, messages: List[Dict]) -> Dict:
        """Analyze conversation for insights and suggestions"""
        if not messages:
            return {}
        
        insights = {
            'message_count': len(messages),
            'response_rate': 0,
            'avg_response_time': 'Unknown',
            'client_sentiment': 'Neutral',
            'recommended_action': 'Continue conversation',
            'urgency_level': 'Normal'
        }
        
        # Count my responses vs client messages
        my_messages = [msg for msg in messages if msg.get('is_from_me', False)]
        client_messages = [msg for msg in messages if not msg.get('is_from_me', False)]
        
        if client_messages:
            insights['response_rate'] = round((len(my_messages) / len(client_messages)) * 100, 1)
        
        # Analyze latest message for urgency
        if messages:
            latest = messages[0].get('content', '').lower()
            urgent_keywords = ['urgent', 'asap', 'immediately', 'rush', 'deadline']
            if any(word in latest for word in urgent_keywords):
                insights['urgency_level'] = 'High'
                insights['recommended_action'] = 'Respond quickly - client needs urgent help'
        
        # Simple sentiment analysis
        if messages:
            latest = messages[0].get('content', '').lower()
            positive_words = ['great', 'excellent', 'perfect', 'love', 'amazing', 'wonderful']
            negative_words = ['disappointed', 'problem', 'issue', 'wrong', 'bad', 'terrible']
            
            positive_score = sum(1 for word in positive_words if word in latest)
            negative_score = sum(1 for word in negative_words if word in latest)
            
            if positive_score > negative_score:
                insights['client_sentiment'] = 'Positive'
            elif negative_score > positive_score:
                insights['client_sentiment'] = 'Negative'
                insights['recommended_action'] = 'Address concerns - client seems unhappy'
        
        return insights

# Global instance
chat_ai = ChatResponseGenerator()

def initialize_chat_ai():
    """Initialize the global chat AI instance"""
    return chat_ai.load_model()