from django.db import models
from django.utils import timezone

class Chat(models.Model):
    """Chat/Conversation model"""
    chat_id = models.CharField(max_length=255, unique=True)  # Upwork conversation ID
    sender_name = models.CharField(max_length=255)           # Client/Freelancer name
    chat_url = models.URLField(blank=True)                   # Direct link to conversation
    last_activity = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Chat metadata
    total_messages = models.IntegerField(default=0)
    unread_count = models.IntegerField(default=0)
    chat_type = models.CharField(max_length=50, default='client')  # client, support, etc.
    
    class Meta:
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"Chat with {self.sender_name} ({self.chat_id})"

class Message(models.Model):
    """Individual message model"""
    message_id = models.CharField(max_length=255, unique=True)  # Unique message ID
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    
    # Message content
    sender = models.CharField(max_length=255)
    content = models.TextField()
    preview = models.CharField(max_length=500, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField()                        # Original message time
    extracted_at = models.DateTimeField(auto_now_add=True)   # When we scraped it
    
    # Message status
    is_read = models.BooleanField(default=False)
    is_from_me = models.BooleanField(default=False)  # Did I send this message
    is_outgoing = models.BooleanField(default=False)  # Alias for is_from_me for compatibility
    
    # Technical metadata
    selector_used = models.CharField(max_length=255, blank=True)  # CSS selector that found this
    html_snippet = models.TextField(blank=True)                  # Raw HTML for debugging
    
    class Meta:
        ordering = ['-timestamp']
        unique_together = ['message_id', 'chat']
    
    def __str__(self):
        return f"Message from {self.sender}: {self.preview[:50]}..."

class MessageExtractionLog(models.Model):
    """Log of message extraction sessions"""
    extraction_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    page_url = models.URLField()
    total_messages_found = models.IntegerField(default=0)
    new_messages_saved = models.IntegerField(default=0)
    selector_used = models.CharField(max_length=255, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Extraction {self.extraction_id}: {self.new_messages_saved} new messages"
