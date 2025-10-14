"""
Notification Push Models
Database models for job monitoring and notification management
"""
from django.db import models
from django.utils import timezone
import json

class Job(models.Model):
    """Upwork job/project model"""
    job_id = models.CharField(max_length=255, unique=True)  # Upwork job ID
    title = models.CharField(max_length=500)
    description = models.TextField()
    client_name = models.CharField(max_length=255, blank=True)
    budget = models.CharField(max_length=100, blank=True)  # e.g. "$500 - $1000"
    hourly_rate = models.CharField(max_length=100, blank=True)  # e.g. "$15-25/hr"
    
    # Job metadata
    posted_date = models.DateTimeField()
    deadline = models.DateTimeField(null=True, blank=True)
    job_url = models.URLField()
    location = models.CharField(max_length=255, blank=True)
    job_type = models.CharField(max_length=50, blank=True)  # hourly, fixed, etc.
    
    # Tracking
    is_applied = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Technical metadata
    selector_used = models.CharField(max_length=255, blank=True)
    html_snippet = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-posted_date', '-scraped_at']
    
    def __str__(self):
        return f"{self.title[:50]}... - {self.client_name}"

class ScrapingSession(models.Model):
    """Log of scraping sessions"""
    session_id = models.CharField(max_length=255, unique=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Session details
    page_url = models.URLField()
    total_jobs_found = models.IntegerField(default=0)
    new_jobs_saved = models.IntegerField(default=0)
    selector_used = models.CharField(max_length=255, blank=True)
    
    # Status
    status = models.CharField(max_length=50, default='running')  # running, completed, failed
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Session {self.session_id}: {self.new_jobs_saved} new jobs"

class Notification(models.Model):
    """System notifications and alerts"""
    notification_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Notification type
    type = models.CharField(max_length=50, default='info')  # info, warning, error, success
    source = models.CharField(max_length=100, default='system')  # system, upwork, scraper
    
    # Related objects
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    session = models.ForeignKey(ScrapingSession, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Status
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Metadata
    data = models.JSONField(default=dict, blank=True)  # Additional data as JSON
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.type.upper()}: {self.title}"

class ChromeSession(models.Model):
    """Chrome browser session tracking"""
    session_id = models.CharField(max_length=255, unique=True)
    debug_port = models.IntegerField(default=9222)
    started_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    tabs_count = models.IntegerField(default=0)
    current_url = models.URLField(blank=True)
    
    # Configuration
    user_data_dir = models.CharField(max_length=500, blank=True)
    chrome_executable = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Chrome Session {self.session_id} on port {self.debug_port}"