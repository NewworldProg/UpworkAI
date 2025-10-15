"""
AI Interview Chat Models
Store interview sessions, chat context, and AI-generated responses
"""

from django.db import models
from django.utils import timezone
import uuid


class ChatContext(models.Model):
    """
    Store active chat data extracted from active_chat_scraper.js
    This serves as training/context data for AI interview responses
    """
    context_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project_title = models.CharField(max_length=500, blank=True, null=True)
    chat_title = models.CharField(max_length=500, blank=True, null=True)
    participants = models.JSONField(default=list)  # List of participant names
    messages = models.JSONField(default=list)  # Full message history from scraper
    url = models.URLField(blank=True, null=True)
    
    # Analysis data
    total_messages = models.IntegerField(default=0)
    client_name = models.CharField(max_length=200, blank=True, null=True)
    project_type = models.CharField(max_length=200, blank=True, null=True)
    key_topics = models.JSONField(default=list)  # Extracted topics/skills mentioned
    
    # Metadata
    extracted_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'ai_interview_chat_context'
        ordering = ['-extracted_at']
    
    def __str__(self):
        return f"ChatContext: {self.chat_title or self.project_title or 'Unknown'} ({self.total_messages} msgs)"


class InterviewSession(models.Model):
    """
    Track AI interview sessions using chat context as reference material
    """
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    chat_context = models.ForeignKey(ChatContext, on_delete=models.CASCADE, related_name='interview_sessions')
    
    # Session info
    session_name = models.CharField(max_length=200, default="AI Interview Session")
    interviewer_name = models.CharField(max_length=100, default="AI Interviewer")
    candidate_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Interview configuration
    interview_type = models.CharField(max_length=50, default="general", choices=[
        ('general', 'General Interview'),
        ('technical', 'Technical Interview'),
        ('behavioral', 'Behavioral Interview'),
        ('project_specific', 'Project-Specific Interview'),
    ])
    difficulty_level = models.CharField(max_length=20, default="medium", choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ])
    
    # Status tracking
    status = models.CharField(max_length=20, default="active", choices=[
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ])
    
    # Statistics
    total_questions = models.IntegerField(default=0)
    total_responses = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)  # seconds
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_interview_session'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Interview: {self.session_name} ({self.status})"
    
    def start_session(self):
        """Mark session as started"""
        self.started_at = timezone.now()
        self.status = 'active'
        self.save()
    
    def complete_session(self):
        """Mark session as completed"""
        self.completed_at = timezone.now()
        self.status = 'completed'
        self.save()


class InterviewQuestion(models.Model):
    """
    Store AI-generated interview questions based on chat context
    """
    question_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='questions')
    
    # Question content
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=[
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('experience', 'Experience'),
        ('project', 'Project-specific'),
        ('skill', 'Skill-based'),
        ('scenario', 'Scenario-based'),
    ])
    
    # Context reference
    based_on_message = models.IntegerField(blank=True, null=True)  # Index in chat_context.messages
    related_topics = models.JSONField(default=list)  # Topics this question covers
    difficulty = models.CharField(max_length=20, default="medium", choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ])
    
    # AI model info
    generated_by_model = models.CharField(max_length=100, default="gpt2")
    generation_confidence = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    asked_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'ai_interview_question'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Q: {self.question_text[:100]}..."


class InterviewResponse(models.Model):
    """
    Store candidate responses and AI-generated follow-up questions
    """
    response_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    question = models.OneToOneField(InterviewQuestion, on_delete=models.CASCADE, related_name='response')
    
    # Response content
    response_text = models.TextField(blank=True, null=True)
    response_time_seconds = models.FloatField(default=0.0)
    
    # AI Analysis
    ai_analysis = models.JSONField(default=dict)  # AI assessment of the response
    sentiment_score = models.FloatField(default=0.0)  # -1 to 1
    relevance_score = models.FloatField(default=0.0)  # 0 to 1
    technical_accuracy = models.FloatField(default=0.0)  # 0 to 1
    
    # AI-generated follow-up
    follow_up_question = models.TextField(blank=True, null=True)
    follow_up_type = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('clarification', 'Clarification'),
        ('deeper', 'Deeper Dive'),
        ('related', 'Related Topic'),
        ('challenge', 'Challenge'),
        ('scenario', 'Scenario Extension'),
    ])
    
    # Status
    needs_follow_up = models.BooleanField(default=False)
    is_satisfactory = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    analyzed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'ai_interview_response'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Response: {self.response_text[:100]}..." if self.response_text else "No response yet"


class AIModelConfig(models.Model):
    """
    Configuration for AI models used in interview system
    """
    config_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    model_name = models.CharField(max_length=100)  # e.g., "gpt2", "distilbert-base-uncased"
    model_type = models.CharField(max_length=50, choices=[
        ('question_generator', 'Question Generator'),
        ('response_analyzer', 'Response Analyzer'),
        ('follow_up_generator', 'Follow-up Generator'),
        ('topic_extractor', 'Topic Extractor'),
    ])
    
    # Model configuration
    model_path = models.CharField(max_length=500)  # Local path or HuggingFace model name
    max_length = models.IntegerField(default=512)
    temperature = models.FloatField(default=0.7)
    top_p = models.FloatField(default=0.9)
    do_sample = models.BooleanField(default=True)
    
    # Performance settings
    use_cpu = models.BooleanField(default=True)  # Perfect for server deployment
    batch_size = models.IntegerField(default=1)
    cache_size = models.IntegerField(default=100)  # Number of cached responses
    
    # Status
    is_active = models.BooleanField(default=True)
    is_loaded = models.BooleanField(default=False)
    load_time_seconds = models.FloatField(default=0.0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'ai_model_config'
        unique_together = ['model_name', 'model_type']
    
    def __str__(self):
        return f"{self.model_name} ({self.model_type})"
