"""
NotificationPush URLs
URL patterns for NotificationPush Browser Scraper API endpoints
"""

from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.notification_status, name='notification_status'),
    path('start/', views.start_monitoring, name='start_monitoring'),
    path('stop/', views.stop_monitoring, name='stop_monitoring'),
    path('refresh/', views.refresh_chrome_status, name='refresh_chrome_status'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('jobs/', views.get_jobs, name='get_jobs'),  # Latest session jobs for Captured Jobs
    path('jobs/all/', views.get_all_jobs, name='get_all_jobs'),  # All jobs with pagination for ProjectList
    path('jobs/batch/', views.batch_jobs, name='batch_jobs'),  # Batch job submission
    path('manual-scrape/', views.manual_scrape, name='manual_scrape'),  # Logged-in manual scraper
    path('universal-scrape/', views.universal_scrape, name='universal_scrape'),  # Universal DOM scraper
    path('scraped-projects/', views.get_scraped_projects, name='get_scraped_projects'),  # Get scraped jobs from DB
    path('scrape-messages/', views.scrape_messages, name='scrape_messages'),  # Extract Upwork messages/notifications
    path('save-jobs/', views.save_jobs_to_database_api, name='save_jobs_to_database_api'),  # Direct database save API
    # path('save-scrapes/', views.save_recent_scrapes_to_db, name='save_recent_scrapes_to_db'),  # Manual save scraped jobs - TEMPORARILY DISABLED
]