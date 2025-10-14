from django.db import models

class Project(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('proposal_ready', 'Proposal Ready'),
        ('accepted', 'Accepted'),
        ('scraped', 'Scraped'),  # New status for scraped jobs
    ]

    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    budget = models.CharField(max_length=128, blank=True)
    skills_required = models.CharField(max_length=512, blank=True)
    deadline = models.DateField(null=True, blank=True)
    url = models.URLField(max_length=1024, blank=True)
    language = models.CharField(max_length=16, blank=True)
    client = models.CharField(max_length=256, blank=True)
    # provenance / TOS-safe metadata
    source_url = models.URLField(max_length=1024, blank=True, help_text='Original source URL')
    fetched_at = models.DateTimeField(null=True, blank=True, help_text='When the source was fetched')
    fetch_method = models.CharField(max_length=32, blank=True, help_text='api|scrape|manual')
    saved_pdf_path = models.CharField(max_length=1024, blank=True, help_text='Optional path to saved PDF')
    tos_safe = models.BooleanField(default=False, help_text='True when ingestion follows TOS-safe/manual workflow')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='new')
    match_score = models.FloatField(null=True, blank=True)
    cover_letter = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New fields for scraped jobs integration
    time_posted = models.CharField(max_length=100, blank=True, help_text='When job was posted (e.g. "1 day ago")')
    scraped_at = models.DateTimeField(null=True, blank=True, help_text='When this job was scraped')
    is_scraped = models.BooleanField(default=False, help_text='True if this project came from scraping')
    scrape_source = models.CharField(max_length=50, default='manual', help_text='manual|logged-in-chrome|universal-dom')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"


class Skillset(models.Model):
    """A named collection of skills a client can save and reuse."""
    name = models.CharField(max_length=128)
    skills = models.CharField(max_length=512, blank=True, help_text='Comma-separated skills')
    owner = models.CharField(max_length=128, blank=True, help_text='Optional client identifier')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}: {self.skills}"
