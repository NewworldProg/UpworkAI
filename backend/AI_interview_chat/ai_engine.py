"""
AI Interview Engine
Core AI logic using Hugging Face models for interview question generation and response analysis
Optimized for CPU execution on server environments
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from django.utils import timezone
from django.conf import settings

# Hugging Face imports
try:
    from transformers import (
        GPT2LMHeadModel, GPT2Tokenizer,
        AutoTokenizer, AutoModelForCausalLM,
        pipeline, set_seed
    )
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIInterviewEngine:
    """
    Main AI engine for interview question generation and response analysis
    Uses lightweight models optimized for CPU execution
    """
    
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        self.model_configs = {}
        self.is_initialized = False
        
        # Default model configurations (CPU-optimized)
        self.default_configs = {
            'question_generator': {
                'model_name': 'gpt2',  # Lightweight and fast
                'max_length': 150,
                'temperature': 0.8,
                'top_p': 0.9,
                'do_sample': True,
                'pad_token_id': 50256
            },
            'response_analyzer': {
                'model_name': 'distilbert-base-uncased',
                'max_length': 512,
                'temperature': 0.7,
                'top_p': 0.8
            },
            'topic_extractor': {
                'model_name': 'gpt2',
                'max_length': 100,
                'temperature': 0.6,
                'top_p': 0.85
            }
        }
    
    def initialize_models(self, force_reload: bool = False) -> bool:
        """
        Initialize all AI models for CPU execution
        """
        if self.is_initialized and not force_reload:
            logger.info("✅ AI Interview Engine already initialized")
            return True
        
        if not TRANSFORMERS_AVAILABLE:
            logger.error("❌ Transformers library not available")
            return False
        
        try:
            logger.info("🤖 Initializing AI Interview Engine...")
            start_time = time.time()
            
            # Set to CPU-only mode
            device = torch.device('cpu')
            
            # Initialize question generator (GPT-2)
            logger.info("📝 Loading question generator (GPT-2)...")
            self._load_question_generator(device)
            
            # Initialize sentiment/analysis pipeline
            logger.info("🔍 Loading response analyzer...")
            self._load_response_analyzer()
            
            # Initialize topic extractor
            logger.info("🏷️ Loading topic extractor...")
            self._load_topic_extractor(device)
            
            load_time = time.time() - start_time
            self.is_initialized = True
            
            logger.info(f"✅ AI Interview Engine initialized in {load_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI models: {str(e)}")
            return False
    
    def _load_question_generator(self, device):
        """Load GPT-2 model for question generation"""
        model_name = self.default_configs['question_generator']['model_name']
        
        try:
            self.tokenizers['question_generator'] = GPT2Tokenizer.from_pretrained(model_name)
            self.models['question_generator'] = GPT2LMHeadModel.from_pretrained(model_name)
            
            # Move to CPU and set to eval mode
            self.models['question_generator'].to(device)
            self.models['question_generator'].eval()
            
            # Set pad token if not exists
            if self.tokenizers['question_generator'].pad_token is None:
                self.tokenizers['question_generator'].pad_token = self.tokenizers['question_generator'].eos_token
            
            logger.info(f"✅ Question generator loaded: {model_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load question generator: {str(e)}")
            raise
    
    def _load_response_analyzer(self):
        """Load pipeline for response analysis"""
        try:
            # Use sentiment analysis pipeline (lightweight)
            self.pipelines['sentiment'] = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1  # Force CPU
            )
            
            # Use text classification for topic analysis
            self.pipelines['classifier'] = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # Force CPU
            )
            
            logger.info("✅ Response analyzer pipelines loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load response analyzer: {str(e)}")
            # Fall back to basic analysis if advanced pipelines fail
            self.pipelines['sentiment'] = None
            self.pipelines['classifier'] = None
    
    def _load_topic_extractor(self, device):
        """Load model for extracting topics from chat content"""
        model_name = self.default_configs['topic_extractor']['model_name']
        
        try:
            # Reuse GPT-2 tokenizer and model for topic extraction
            self.tokenizers['topic_extractor'] = self.tokenizers['question_generator']
            self.models['topic_extractor'] = self.models['question_generator']
            
            logger.info("✅ Topic extractor configured (shared GPT-2)")
            
        except Exception as e:
            logger.error(f"❌ Failed to configure topic extractor: {str(e)}")
            raise
    
    def extract_topics_from_chat(self, chat_data: Dict[str, Any]) -> List[str]:
        """
        Extract key topics and skills from chat conversation
        """
        try:
            if not self.is_initialized:
                self.initialize_models()
            
            # Handle both dict and list input
            if isinstance(chat_data, list):
                # If chat_data is a list, assume it's the messages directly
                messages = chat_data
            elif isinstance(chat_data, dict):
                # If chat_data is a dict, extract messages
                messages = chat_data.get('messages', [])
            else:
                logger.error(f"Invalid chat_data type: {type(chat_data)}")
                return []
            
            if not messages:
                return []
            
            # Combine message content
            combined_text = ""
            for msg in messages[-10:]:  # Last 10 messages for context
                content = msg.get('content', '').strip()
                if content and len(content) > 10:  # Skip very short messages
                    combined_text += f" {content}"
            
            if not combined_text.strip():
                return []
            
            # Extract topics using keyword matching and simple NLP
            topics = self._extract_keywords(combined_text)
            
            # Use AI classifier if available
            if self.pipelines.get('classifier'):
                ai_topics = self._classify_topics_ai(combined_text)
                topics.extend(ai_topics)
            
            # Remove duplicates and return top topics
            unique_topics = list(set(topics))
            return unique_topics[:10]  # Top 10 topics
            
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords using simple pattern matching"""
        # Common tech/business keywords
        tech_keywords = [
            'python', 'javascript', 'react', 'django', 'api', 'database', 'sql',
            'frontend', 'backend', 'fullstack', 'mobile', 'web development',
            'machine learning', 'ai', 'data', 'analytics', 'cloud', 'aws',
            'project management', 'agile', 'scrum', 'testing', 'deployment'
        ]
        
        text_lower = text.lower()
        found_topics = []
        
        for keyword in tech_keywords:
            if keyword in text_lower:
                found_topics.append(keyword.title())
        
        return found_topics
    
    def _classify_topics_ai(self, text: str) -> List[str]:
        """Use AI classifier to identify topics"""
        try:
            if not self.pipelines.get('classifier'):
                return []
            
            candidate_labels = [
                "software development", "web development", "mobile development",
                "data science", "machine learning", "project management",
                "frontend", "backend", "database", "api development",
                "testing", "deployment", "cloud computing", "security"
            ]
            
            result = self.pipelines['classifier'](text[:512], candidate_labels)
            
            # Return high-confidence topics
            return [label for label, score in zip(result['labels'], result['scores']) if score > 0.3]
            
        except Exception as e:
            logger.error(f"Error in AI topic classification: {str(e)}")
            return []
    
    def generate_interview_questions(self, chat_context: Dict[str, Any], 
                                   question_type: str = "general",
                                   num_questions: int = 3) -> List[Dict[str, Any]]:
        """
        Generate interview questions based on chat context
        """
        try:
            if not self.is_initialized:
                self.initialize_models()
            
            topics = self.extract_topics_from_chat(chat_context)
            
            # Handle both dict and list input for messages
            if isinstance(chat_context, list):
                # If chat_context is a list, assume it's the messages directly
                messages = chat_context
                project_title = ''
            elif isinstance(chat_context, dict):
                # If chat_context is a dict, extract data properly
                messages = chat_context.get('messages', [])
                project_title = chat_context.get('projectTitle', '')
            else:
                logger.error(f"Invalid chat_context type: {type(chat_context)}")
                messages = []
                project_title = ''
            
            questions = []
            
            for i in range(num_questions):
                if i < len(topics):
                    topic = topics[i]
                    question = self._generate_question_for_topic(topic, question_type, messages)
                else:
                    question = self._generate_general_question(question_type)
                
                if question:
                    questions.append({
                        'question_text': question,
                        'question_type': question_type,
                        'related_topics': [topics[i]] if i < len(topics) else [],
                        'difficulty': 'medium',
                        'generated_by_model': 'gpt2',
                        'generation_confidence': 0.8
                    })
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating interview questions: {str(e)}")
            return []
    
    def _generate_question_for_topic(self, topic: str, question_type: str, messages: List[Dict]) -> str:
        """Generate a specific question for a given topic"""
        try:
            # Create context-aware prompt
            prompt = self._create_question_prompt(topic, question_type, messages)
            
            # Generate using GPT-2
            tokenizer = self.tokenizers.get('question_generator')
            model = self.models.get('question_generator')
            
            if not tokenizer or not model:
                return self._fallback_question_generation(topic, question_type)
            
            # Encode prompt
            inputs = tokenizer.encode(prompt, return_tensors='pt', max_length=100, truncation=True)
            
            # Generate
            with torch.no_grad():
                config = self.default_configs['question_generator']
                outputs = model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 50,
                    temperature=config['temperature'],
                    top_p=config['top_p'],
                    do_sample=config['do_sample'],
                    pad_token_id=config['pad_token_id'],
                    num_return_sequences=1
                )
            
            # Decode and clean
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            question = generated_text[len(prompt):].strip()
            
            # Clean up the question
            question = self._clean_generated_question(question)
            
            return question if question else self._fallback_question_generation(topic, question_type)
            
        except Exception as e:
            logger.error(f"Error generating AI question: {str(e)}")
            return self._fallback_question_generation(topic, question_type)
    
    def _create_question_prompt(self, topic: str, question_type: str, messages: List[Dict]) -> str:
        """Create a prompt for question generation"""
        if question_type == "technical":
            return f"Interview question about {topic}: What is your experience with {topic}? "
        elif question_type == "behavioral":
            return f"Behavioral interview question about {topic}: Tell me about a time when you "
        elif question_type == "project":
            return f"Project interview question about {topic}: How would you approach "
        else:
            return f"Interview question about {topic}: Can you explain "
    
    def _clean_generated_question(self, question: str) -> str:
        """Clean up AI-generated question"""
        if not question:
            return ""
        
        # Take first sentence
        sentences = question.split('.')
        if sentences:
            question = sentences[0].strip()
        
        # Ensure it ends with a question mark
        if question and not question.endswith('?'):
            question += "?"
        
        # Capitalize first letter
        if question:
            question = question[0].upper() + question[1:]
        
        return question
    
    def _fallback_question_generation(self, topic: str, question_type: str) -> str:
        """Fallback question generation using templates"""
        templates = {
            "technical": [
                f"What is your experience with {topic}?",
                f"How would you implement {topic} in a project?",
                f"What are the key challenges when working with {topic}?",
                f"Can you explain the benefits of using {topic}?"
            ],
            "behavioral": [
                f"Tell me about a time when you had to learn {topic} quickly.",
                f"Describe a project where you used {topic} successfully.",
                f"How do you stay updated with {topic} best practices?",
                f"What challenges have you faced when working with {topic}?"
            ],
            "project": [
                f"How would you approach a project involving {topic}?",
                f"What considerations would you make when implementing {topic}?",
                f"How would you explain {topic} to a non-technical team member?",
                f"What would be your strategy for testing {topic} functionality?"
            ]
        }
        
        questions = templates.get(question_type, templates["technical"])
        return questions[0] if questions else f"What is your experience with {topic}?"
    
    def _generate_general_question(self, question_type: str) -> str:
        """Generate general interview questions"""
        general_questions = {
            "technical": [
                "What programming languages are you most comfortable with?",
                "How do you approach debugging complex issues?",
                "What is your experience with version control systems?",
                "How do you ensure code quality in your projects?"
            ],
            "behavioral": [
                "Tell me about a challenging project you've worked on.",
                "How do you handle tight deadlines?",
                "Describe a time when you had to work with a difficult team member.",
                "How do you prioritize tasks when working on multiple projects?"
            ],
            "project": [
                "How do you approach planning a new project?",
                "What is your experience with project management methodologies?",
                "How do you handle changing requirements during a project?",
                "What tools do you use for project collaboration?"
            ]
        }
        
        questions = general_questions.get(question_type, general_questions["technical"])
        return questions[0] if questions else "Tell me about your professional experience."
    
    def analyze_response(self, question: str, response: str) -> Dict[str, Any]:
        """
        Analyze candidate response using AI
        """
        try:
            if not response or not response.strip():
                return {
                    'sentiment_score': 0.0,
                    'relevance_score': 0.0,
                    'technical_accuracy': 0.0,
                    'analysis': {'error': 'No response provided'},
                    'needs_follow_up': True
                }
            
            analysis = {}
            
            # Sentiment analysis
            if self.pipelines.get('sentiment'):
                sentiment_result = self.pipelines['sentiment'](response[:512])
                sentiment_score = sentiment_result[0]['score']
                if sentiment_result[0]['label'] == 'NEGATIVE':
                    sentiment_score = -sentiment_score
                analysis['sentiment_score'] = sentiment_score
            else:
                analysis['sentiment_score'] = self._basic_sentiment_analysis(response)
            
            # Basic relevance scoring
            analysis['relevance_score'] = self._calculate_relevance(question, response)
            
            # Technical accuracy (basic keyword matching)
            analysis['technical_accuracy'] = self._assess_technical_accuracy(response)
            
            # Determine if follow-up is needed
            analysis['needs_follow_up'] = (
                analysis['relevance_score'] < 0.6 or 
                len(response.split()) < 10
            )
            
            # Overall assessment
            analysis['analysis'] = {
                'response_length': len(response.split()),
                'contains_examples': 'example' in response.lower() or 'project' in response.lower(),
                'technical_terms': self._count_technical_terms(response),
                'assessment': self._generate_overall_assessment(analysis)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing response: {str(e)}")
            return {
                'sentiment_score': 0.0,
                'relevance_score': 0.0,
                'technical_accuracy': 0.0,
                'analysis': {'error': str(e)},
                'needs_follow_up': True
            }
    
    def _basic_sentiment_analysis(self, text: str) -> float:
        """Basic sentiment analysis using keyword matching"""
        positive_words = ['good', 'great', 'excellent', 'successful', 'effective', 'efficient', 'love', 'enjoy']
        negative_words = ['bad', 'difficult', 'challenging', 'problem', 'issue', 'struggle', 'hate', 'dislike']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        # Simple scoring
        score = (positive_count - negative_count) / max(total_words * 0.1, 1)
        return max(-1.0, min(1.0, score))
    
    def _calculate_relevance(self, question: str, response: str) -> float:
        """Calculate relevance between question and response"""
        question_words = set(question.lower().split())
        response_words = set(response.lower().split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        question_words -= common_words
        response_words -= common_words
        
        if not question_words:
            return 0.5
        
        overlap = len(question_words.intersection(response_words))
        return min(1.0, overlap / len(question_words))
    
    def _assess_technical_accuracy(self, response: str) -> float:
        """Assess technical accuracy based on keyword presence"""
        technical_terms = self._count_technical_terms(response)
        response_length = len(response.split())
        
        if response_length == 0:
            return 0.0
        
        # Simple scoring based on technical term density
        density = technical_terms / max(response_length * 0.1, 1)
        return min(1.0, density)
    
    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms in response"""
        tech_terms = [
            'api', 'database', 'sql', 'python', 'javascript', 'react', 'django',
            'frontend', 'backend', 'server', 'client', 'framework', 'library',
            'algorithm', 'data structure', 'testing', 'debugging', 'optimization',
            'scalability', 'performance', 'security', 'authentication', 'deployment'
        ]
        
        text_lower = text.lower()
        return sum(1 for term in tech_terms if term in text_lower)
    
    def _generate_overall_assessment(self, analysis: Dict) -> str:
        """Generate overall assessment text"""
        relevance = analysis.get('relevance_score', 0)
        sentiment = analysis.get('sentiment_score', 0)
        technical = analysis.get('technical_accuracy', 0)
        
        avg_score = (relevance + sentiment + technical) / 3
        
        if avg_score >= 0.7:
            return "Strong response with good technical insight and relevance."
        elif avg_score >= 0.5:
            return "Adequate response, but could benefit from more detail or examples."
        else:
            return "Response needs improvement in relevance and technical depth."
    
    def generate_follow_up_question(self, original_question: str, response: str, 
                                  analysis: Dict[str, Any]) -> Optional[str]:
        """
        Generate follow-up question based on response analysis
        """
        try:
            if analysis.get('relevance_score', 0) < 0.5:
                return f"Could you provide more specific details about {original_question.split()[-1]}?"
            
            if analysis.get('technical_accuracy', 0) < 0.5:
                return "Can you give a concrete example from your experience?"
            
            if 'example' not in response.lower():
                return "Could you walk me through a specific example where you applied this?"
            
            # Generate deeper dive questions
            if 'challenge' in response.lower():
                return "What specific strategies did you use to overcome those challenges?"
            
            return "What would you do differently if you encountered a similar situation again?"
            
        except Exception as e:
            logger.error(f"Error generating follow-up: {str(e)}")
            return "Could you elaborate on your previous answer?"

    def suggest_answer_from_chat(self, question: str, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest answer to interview question based on chat conversation history
        """
        try:
            if not self.is_initialized:
                self.initialize_models()
            
            # Handle both dict and list input
            if isinstance(chat_data, list):
                # If chat_data is a list, assume it's the messages directly
                messages = chat_data
            elif isinstance(chat_data, dict):
                # If chat_data is a dict, extract messages
                messages = chat_data.get('messages', [])
            else:
                logger.error(f"Invalid chat_data type: {type(chat_data)}")
                messages = []
                
            if not messages:
                return {
                    'suggested_answer': 'No chat context available to generate answer.',
                    'confidence': 0.0,
                    'key_points': [],
                    'evidence_from_chat': []
                }
            
            # Extract relevant information from chat
            relevant_messages = self._find_relevant_chat_messages(question, messages)
            
            # Generate answer based on chat context
            suggested_answer = self._generate_answer_from_context(question, relevant_messages)
            
            # Extract key points and evidence
            key_points = self._extract_key_points_from_messages(relevant_messages)
            evidence = self._extract_evidence_from_messages(relevant_messages, question)
            
            # Calculate confidence score
            confidence = self._calculate_answer_confidence(question, relevant_messages)
            
            return {
                'suggested_answer': suggested_answer,
                'confidence': confidence,
                'key_points': key_points,
                'evidence_from_chat': evidence,
                'source_messages': len(relevant_messages)
            }
            
        except Exception as e:
            logger.error(f"Error suggesting answer from chat: {str(e)}")
            return {
                'suggested_answer': 'Unable to generate answer suggestion.',
                'confidence': 0.0,
                'key_points': [],
                'evidence_from_chat': [],
                'error': str(e)
            }
    
    def generate_smart_responses_from_chat(self, chat_data, context=None):
        """
        Generate smart response suggestions based on chat conversation without requiring manual questions.
        Analyzes chat context and suggests intelligent responses that could be used in the conversation.
        
        Args:
            chat_data (dict): Chat data with messages and context
            context (dict): Additional context information
            
        Returns:
            list: Smart response suggestions with confidence scores and context
        """
        try:
            logger.info("Starting smart response generation from chat")
            
            if not self.is_initialized:
                self.initialize_models()
            
            # Handle different input types
            if isinstance(chat_data, list):
                messages = chat_data
                chat_context = {'messages': messages}
            elif isinstance(chat_data, dict):
                messages = chat_data.get('messages', [])
                chat_context = chat_data
            else:
                logger.error(f"Invalid chat_data type: {type(chat_data)}")
                return []
            
            # Debug logging
            logger.info(f"🔍 Processing {len(messages)} messages")
            logger.info(f"🔍 Chat context keys: {list(chat_context.keys())}")
            if messages:
                logger.info(f"🔍 Sample messages: {messages[:3]}")
                logger.info(f"🔍 Total message count: {len(messages)}")
            
            if not messages:
                logger.warning("No messages found in chat data")
                return []
            
            # Extract topics and key themes from conversation
            topics = self.extract_topics_from_chat(chat_context)
            
            # Analyze conversation flow and context
            conversation_analysis = self._analyze_conversation_flow(messages)
            
            # Generate multiple smart response suggestions
            smart_responses = []
            
            # Generate responses based on different strategies
            response_strategies = []
            
            # Strategy 1: Followup Response
            try:
                followup = self._generate_followup_response(messages, topics, conversation_analysis)
                if followup:
                    response_strategies.append(followup)
                    logger.info(f"✅ Generated followup response")
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate followup response: {e}")
            
            # Strategy 2: Clarification Response
            try:
                clarification = self._generate_clarification_response(messages, topics)
                if clarification:
                    response_strategies.append(clarification)
                    logger.info(f"✅ Generated clarification response")
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate clarification response: {e}")
            
            # Strategy 3: Expertise Response
            try:
                expertise = self._generate_expertise_response(messages, topics)
                if expertise:
                    response_strategies.append(expertise)
                    logger.info(f"✅ Generated expertise response")
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate expertise response: {e}")
            
            # Strategy 4: Experience Response
            try:
                experience = self._generate_experience_response(messages, topics)
                if experience:
                    response_strategies.append(experience)
                    logger.info(f"✅ Generated experience response")
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate experience response: {e}")
            
            # Strategy 5: Project-focused Response
            try:
                project_focused = self._generate_project_focused_response(messages, topics, chat_context)
                if project_focused:
                    response_strategies.append(project_focused)
                    logger.info(f"✅ Generated project-focused response")
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate project-focused response: {e}")
            
            # Add fallback responses if we don't have enough
            if len(response_strategies) < 3:
                logger.info("Adding fallback responses...")
                fallback_responses = self._generate_fallback_responses(messages, topics, chat_context)
                response_strategies.extend(fallback_responses)
            
            logger.info(f"🔍 Generated {len(response_strategies)} total responses")
            
            logger.info(f"🔍 Generated {len(response_strategies)} total responses")
            
            # Sort by confidence score
            response_strategies.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            # Return top 5 responses
            final_responses = response_strategies[:5]
            logger.info(f"🎯 Returning {len(final_responses)} smart responses")
            
            return final_responses
            
        except Exception as e:
            logger.error(f"Error generating smart responses: {str(e)}")
            return []
    
    def _analyze_conversation_flow(self, messages):
        """Analyze the flow and context of conversation"""
        try:
            if not messages:
                return {}
            
            # Get recent messages (last 5)
            recent_messages = messages[-5:] if len(messages) > 5 else messages
            
            # Analyze message patterns
            authors = [msg.get('author', 'Unknown') for msg in recent_messages]
            last_author = authors[-1] if authors else 'Unknown'
            
            # Determine conversation phase
            total_messages = len(messages)
            if total_messages <= 3:
                phase = 'opening'
            elif total_messages <= 10:
                phase = 'exploration'
            else:
                phase = 'deep_discussion'
            
            # Extract last message context
            last_message = recent_messages[-1] if recent_messages else {}
            last_content = last_message.get('content', '')
            
            return {
                'phase': phase,
                'last_author': last_author,
                'last_content': last_content,
                'recent_messages': recent_messages,
                'total_messages': total_messages,
                'is_question': '?' in last_content,
                'mentions_experience': any(word in last_content.lower() for word in ['experience', 'worked', 'project', 'skill'])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing conversation flow: {str(e)}")
            return {}
    
    def _generate_followup_response(self, messages, topics, analysis):
        """Generate a natural follow-up response based on conversation flow"""
        try:
            if not analysis.get('last_content'):
                return None
            
            last_content = analysis['last_content']
            
            # Create context-aware prompt
            prompt = f"""Based on this conversation context, suggest a natural follow-up response:
            
            Last message: "{last_content}"
            Topics discussed: {', '.join(topics[:3])}
            Conversation phase: {analysis.get('phase', 'discussion')}
            
            Generate a professional, relevant response (2-3 sentences):"""
            
            # Generate response using GPT-2
            if self.models.get('question_generator') and self.tokenizers.get('question_generator'):
                inputs = self.tokenizers['question_generator'].encode(prompt, return_tensors='pt', max_length=200, truncation=True)
                
                with torch.no_grad():
                    outputs = self.models['question_generator'].generate(
                        inputs,
                        max_new_tokens=50,
                        num_return_sequences=1,
                        temperature=0.8,
                        do_sample=True,
                        pad_token_id=self.tokenizers['question_generator'].eos_token_id
                    )
                
                response_text = self.tokenizers['question_generator'].decode(outputs[0], skip_special_tokens=True)
                # Extract generated part
                input_text = self.tokenizers['question_generator'].decode(inputs[0], skip_special_tokens=True)
                generated_response = response_text[len(input_text):].strip()
                
                # Clean up the generated response
                if generated_response and len(generated_response) > 10:
                    # Remove any repeated content and fix formatting
                    lines = generated_response.split('\n')
                    clean_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and line not in clean_lines and len(line) > 5:
                            clean_lines.append(line)
                    
                    if clean_lines:
                        final_response = clean_lines[0]  # Take first clean line
                        # Ensure proper sentence ending
                        if not final_response.endswith('.') and not final_response.endswith('?') and not final_response.endswith('!'):
                            if '?' in final_response:
                                final_response = final_response.split('?')[0] + '?'
                            else:
                                final_response += '.'
                        
                        return {
                            'response': final_response,
                            'type': 'followup',
                            'confidence': 0.75,
                            'context': f"Natural follow-up to: {last_content[:100]}...",
                            'topics': topics[:3]
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating follow-up response: {str(e)}")
            return None
    
    def _generate_clarification_response(self, messages, topics):
        """Generate a clarifying question or response"""
        try:
            if not topics:
                return None
            
            # Template-based clarification responses
            clarification_templates = [
                f"Could you tell me more about your experience with {topics[0]}?",
                f"What specific aspects of {topics[0]} have you worked with?",
                f"How long have you been working with {topics[0]}?",
                f"What challenges have you faced when working with {topics[0]}?",
                f"Can you share an example of a {topics[0]} project you've completed?"
            ]
            
            import random
            selected_template = random.choice(clarification_templates)
            
            return {
                'response': selected_template,
                'type': 'clarification',
                'confidence': 0.70,
                'context': f"Seeking clarification about {topics[0]}",
                'topics': topics[:2]
            }
            
        except Exception as e:
            logger.error(f"Error generating clarification response: {str(e)}")
            return None
    
    def _generate_expertise_response(self, messages, topics):
        """Generate a response showcasing expertise in discussed topics"""
        try:
            if not topics:
                return None
            
            # Template-based expertise responses
            expertise_templates = [
                f"I have extensive experience with {topics[0]}, particularly in building scalable solutions.",
                f"My background in {topics[0]} includes both development and optimization work.",
                f"I've successfully implemented {topics[0]} solutions for various client projects.",
                f"In my experience with {topics[0]}, I've found that proper architecture is crucial.",
                f"I'm particularly strong in {topics[0]} development and best practices."
            ]
            
            import random
            selected_template = random.choice(expertise_templates)
            
            return {
                'response': selected_template,
                'type': 'expertise',
                'confidence': 0.65,
                'context': f"Demonstrating expertise in {topics[0]}",
                'topics': topics[:2]
            }
            
        except Exception as e:
            logger.error(f"Error generating expertise response: {str(e)}")
            return None
    
    def _generate_experience_response(self, messages, topics):
        """Generate a response sharing relevant experience"""
        try:
            if not topics:
                return None
            
            # Template-based experience responses
            experience_templates = [
                f"In my recent projects, I've worked extensively with {topics[0]} to solve complex challenges.",
                f"I have hands-on experience implementing {topics[0]} solutions in production environments.",
                f"My work with {topics[0]} has involved both frontend and backend development.",
                f"I've been working with {topics[0]} for several years across different types of projects.",
                f"One of my strongest areas is {topics[0]} development and system integration."
            ]
            
            import random
            selected_template = random.choice(experience_templates)
            
            return {
                'response': selected_template,
                'type': 'experience',
                'confidence': 0.68,
                'context': f"Sharing experience with {topics[0]}",
                'topics': topics[:2]
            }
            
        except Exception as e:
            logger.error(f"Error generating experience response: {str(e)}")
            return None
    
    def _generate_project_focused_response(self, messages, topics, chat_context):
        """Generate a response focused on project requirements"""
        try:
            project_title = chat_context.get('projectTitle', chat_context.get('project_title', ''))
            
            if not topics:
                return None
            
            # Template-based project responses
            if project_title:
                project_templates = [
                    f"For this {project_title} project, my {topics[0]} expertise would be particularly valuable.",
                    f"I understand the requirements for {project_title} and have relevant {topics[0]} experience.",
                    f"My background in {topics[0]} aligns well with the {project_title} project goals.",
                    f"I can contribute to {project_title} by leveraging my {topics[0]} skills and experience."
                ]
            else:
                project_templates = [
                    f"For this project, my {topics[0]} expertise would be particularly valuable.",
                    f"I understand the project requirements and have relevant {topics[0]} experience.",
                    f"My background in {topics[0]} aligns well with the project goals.",
                    f"I can contribute by leveraging my {topics[0]} skills and experience."
                ]
            
            import random
            selected_template = random.choice(project_templates)
            
            return {
                'response': selected_template,
                'type': 'project_focused',
                'confidence': 0.72,
                'context': f"Project-focused response about {topics[0]}",
                'topics': topics[:2]
            }
            
        except Exception as e:
            logger.error(f"Error generating project-focused response: {str(e)}")
            return None
    
    def _generate_fallback_responses(self, messages, topics, chat_context):
        """Generate fallback responses when primary strategies fail"""
        fallback_responses = []
        
        try:
            # Generic professional responses
            generic_responses = [
                {
                    'response': "I'd be happy to discuss this further and provide more details about my background.",
                    'type': 'generic',
                    'confidence': 0.60,
                    'context': 'Generic professional response',
                    'topics': topics[:2] if topics else ['general']
                },
                {
                    'response': "Thank you for considering my application. I believe my skills align well with your project requirements.",
                    'type': 'generic',
                    'confidence': 0.58,
                    'context': 'Professional closing response',
                    'topics': topics[:2] if topics else ['general']
                },
                {
                    'response': "I'm excited about the opportunity to contribute to this project and would welcome the chance to discuss it further.",
                    'type': 'generic',
                    'confidence': 0.55,
                    'context': 'Enthusiasm and next steps',
                    'topics': topics[:2] if topics else ['general']
                }
            ]
            
            # Topic-specific responses if we have topics
            if topics:
                topic_responses = [
                    {
                        'response': f"I have relevant experience with {topics[0]} that would be valuable for this project.",
                        'type': 'topic_specific',
                        'confidence': 0.65,
                        'context': f'Topic-specific experience with {topics[0]}',
                        'topics': topics[:2]
                    },
                    {
                        'response': f"My expertise in {topics[0]} includes both practical implementation and best practices.",
                        'type': 'topic_specific',
                        'confidence': 0.62,
                        'context': f'Expertise demonstration in {topics[0]}',
                        'topics': topics[:2]
                    }
                ]
                fallback_responses.extend(topic_responses)
            
            fallback_responses.extend(generic_responses)
            
            return fallback_responses[:3]  # Return max 3 fallback responses
            
        except Exception as e:
            logger.error(f"Error generating fallback responses: {str(e)}")
            return []

    def _find_relevant_chat_messages(self, question: str, messages: List[Dict]) -> List[Dict]:
        """Find messages relevant to the interview question"""
        try:
            question_lower = question.lower()
            relevant_messages = []
            
            # Keywords to look for based on question content
            keywords = self._extract_question_keywords(question_lower)
            
            for msg in messages:
                content = msg.get('content', '').lower()
                
                # Check if message contains relevant keywords
                relevance_score = 0
                for keyword in keywords:
                    if keyword in content:
                        relevance_score += 1
                
                # Include messages with high relevance or from specific authors
                if relevance_score > 0 or len(content) > 50:
                    relevant_messages.append({
                        **msg,
                        'relevance_score': relevance_score
                    })
            
            # Sort by relevance and limit to most relevant
            relevant_messages.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            return relevant_messages[:10]  # Top 10 most relevant
            
        except Exception as e:
            logger.error(f"Error finding relevant messages: {str(e)}")
            return messages[-5:]  # Fallback to last 5 messages
    
    def _extract_question_keywords(self, question: str) -> List[str]:
        """Extract keywords from interview question"""
        # Common interview question keywords
        keywords = []
        
        if 'experience' in question:
            keywords.extend(['work', 'project', 'experience', 'used', 'worked'])
        if 'challenge' in question:
            keywords.extend(['problem', 'difficult', 'challenge', 'issue'])
        if 'skill' in question or 'technology' in question:
            keywords.extend(['python', 'javascript', 'programming', 'code', 'develop'])
        if 'team' in question:
            keywords.extend(['team', 'collaborate', 'work together', 'communication'])
        if 'project' in question:
            keywords.extend(['project', 'build', 'create', 'develop', 'implement'])
        
        return keywords
    
    def _generate_answer_from_context(self, question: str, messages: List[Dict]) -> str:
        """Generate answer based on chat context"""
        try:
            if not messages:
                return "Based on our conversation, I don't have specific details to address this question directly."
            
            # Combine relevant message content
            context_text = ""
            for msg in messages[:5]:  # Use top 5 relevant messages
                content = msg.get('content', '').strip()
                author = msg.get('author', '')
                if content and len(content) > 10:
                    context_text += f"{author}: {content}\n"
            
            if not context_text.strip():
                return "Based on our conversation, I would need to provide more specific details about my experience."
            
            # Generate structured answer
            answer_parts = []
            
            # Opening based on question type
            if 'experience' in question.lower():
                answer_parts.append("Based on our previous conversation,")
            elif 'challenge' in question.lower():
                answer_parts.append("From what we discussed,")
            else:
                answer_parts.append("As mentioned in our chat,")
            
            # Add context-based content
            if 'python' in context_text.lower() or 'programming' in context_text.lower():
                answer_parts.append("I have experience with Python programming and development.")
            
            if 'project' in context_text.lower():
                answer_parts.append("I've worked on various projects that demonstrate my capabilities.")
            
            if 'team' in context_text.lower() or 'collaborate' in context_text.lower():
                answer_parts.append("I'm comfortable working in team environments and collaborating with others.")
            
            # Fallback if no specific content found
            if len(answer_parts) == 1:
                answer_parts.append("I'm ready to contribute my skills and experience to achieve the project goals.")
            
            return " ".join(answer_parts)
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "I'm excited about this opportunity and ready to discuss my qualifications in more detail."
    
    def _extract_key_points_from_messages(self, messages: List[Dict]) -> List[str]:
        """Extract key points from relevant messages"""
        key_points = []
        
        try:
            for msg in messages[:3]:  # Top 3 messages
                content = msg.get('content', '').strip()
                if len(content) > 20:
                    # Truncate long messages and add as key point
                    if len(content) > 100:
                        content = content[:97] + "..."
                    key_points.append(content)
            
            return key_points
            
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            return []
    
    def _extract_evidence_from_messages(self, messages: List[Dict], question: str) -> List[Dict]:
        """Extract evidence from chat that supports the answer"""
        evidence = []
        
        try:
            for msg in messages[:3]:
                content = msg.get('content', '')
                author = msg.get('author', '')
                
                if len(content) > 15:
                    evidence.append({
                        'message': content[:150] + "..." if len(content) > 150 else content,
                        'author': author,
                        'relevance': 'Contains relevant context for the question'
                    })
            
            return evidence
            
        except Exception as e:
            logger.error(f"Error extracting evidence: {str(e)}")
            return []
    
    def _calculate_answer_confidence(self, question: str, messages: List[Dict]) -> float:
        """Calculate confidence score for suggested answer"""
        try:
            if not messages:
                return 0.1
            
            # Base confidence on number of relevant messages and content quality
            relevance_score = sum(msg.get('relevance_score', 0) for msg in messages)
            content_score = sum(1 for msg in messages if len(msg.get('content', '')) > 30)
            
            # Normalize scores
            max_possible_relevance = len(messages) * 3  # Max 3 keywords per message
            max_possible_content = len(messages)
            
            if max_possible_relevance > 0 and max_possible_content > 0:
                normalized_relevance = min(relevance_score / max_possible_relevance, 1.0)
                normalized_content = min(content_score / max_possible_content, 1.0)
                
                # Combine scores
                confidence = (normalized_relevance * 0.6 + normalized_content * 0.4)
                return min(max(confidence, 0.1), 0.9)  # Keep between 0.1 and 0.9
            
            return 0.3  # Default confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.2

# Global instance
ai_interview_engine = AIInterviewEngine()