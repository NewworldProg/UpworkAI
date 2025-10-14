"""
AI Cover Letters URL Configuration
"""

from django.urls import path
from . import views

urlpatterns = [
    path('generate-cover-letter/', views.generate_cover_letter, name='generate_cover_letter'),
    path('prompt/', views.direct_prompt, name='direct_prompt'),
    path('status/', views.ai_status, name='ai_status'),
]