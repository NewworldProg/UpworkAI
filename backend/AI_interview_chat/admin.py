"""
AI Interview Chat Admin
Django admin configuration for interview system models
"""

from django.contrib import admin
from .models import ChatContext, InterviewSession, InterviewQuestion, InterviewResponse, AIModelConfig


@admin.register(ChatContext)
class ChatContextAdmin(admin.ModelAdmin):
    list_display = ('context_id', 'project_title', 'client_name', 'total_messages', 'extracted_at', 'is_active')
    list_filter = ('is_active', 'extracted_at', 'project_type')
    search_fields = ('project_title', 'chat_title', 'client_name', 'participants')
    readonly_fields = ('context_id', 'extracted_at', 'created_at', 'updated_at')
    ordering = ('-extracted_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('context_id', 'project_title', 'chat_title', 'url', 'is_active')
        }),
        ('Participants & Content', {
            'fields': ('participants', 'client_name', 'total_messages', 'key_topics')
        }),
        ('Analysis', {
            'fields': ('project_type', 'messages'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('extracted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'session_name', 'candidate_name', 'interview_type', 'status', 'total_questions', 'created_at')
    list_filter = ('status', 'interview_type', 'difficulty_level', 'created_at')
    search_fields = ('session_name', 'candidate_name', 'interviewer_name')
    readonly_fields = ('session_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Session Info', {
            'fields': ('session_id', 'session_name', 'candidate_name', 'interviewer_name')
        }),
        ('Configuration', {
            'fields': ('chat_context', 'interview_type', 'difficulty_level', 'status')
        }),
        ('Statistics', {
            'fields': ('total_questions', 'total_responses', 'average_response_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_id', 'session', 'question_type', 'difficulty', 'generated_by_model', 'asked_at')
    list_filter = ('question_type', 'difficulty', 'generated_by_model', 'created_at')
    search_fields = ('question_text', 'related_topics')
    readonly_fields = ('question_id', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Question Info', {
            'fields': ('question_id', 'session', 'question_text', 'question_type')
        }),
        ('Configuration', {
            'fields': ('difficulty', 'related_topics', 'based_on_message')
        }),
        ('AI Generation', {
            'fields': ('generated_by_model', 'generation_confidence'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'asked_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(InterviewResponse)
class InterviewResponseAdmin(admin.ModelAdmin):
    list_display = ('response_id', 'question', 'sentiment_score', 'relevance_score', 'needs_follow_up', 'created_at')
    list_filter = ('needs_follow_up', 'is_satisfactory', 'follow_up_type', 'created_at')
    search_fields = ('response_text', 'follow_up_question')
    readonly_fields = ('response_id', 'created_at', 'analyzed_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Response Info', {
            'fields': ('response_id', 'question', 'response_text', 'response_time_seconds')
        }),
        ('AI Analysis', {
            'fields': ('sentiment_score', 'relevance_score', 'technical_accuracy', 'ai_analysis')
        }),
        ('Follow-up', {
            'fields': ('follow_up_question', 'follow_up_type', 'needs_follow_up', 'is_satisfactory')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'analyzed_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(AIModelConfig)
class AIModelConfigAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'model_type', 'is_active', 'is_loaded', 'use_cpu', 'last_used')
    list_filter = ('model_type', 'is_active', 'is_loaded', 'use_cpu')
    search_fields = ('model_name', 'model_path')
    readonly_fields = ('config_id', 'created_at', 'updated_at', 'last_used')
    ordering = ('model_type', 'model_name')
    
    fieldsets = (
        ('Model Info', {
            'fields': ('config_id', 'model_name', 'model_type', 'model_path')
        }),
        ('Generation Settings', {
            'fields': ('max_length', 'temperature', 'top_p', 'do_sample')
        }),
        ('Performance Settings', {
            'fields': ('use_cpu', 'batch_size', 'cache_size')
        }),
        ('Status', {
            'fields': ('is_active', 'is_loaded', 'load_time_seconds')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_used'),
            'classes': ('collapse',)
        })
    )
