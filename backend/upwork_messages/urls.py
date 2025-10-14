"""
Upwork Messages URLs
URL patterns for Upwork messages and AI chat API endpoints
"""

from django.urls import path
from . import views

urlpatterns = [
    path('extract/', views.extract_and_save_messages, name='extract_and_save_messages'),
    path('extract/status/', views.get_extraction_status, name='get_extraction_status'),
    path('messages/', views.get_all_messages, name='get_all_messages'),
    path('chats/', views.get_chats_with_messages, name='get_chats'),
    path('chats/<str:chat_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('chats/<str:chat_id>/messages/', views.get_chat_messages, name='get_chat_messages_alt'),
    path('chats/<str:chat_id>/ai-suggestions/', views.suggest_ai_replies, name='suggest_ai_replies'),
    path('ai/suggest-replies/', views.suggest_ai_replies, name='suggest_ai_replies_global'),
    path('ai/generate-response/', views.generate_ai_response, name='generate_ai_response'),
    path('ai/analyze-active-chat/', views.analyze_active_chat, name='analyze_active_chat'),
    path('chrome/open-message/', views.open_message_in_chrome, name='open_message_in_chrome'),
]