"""
AI Interview Chat URLs
URL routing for AI interview system endpoints
"""

from django.urls import path
from . import views

app_name = 'ai_interview_chat'

urlpatterns = [
    # ========= 📥 Data Ingestion =========
    path('ingest-chat-context/', views.ingest_chat_context, name='ingest_chat_context'),
    
    # ========= 🎯 Interview Session Management =========
    path('sessions/', views.get_interview_sessions, name='get_interview_sessions'),
    path('sessions/<uuid:session_id>/', views.get_interview_session, name='get_interview_session'),
    path('sessions/<uuid:session_id>/questions/', views.get_session_questions, name='get_session_questions'),
    path('sessions/<uuid:session_id>/suggest-answer/', views.suggest_answer_for_question, name='suggest_answer_for_question'),
    path('sessions/create/', views.create_interview_session, name='create_interview_session'),
    path('sessions/<uuid:session_id>/start/', views.start_interview, name='start_interview'),
    path('sessions/<uuid:session_id>/complete/', views.complete_interview, name='complete_interview'),
    
    # ========= 🤖 AI Interview Engine =========
    path('generate-smart-responses/', views.generate_smart_responses, name='generate_smart_responses'),
    path('questions/<uuid:question_id>/respond/', views.submit_response, name='submit_response'),
    
    # ========= 🔧 System Management =========
    path('ai/status/', views.get_ai_status, name='get_ai_status'),
    path('ai/initialize/', views.initialize_ai_engine, name='initialize_ai_engine'),
]