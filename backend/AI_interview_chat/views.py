"""
AI Interview Chat Views
API endpoints for AI-powered interview system using chat context
"""

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import models
import json
import logging
import uuid

from .models import ChatContext, InterviewSession, InterviewQuestion, InterviewResponse, AIModelConfig
from .ai_engine import ai_interview_engine

logger = logging.getLogger(__name__)

# ========= 📥 Data Ingestion from active_chat_scraper.js =========

@api_view(['POST'])
@permission_classes([AllowAny])
def ingest_chat_context(request):
    """
    Receive and store chat data from active_chat_scraper.js
    This data will be used as context for AI interview generation
    """
    try:
        # Initialize AI models if not already loaded
        try:
            ai_interview_engine.initialize_models()
        except Exception as ai_error:
            logger.warning(f"AI models initialization warning: {ai_error}")
        
        chat_data = request.data
        
        logger.info(f"DEBUG: chat_data type: {type(chat_data)}")
        logger.info(f"DEBUG: chat_data keys: {list(chat_data.keys()) if hasattr(chat_data, 'keys') else 'No keys method'}")
        
        # Validate required fields
        if not chat_data:
            return Response({
                'success': False,
                'error': 'No chat data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        messages = chat_data.get('messages', [])
        if not messages:
            return Response({
                'success': False,
                'error': 'No messages found in chat data'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract topics using AI
        try:
            topics = ai_interview_engine.extract_topics_from_chat(chat_data)
        except Exception as topic_error:
            logger.warning(f"Topic extraction failed: {topic_error}")
            topics = []  # Use empty list if extraction fails
        
        # Determine client name from participants or messages
        participants = chat_data.get('participants', [])
        client_name = None
        if participants:
            # Assume first participant is client
            client_name = participants[0] if len(participants) > 0 else None
        
        # Create or update ChatContext
        context, created = ChatContext.objects.get_or_create(
            url=chat_data.get('url', ''),
            defaults={
                'project_title': chat_data.get('projectTitle', ''),
                'chat_title': chat_data.get('chatTitle', ''),
                'participants': participants,
                'messages': messages,
                'total_messages': len(messages),
                'client_name': client_name,
                'key_topics': topics,
                'extracted_at': timezone.now()
            }
        )
        
        if not created:
            # Update existing context with new data
            context.messages = messages
            context.total_messages = len(messages)
            context.key_topics = topics
            context.extracted_at = timezone.now()
            context.save()
        
        logger.info(f"✅ Chat context {'created' if created else 'updated'}: {context.context_id}")
        
        return Response({
            'success': True,
            'message': f'Chat context {"created" if created else "updated"} successfully',
            'data': {
                'context_id': str(context.context_id),
                'total_messages': context.total_messages,
                'extracted_topics': topics,
                'client_name': client_name,
                'created': created
            }
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error ingesting chat context: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to process chat context: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========= 🎯 Interview Session Management =========

@api_view(['POST'])
@permission_classes([AllowAny])
def create_interview_session(request):
    """
    Create new interview session based on chat context
    """
    try:
        context_id = request.data.get('context_id')
        if not context_id:
            return Response({
                'success': False,
                'error': 'context_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            chat_context = ChatContext.objects.get(context_id=context_id)
        except ChatContext.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Chat context not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get interview configuration from request
        interview_config = request.data.get('config', {})
        interview_type = interview_config.get('type', 'general')
        difficulty_level = interview_config.get('difficulty', 'medium')
        candidate_name = interview_config.get('candidate_name', '')
        
        # Create interview session
        session = InterviewSession.objects.create(
            chat_context=chat_context,
            session_name=f"Interview for {chat_context.project_title or chat_context.chat_title or 'Project'}",
            candidate_name=candidate_name,
            interview_type=interview_type,
            difficulty_level=difficulty_level
        )
        
        # Initialize AI models if not already loaded
        if not ai_interview_engine.is_initialized:
            ai_interview_engine.initialize_models()
        
        # Generate initial questions
        num_questions = interview_config.get('num_questions', 3)
        questions_data = ai_interview_engine.generate_interview_questions(
            chat_context.messages,
            question_type=interview_type,
            num_questions=num_questions
        )
        
        # Save generated questions
        questions = []
        for q_data in questions_data:
            question = InterviewQuestion.objects.create(
                session=session,
                question_text=q_data['question_text'],
                question_type=q_data.get('question_type', 'general'),
                related_topics=q_data.get('related_topics', []),
                difficulty=q_data.get('difficulty', 'medium'),
                generated_by_model=q_data.get('generated_by_model', 'gpt2'),
                generation_confidence=q_data.get('generation_confidence', 0.8)
            )
            questions.append(question)
        
        # Update session stats
        session.total_questions = len(questions)
        session.save()
        
        logger.info(f"✅ Interview session created: {session.session_id}")
        
        return Response({
            'success': True,
            'message': 'Interview session created successfully',
            'data': {
                'session_id': str(session.session_id),
                'session_name': session.session_name,
                'interview_type': session.interview_type,
                'difficulty_level': session.difficulty_level,
                'total_questions': session.total_questions,
                'questions': [
                    {
                        'question_id': str(q.question_id),
                        'question_text': q.question_text,
                        'question_type': q.question_type,
                        'related_topics': q.related_topics,
                        'difficulty': q.difficulty
                    }
                    for q in questions
                ],
                'context_topics': chat_context.key_topics,
                'created_at': session.created_at.isoformat()
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating interview session: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to create interview session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_interview_sessions(request):
    """
    Get list of all interview sessions
    """
    try:
        sessions = InterviewSession.objects.all()
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'session_id': str(session.session_id),
                'session_name': session.session_name,
                'candidate_name': session.candidate_name,
                'interview_type': session.interview_type,
                'difficulty_level': session.difficulty_level,
                'status': session.status,
                'total_questions': session.total_questions,
                'total_responses': session.total_responses,
                'created_at': session.created_at.isoformat(),
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'context_topics': session.chat_context.key_topics,
                'project_title': session.chat_context.project_title
            })
        
        return Response({
            'success': True,
            'sessions': sessions_data,
            'total_sessions': len(sessions_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching interview sessions: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_interview_session(request, session_id):
    """
    Get detailed information about a specific interview session
    """
    try:
        session = InterviewSession.objects.get(session_id=session_id)
        
        # Get all questions for this session
        questions = []
        for question in session.questions.all():
            question_data = {
                'question_id': str(question.question_id),
                'question_text': question.question_text,
                'question_type': question.question_type,
                'difficulty_level': question.difficulty_level,
                'expected_answer': question.expected_answer,
                'created_at': question.created_at.isoformat(),
                'asked_at': question.asked_at.isoformat() if question.asked_at else None,
                'order_index': question.order_index
            }
            
            # Add response if exists
            response = question.responses.first()
            if response:
                question_data['response'] = {
                    'response_id': str(response.response_id),
                    'response_text': response.response_text,
                    'submitted_at': response.submitted_at.isoformat(),
                    'ai_feedback': response.ai_feedback,
                    'confidence_score': response.confidence_score,
                    'follow_up_suggestions': response.follow_up_suggestions
                }
            
            questions.append(question_data)
        
        session_data = {
            'session_id': str(session.session_id),
            'session_name': session.session_name,
            'candidate_name': session.candidate_name,
            'interview_type': session.interview_type,
            'difficulty_level': session.difficulty_level,
            'status': session.status,
            'total_questions': session.total_questions,
            'total_responses': session.total_responses,
            'created_at': session.created_at.isoformat(),
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'questions': questions,
            'chat_context': {
                'context_id': str(session.chat_context.context_id),
                'project_title': session.chat_context.project_title,
                'chat_title': session.chat_context.chat_title,
                'participants': session.chat_context.participants,
                'total_messages': session.chat_context.total_messages,
                'key_topics': session.chat_context.key_topics,
                'extracted_at': session.chat_context.extracted_at.isoformat()
            }
        }
        
        return Response({
            'success': True,
            'session': session_data
        })
        
    except InterviewSession.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Interview session not found'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error fetching interview session: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def get_session_questions(request, session_id):
    """
    Get questions for a specific session, or generate new ones if POST
    """
    try:
        session = InterviewSession.objects.get(session_id=session_id)
        
        if request.method == 'POST':
            # Generate new questions for this session
            try:
                ai_interview_engine.initialize_models()
                questions = ai_interview_engine.generate_interview_questions(session.chat_context.messages)
                
                # Save questions to database
                for i, question_data in enumerate(questions):
                    InterviewQuestion.objects.create(
                        session=session,
                        question_text=question_data.get('question', ''),
                        question_type=question_data.get('type', 'general'),
                        difficulty_level=question_data.get('difficulty', session.difficulty_level),
                        expected_answer=question_data.get('expected_answer', ''),
                        order_index=i
                    )
                
                # Update session question count
                session.total_questions = len(questions)
                session.save()
                
                logger.info(f"Generated {len(questions)} questions for session {session_id}")
                
            except Exception as e:
                logger.error(f"Error generating questions: {str(e)}")
                return Response({
                    'success': False,
                    'error': f'Failed to generate questions: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Get questions for this session
        questions = []
        for question in session.questions.all():
            question_data = {
                'question_id': str(question.question_id),
                'question_text': question.question_text,
                'question_type': question.question_type,
                'difficulty_level': question.difficulty_level,
                'expected_answer': question.expected_answer,
                'created_at': question.created_at.isoformat(),
                'asked_at': question.asked_at.isoformat() if question.asked_at else None,
                'order_index': question.order_index
            }
            
            # Add response if exists
            response = question.responses.first()
            if response:
                question_data['response'] = {
                    'response_id': str(response.response_id),
                    'response_text': response.response_text,
                    'submitted_at': response.submitted_at.isoformat(),
                    'ai_feedback': response.ai_feedback,
                    'confidence_score': response.confidence_score,
                    'follow_up_suggestions': response.follow_up_suggestions
                }
            
            questions.append(question_data)
        
        return Response({
            'success': True,
            'session_id': str(session.session_id),
            'total_questions': len(questions),
            'questions': questions
        })
        
    except InterviewSession.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Interview session not found'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error fetching session questions: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_smart_responses(request):
    """
    Generate smart response suggestions based on chat context without requiring manual questions.
    AI analyzes conversation and suggests intelligent responses.
    """
    try:
        data = request.data
        chat_data = data.get('chat_data', {})
        context = data.get('context', {})
        
        # Debug logging
        logger.info(f"🔍 Smart responses request data keys: {list(data.keys())}")
        logger.info(f"🔍 Chat data keys: {list(chat_data.keys()) if isinstance(chat_data, dict) else 'Not a dict'}")
        logger.info(f"🔍 Chat data type: {type(chat_data)}")
        if isinstance(chat_data, dict) and 'messages' in chat_data:
            logger.info(f"🔍 Messages count: {len(chat_data['messages'])}")
            logger.info(f"🔍 First few messages: {chat_data['messages'][:3] if chat_data['messages'] else 'None'}")
        
        if not chat_data or not isinstance(chat_data, dict):
            return Response({
                'error': 'Invalid chat data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize AI engine
        try:
            ai_interview_engine.initialize_models()
        except Exception as ai_error:
            logger.error(f"AI engine initialization failed: {str(ai_error)}")
            return Response({
                'error': f'AI service temporarily unavailable: {str(ai_error)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Generate smart responses using AI engine
        smart_responses = ai_interview_engine.generate_smart_responses_from_chat(
            chat_data=chat_data,
            context=context
        )
        
        if not smart_responses:
            return Response({
                'error': 'Unable to generate smart responses from chat context'
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        return Response({
            'success': True,
            'smart_responses': smart_responses,
            'chat_analyzed': bool(chat_data.get('messages')),
            'response_count': len(smart_responses),
            'analysis_context': {
                'message_count': len(chat_data.get('messages', [])),
                'participants': context.get('participants', []),
                'project_title': context.get('projectTitle', 'Unknown')
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating smart responses: {str(e)}")
        return Response({
            'error': f'Failed to generate smart responses: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def suggest_answer_for_question(request, session_id):
    """
    Suggest answer for interview question based on chat context
    """
    try:
        session = InterviewSession.objects.get(session_id=session_id)
        
        question_text = request.data.get('question')
        if not question_text:
            return Response({
                'success': False,
                'error': 'Question text is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get chat data from session context
        chat_data = {
            'messages': session.chat_context.messages,
            'participants': session.chat_context.participants,
            'project_title': session.chat_context.project_title,
            'key_topics': session.chat_context.key_topics
        }
        
        # Initialize AI engine
        try:
            ai_interview_engine.initialize_models()
        except Exception as ai_error:
            logger.warning(f"AI models initialization warning: {ai_error}")
        
        # Generate answer suggestion
        suggestion = ai_interview_engine.suggest_answer_from_chat(question_text, chat_data)
        
        return Response({
            'success': True,
            'session_id': str(session.session_id),
            'question': question_text,
            'suggestion': suggestion,
            'chat_context': {
                'total_messages': len(chat_data['messages']),
                'participants': chat_data['participants'],
                'project_title': chat_data['project_title']
            }
        })
        
    except InterviewSession.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Interview session not found'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error suggesting answer: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========= 🤖 AI Interview Engine Endpoints =========

@api_view(['POST'])
@permission_classes([AllowAny])
def start_interview(request, session_id):
    """
    Start an interview session and get first question
    """
    try:
        session = InterviewSession.objects.get(session_id=session_id)
        
        # Start session
        session.start_session()
        
        # Get first question
        first_question = session.questions.first()
        if not first_question:
            return Response({
                'success': False,
                'error': 'No questions found for this session'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Mark question as asked
        first_question.asked_at = timezone.now()
        first_question.save()
        
        return Response({
            'success': True,
            'message': 'Interview started successfully',
            'data': {
                'session_id': str(session.session_id),
                'session_name': session.session_name,
                'current_question': {
                    'question_id': str(first_question.question_id),
                    'question_text': first_question.question_text,
                    'question_type': first_question.question_type,
                    'related_topics': first_question.related_topics,
                    'difficulty': first_question.difficulty
                },
                'question_number': 1,
                'total_questions': session.total_questions,
                'started_at': session.started_at.isoformat()
            }
        })
        
    except InterviewSession.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Interview session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_response(request, question_id):
    """
    Submit response to interview question and get AI analysis
    """
    try:
        question = InterviewQuestion.objects.get(question_id=question_id)
        response_text = request.data.get('response_text', '').strip()
        response_time = request.data.get('response_time_seconds', 0.0)
        
        if not response_text:
            return Response({
                'success': False,
                'error': 'Response text is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize AI if needed
        if not ai_interview_engine.is_initialized:
            ai_interview_engine.initialize_models()
        
        # Analyze response using AI
        analysis = ai_interview_engine.analyze_response(
            question.question_text,
            response_text
        )
        
        # Generate follow-up question if needed
        follow_up_question = None
        follow_up_type = None
        if analysis.get('needs_follow_up', False):
            follow_up_question = ai_interview_engine.generate_follow_up_question(
                question.question_text,
                response_text,
                analysis
            )
            follow_up_type = 'clarification'
        
        # Create or update response record
        response, created = InterviewResponse.objects.get_or_create(
            question=question,
            defaults={
                'response_text': response_text,
                'response_time_seconds': response_time,
                'ai_analysis': analysis.get('analysis', {}),
                'sentiment_score': analysis.get('sentiment_score', 0.0),
                'relevance_score': analysis.get('relevance_score', 0.0),
                'technical_accuracy': analysis.get('technical_accuracy', 0.0),
                'follow_up_question': follow_up_question,
                'follow_up_type': follow_up_type,
                'needs_follow_up': analysis.get('needs_follow_up', False),
                'analyzed_at': timezone.now()
            }
        )
        
        if not created:
            # Update existing response
            response.response_text = response_text
            response.response_time_seconds = response_time
            response.ai_analysis = analysis.get('analysis', {})
            response.sentiment_score = analysis.get('sentiment_score', 0.0)
            response.relevance_score = analysis.get('relevance_score', 0.0)
            response.technical_accuracy = analysis.get('technical_accuracy', 0.0)
            response.follow_up_question = follow_up_question
            response.follow_up_type = follow_up_type
            response.needs_follow_up = analysis.get('needs_follow_up', False)
            response.analyzed_at = timezone.now()
            response.save()
        
        # Update session statistics
        session = question.session
        session.total_responses = session.questions.filter(response__isnull=False).count()
        if session.total_responses > 0:
            avg_time = session.questions.filter(response__isnull=False).aggregate(
                avg_time=models.Avg('response__response_time_seconds')
            )['avg_time']
            session.average_response_time = avg_time or 0.0
        session.save()
        
        # Get next question
        next_question = session.questions.filter(asked_at__isnull=True).first()
        
        return Response({
            'success': True,
            'message': 'Response submitted and analyzed successfully',
            'data': {
                'response_id': str(response.response_id),
                'analysis': {
                    'sentiment_score': response.sentiment_score,
                    'relevance_score': response.relevance_score,
                    'technical_accuracy': response.technical_accuracy,
                    'overall_assessment': analysis.get('analysis', {}).get('assessment', ''),
                    'needs_follow_up': response.needs_follow_up
                },
                'follow_up_question': follow_up_question,
                'next_question': {
                    'question_id': str(next_question.question_id),
                    'question_text': next_question.question_text,
                    'question_type': next_question.question_type,
                    'related_topics': next_question.related_topics,
                    'difficulty': next_question.difficulty
                } if next_question else None,
                'progress': {
                    'completed_questions': session.total_responses,
                    'total_questions': session.total_questions,
                    'percentage': (session.total_responses / session.total_questions * 100) if session.total_questions > 0 else 0
                }
            }
        })
        
    except InterviewQuestion.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Interview question not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error submitting response: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def complete_interview(request, session_id):
    """
    Complete interview session and get final report
    """
    try:
        session = InterviewSession.objects.get(session_id=session_id)
        
        # Complete session
        session.complete_session()
        
        # Generate final report
        responses = InterviewResponse.objects.filter(question__session=session)
        
        # Calculate overall scores
        total_responses = responses.count()
        if total_responses > 0:
            avg_sentiment = sum(r.sentiment_score for r in responses) / total_responses
            avg_relevance = sum(r.relevance_score for r in responses) / total_responses
            avg_technical = sum(r.technical_accuracy for r in responses) / total_responses
            overall_score = (avg_sentiment + avg_relevance + avg_technical) / 3
        else:
            avg_sentiment = avg_relevance = avg_technical = overall_score = 0.0
        
        # Prepare detailed responses
        detailed_responses = []
        for response in responses:
            detailed_responses.append({
                'question': response.question.question_text,
                'question_type': response.question.question_type,
                'response': response.response_text,
                'response_time': response.response_time_seconds,
                'scores': {
                    'sentiment': response.sentiment_score,
                    'relevance': response.relevance_score,
                    'technical_accuracy': response.technical_accuracy
                },
                'analysis': response.ai_analysis,
                'follow_up_generated': response.follow_up_question is not None
            })
        
        return Response({
            'success': True,
            'message': 'Interview completed successfully',
            'data': {
                'session_id': str(session.session_id),
                'session_name': session.session_name,
                'candidate_name': session.candidate_name,
                'interview_type': session.interview_type,
                'completed_at': session.completed_at.isoformat(),
                'duration_minutes': (session.completed_at - session.started_at).total_seconds() / 60 if session.started_at else 0,
                'overall_scores': {
                    'sentiment': round(avg_sentiment, 2),
                    'relevance': round(avg_relevance, 2),
                    'technical_accuracy': round(avg_technical, 2),
                    'overall': round(overall_score, 2)
                },
                'statistics': {
                    'total_questions': session.total_questions,
                    'total_responses': total_responses,
                    'average_response_time': round(session.average_response_time, 2),
                    'completion_rate': round((total_responses / session.total_questions * 100), 1) if session.total_questions > 0 else 0
                },
                'detailed_responses': detailed_responses,
                'context_topics': session.chat_context.key_topics,
                'recommendations': _generate_recommendations(overall_score, detailed_responses)
            }
        })
        
    except InterviewSession.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Interview session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error completing interview: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _generate_recommendations(overall_score: float, responses: list) -> list:
    """Generate recommendations based on interview performance"""
    recommendations = []
    
    if overall_score >= 0.8:
        recommendations.append("Excellent performance! Strong technical knowledge and communication skills.")
    elif overall_score >= 0.6:
        recommendations.append("Good performance with room for improvement in specific areas.")
    else:
        recommendations.append("Performance needs improvement. Consider additional preparation.")
    
    # Analyze response patterns
    technical_responses = [r for r in responses if r.get('question_type') == 'technical']
    if technical_responses:
        avg_technical = sum(r['scores']['technical_accuracy'] for r in technical_responses) / len(technical_responses)
        if avg_technical < 0.5:
            recommendations.append("Focus on strengthening technical knowledge and providing concrete examples.")
    
    # Check response times
    avg_time = sum(r['response_time'] for r in responses) / len(responses) if responses else 0
    if avg_time > 120:  # 2 minutes
        recommendations.append("Consider practicing to provide more concise responses.")
    elif avg_time < 30:  # 30 seconds
        recommendations.append("Consider providing more detailed and thorough responses.")
    
    return recommendations

# ========= 🔧 System Management =========

@api_view(['GET'])
@permission_classes([AllowAny])
def get_ai_status(request):
    """
    Get AI engine status and model information
    """
    try:
        return Response({
            'success': True,
            'ai_engine': {
                'is_initialized': ai_interview_engine.is_initialized,
                'models_loaded': list(ai_interview_engine.models.keys()),
                'pipelines_available': list(ai_interview_engine.pipelines.keys()),
                'cpu_mode': True,  # Always CPU for server deployment
                'transformers_available': hasattr(ai_interview_engine, 'TRANSFORMERS_AVAILABLE')
            },
            'statistics': {
                'total_contexts': ChatContext.objects.count(),
                'total_sessions': InterviewSession.objects.count(),
                'active_sessions': InterviewSession.objects.filter(status='active').count(),
                'completed_sessions': InterviewSession.objects.filter(status='completed').count()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting AI status: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def initialize_ai_engine(request):
    """
    Initialize or reload AI engine
    """
    try:
        force_reload = request.data.get('force_reload', False)
        success = ai_interview_engine.initialize_models(force_reload=force_reload)
        
        if success:
            return Response({
                'success': True,
                'message': 'AI engine initialized successfully',
                'models_loaded': list(ai_interview_engine.models.keys())
            })
        else:
            return Response({
                'success': False,
                'message': 'Failed to initialize AI engine'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error initializing AI engine: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
