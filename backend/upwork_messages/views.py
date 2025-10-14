"""
Upwork Messages Views
API endpoints for message management and AI-powered chat responses
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Chat, Message, MessageExtractionLog
from .ai_chat import chat_ai
import json
import os
import subprocess
import uuid
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def extract_and_save_messages(request):
    """Extract messages from Upwork and save to database - Async approach"""
    try:
        # Run message extractor script
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        scraper_dir = os.path.join(project_root, 'frontend', 'src', 'scraper')
        message_script = os.path.join(scraper_dir, 'message_extractor.js')
        
        if not os.path.exists(message_script):
            return Response({
                'success': False,
                'message': f'Message extractor not found: {message_script}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"Starting message extraction with: {message_script}")
        
        # Start process in background without waiting
        import threading
        def run_extraction():
            try:
                result = subprocess.run(
                    ['node', message_script],
                    cwd=scraper_dir,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=300  # 5 minutes timeout for background process
                )
                
                if result.returncode != 0:
                    logger.error(f"❌ Background message extraction failed: {result.stderr}")
                    return
                
                # Process extraction results
                data_dir = os.path.join(project_root, 'backend', 'notification_push', 'data')
                
                if not os.path.exists(data_dir):
                    logger.error("❌ Data directory not found")
                    return
                
                message_files = []
                for file in os.listdir(data_dir):
                    if file.startswith('upwork_messages_') and file.endswith('.json'):
                        message_files.append(os.path.join(data_dir, file))
                
                if not message_files:
                    logger.warning("⚠️ No extracted messages found")
                    return
                
                # Get most recent file
                latest_file = max(message_files, key=os.path.getctime)
                
                # Load extracted data
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                messages_data = data.get('messages', [])
                page_info = data.get('pageInfo', {})
                
                # Create extraction log
                extraction_log = MessageExtractionLog.objects.create(
                    extraction_id=str(uuid.uuid4()),
                    page_url=page_info.get('url', ''),
                    total_messages_found=len(messages_data),
                    selector_used=page_info.get('selector_used', ''),
                    success=True
                )
                
                saved_messages = 0
                new_chats = 0
                
                # Process each message
                for msg_data in messages_data:
                    try:
                        # Get or create chat
                        chat_id = msg_data.get('conversationId') or f"chat_{msg_data.get('sender', 'unknown')}"
                        chat, created = Chat.objects.get_or_create(
                            chat_id=chat_id,
                            defaults={
                                'sender_name': msg_data.get('sender', 'Unknown'),
                                'chat_url': msg_data.get('chatUrl', ''),
                                'last_activity': timezone.now(),
                            }
                        )
                        
                        if created:
                            new_chats += 1
                        
                        # Parse timestamp
                        msg_timestamp = msg_data.get('timestamp')
                        if msg_timestamp:
                            try:
                                if msg_timestamp.endswith('Z'):
                                    msg_timestamp = msg_timestamp[:-1] + '+00:00'
                                parsed_time = timezone.datetime.fromisoformat(msg_timestamp)
                            except:
                                parsed_time = timezone.now()
                        else:
                            parsed_time = timezone.now()
                        
                        # Create or update message
                        message_id = msg_data.get('id', f"msg_{uuid.uuid4()}")
                        message, created = Message.objects.get_or_create(
                            message_id=message_id,
                            chat=chat,
                            defaults={
                                'sender': msg_data.get('sender', 'Unknown'),
                                'content': msg_data.get('content', msg_data.get('text', '')),
                                'preview': msg_data.get('preview', '')[:500],
                                'timestamp': parsed_time,
                                'is_read': msg_data.get('isRead', True),  # Default to read
                                'selector_used': msg_data.get('selector_used', ''),
                                'html_snippet': msg_data.get('html', '')[:1000],
                            }
                        )
                        
                        if created:
                            saved_messages += 1
                        
                        # Update chat metadata
                        chat.total_messages = chat.messages.count()
                        chat.unread_count = chat.messages.filter(is_read=False).count()
                        chat.last_activity = timezone.now()
                        chat.save()
                        
                    except Exception as e:
                        logger.error(f"Error processing message {msg_data.get('id')}: {e}")
                        continue
                
                # Update extraction log
                extraction_log.new_messages_saved = saved_messages
                extraction_log.save()
                
                logger.info(f"✅ Background extraction completed: {saved_messages} new messages in {new_chats} new chats")
                
            except subprocess.TimeoutExpired:
                logger.error("❌ Background message extraction timed out after 5 minutes")
            except Exception as e:
                logger.error(f"❌ Background extraction error: {str(e)}")
        
        # Start extraction in background thread
        extraction_thread = threading.Thread(target=run_extraction, daemon=True)
        extraction_thread.start()
        
        # Return immediate response
        return Response({
            'success': True,
            'message': 'Message extraction started in background. Check logs for completion status.',
            'status': 'processing'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Unexpected error during message extraction setup: {str(e)}")
        return Response({
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_extraction_status(request):
    """Get status of the most recent message extraction"""
    try:
        # Get the most recent extraction log
        latest_log = MessageExtractionLog.objects.order_by('-timestamp').first()
        
        if not latest_log:
            return Response({
                'success': True,
                'status': 'no_extractions',
                'message': 'No message extractions found'
            })
        
        return Response({
            'success': True,
            'status': 'completed' if latest_log.success else 'failed',
            'extraction_id': latest_log.extraction_id,
            'timestamp': latest_log.timestamp.isoformat(),
            'total_messages_found': latest_log.total_messages_found,
            'new_messages_saved': latest_log.new_messages_saved,
            'page_url': latest_log.page_url,
            'error_message': latest_log.error_message if not latest_log.success else None
        })
        
    except Exception as e:
        logger.error(f"Error getting extraction status: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_messages(request):
    """Get all messages from database"""
    try:
        messages = Message.objects.all().order_by('-timestamp')[:200]  # Latest 200 messages
        
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'chat_id': message.chat.id,
                'content': message.content,
                'sender': message.sender,
                'timestamp': message.timestamp.isoformat(),
                'is_outgoing': message.is_outgoing,
                'is_read': message.is_read,
                'conversation_id': message.chat.id,
                'conversationId': message.chat.id,  # For backward compatibility
                'preview': message.content[:100] + '...' if len(message.content) > 100 else message.content
            })
        
        return Response(messages_data)
        
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        return Response({
            'error': 'Failed to fetch messages',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_chats_with_messages(request):
    """Get all chats with their messages from database"""
    try:
        chats = Chat.objects.all().prefetch_related('messages')
        
        chats_data = []
        for chat in chats:
            messages = chat.messages.all()[:20]  # Latest 20 messages per chat
            
            chats_data.append({
                'id': chat.id,
                'chat_id': chat.chat_id,
                'sender_name': chat.sender_name,
                'chat_url': chat.chat_url,
                'last_activity': chat.last_activity.isoformat(),
                'total_messages': chat.total_messages,
                'unread_count': chat.unread_count,
                'is_active': chat.is_active,
                'messages': [
                    {
                        'id': msg.id,
                        'message_id': msg.message_id,
                        'sender': msg.sender,
                        'content': msg.content,
                        'preview': msg.preview,
                        'timestamp': msg.timestamp.isoformat(),
                        'is_read': msg.is_read,
                        'is_from_me': msg.is_from_me,
                    }
                    for msg in messages
                ]
            })
        
        return Response({
            'success': True,
            'chats': chats_data,
            'total_chats': len(chats_data),
            'total_unread': sum(chat['unread_count'] for chat in chats_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting chats: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_chat_messages(request, chat_id):
    """Get all messages for specific chat"""
    try:
        chat = Chat.objects.get(chat_id=chat_id)
        messages = chat.messages.all().order_by('timestamp')  # Chronological order (oldest first)
        
        # Vrati i informacije o chat-u
        if request.path.endswith(f'/chats/{chat_id}/'):
            # Request za chat info
            return Response({
                'success': True,
                'chat': {
                    'id': chat.id,
                    'chat_id': chat.chat_id,
                    'conversation_id': chat.conversation_id,
                    'other_participant': chat.other_participant,
                    'chat_url': chat.chat_url,
                    'total_messages': messages.count(),
                    'unread_count': messages.filter(is_read=False).count(),
                    'last_message': {
                        'content': messages.last().content if messages.exists() else '',
                        'timestamp': messages.last().timestamp.isoformat() if messages.exists() else '',
                        'sender': messages.last().sender if messages.exists() else ''
                    }
                }
            })
        else:
            # Request za messages
            messages_data = [
                {
                    'id': msg.id,
                    'message_id': msg.message_id,
                    'sender': msg.sender,
                    'content': msg.content,
                    'preview': msg.preview,
                    'timestamp': msg.timestamp.isoformat(),
                    'is_read': msg.is_read,
                    'is_from_me': msg.is_from_me,
                    'is_outgoing': msg.is_from_me,  # Add compatibility field
                    'extracted_at': msg.extracted_at.isoformat(),
                }
                for msg in messages
            ]
            
            return Response({
                'success': True,
                'chat': {
                    'id': chat.id,
                    'chat_id': chat.chat_id,
                    'conversation_id': chat.conversation_id,
                    'other_participant': chat.other_participant,
                    'chat_url': chat.chat_url,
                    'total_messages': messages.count(),
                    'unread_count': messages.filter(is_read=False).count(),
                },
                'messages': messages_data
            })
        
    except Chat.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Chat not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def suggest_ai_replies(request, chat_id=None):
    """Generate AI reply suggestions based on message content"""
    try:
        # Initialize AI if not loaded
        if not chat_ai.model_loaded:
            chat_ai.load_model()

        if request.method == 'GET':
            # Za GET request, uzmi chat_id iz URL-a i poslednju poruku
            if chat_id:
                try:
                    chat = Chat.objects.get(chat_id=chat_id)
                    last_message = chat.messages.order_by('-timestamp').first()
                    if last_message:
                        message_content = last_message.content
                    else:
                        return Response({
                            'success': False,
                            'error': 'No messages found in chat'
                        }, status=status.HTTP_404_NOT_FOUND)
                except Chat.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Chat not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'success': False,
                    'error': 'chat_id is required for GET request'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # POST request - koristi postojeću logiku
            message_content = request.data.get('message_content', '')
            chat_id = request.data.get('chat_id', '')

        if not message_content:
            return Response({
                'success': False,
                'error': 'message_content is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        suggestions = chat_ai.suggest_reply_templates(message_content)
        
        # Get conversation insights if chat_id is provided
        insights = {}
        if chat_id:
            try:
                chat = Chat.objects.get(chat_id=chat_id)
                messages = chat.messages.all()[:10]  # Last 10 messages
                message_data = [
                    {
                        'content': msg.content,
                        'is_from_me': msg.is_from_me,
                        'timestamp': msg.timestamp.isoformat()
                    }
                    for msg in messages
                ]
                insights = chat_ai.get_conversation_insights(message_data)
            except Chat.DoesNotExist:
                pass
        
        return Response({
            'success': True,
            'suggestions': suggestions,
            'insights': insights,
            'intent': chat_ai.classify_message_intent(message_content)
        })
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_ai_response(request):
    """Generate personalized AI response based on conversation history"""
    try:
        # Initialize AI if not loaded
        if not chat_ai.model_loaded:
            chat_ai.load_model()
        
        chat_id = request.data.get('chat_id')
        message_history = request.data.get('message_history', [])
        
        if not chat_id:
            return Response({
                'success': False,
                'error': 'chat_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get chat context
        try:
            chat = Chat.objects.get(chat_id=chat_id)
            client_context = f"Client: {chat.sender_name}, Total messages: {chat.total_messages}"
            
            # If no message history provided, get from database
            if not message_history:
                messages = chat.messages.all()[:10]  # Last 10 messages
                message_history = [
                    {
                        'content': msg.content,
                        'is_from_me': msg.is_from_me,
                        'timestamp': msg.timestamp.isoformat()
                    }
                    for msg in messages
                ]
        except Chat.DoesNotExist:
            client_context = "Unknown client"
        
        response = chat_ai.generate_personalized_response(message_history, client_context)
        
        return Response({
            'success': True,
            'response': response,
            'context_used': client_context
        })
        
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def open_message_in_chrome(request):
    """Open specific message conversation in Chrome debugger"""
    try:
        from .chrome_control_simple import chrome_controller
        
        conversation_id = request.data.get('conversation_id')
        if not conversation_id:
            return Response({
                'success': False,
                'error': 'conversation_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Open message in Chrome debugger
        result = chrome_controller.open_upwork_message(conversation_id)
        
        return Response({
            'success': result['success'],
            'action': result.get('action', 'attempted'),
            'url': result['url'],
            'error': result.get('error')
        })
        
    except Exception as e:
        logger.error(f"Error opening message in Chrome: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_active_chat(request):
    """Analyze active chat in Chrome debugger and provide AI suggestions"""
    try:
        # Get paths
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        scraper_dir = os.path.join(project_root, 'frontend', 'src', 'scraper')
        chat_script = os.path.join(scraper_dir, 'active_chat_scraper.js')
        
        if not os.path.exists(chat_script):
            return Response({
                'success': False,
                'error': f'Active chat scraper not found: {chat_script}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"🤖 Running active chat analysis with: {chat_script}")
        
        # Run active chat scraper
        cmd_args = ['node', chat_script]
        
        result = subprocess.run(
            cmd_args,
            cwd=scraper_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60  # Povećano na 60 sekundi
        )
        
        if result.returncode == 0:
            logger.info("✅ Active chat analysis completed successfully")
            logger.info(f"Output length: {len(result.stdout)}")
            logger.info(f"Output: '{result.stdout}'")
            logger.info(f"STDERR: '{result.stderr}'")
            
            try:
                # Parse JSON output from scraper
                import json
                stripped_output = result.stdout.strip()
                logger.info(f"Stripped output length: {len(stripped_output)}")
                
                # Extract JSON part from output (starts with '{')
                json_start = stripped_output.find('{')
                if json_start != -1:
                    json_part = stripped_output[json_start:]
                    logger.info(f"JSON part: '{json_part[:200]}...'")
                    chat_result = json.loads(json_part)
                else:
                    logger.error("No JSON found in scraper output")
                    return Response({
                        'success': False,
                        'error': 'No JSON found in scraper output',
                        'debug': {'stdout': result.stdout}
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                if chat_result.get('success'):
                    # The scraper returns data directly in the main object
                    chat_data = {
                        'url': chat_result.get('url'),
                        'chatTitle': chat_result.get('chatTitle'),
                        'projectTitle': chat_result.get('projectTitle'),
                        'participants': chat_result.get('participants', []),
                        'messages': chat_result.get('messages', []),
                        'extractedAt': chat_result.get('extractedAt'),
                        'messageCount': chat_result.get('messageCount')
                    }
                    
                    # Generate AI suggestions based on chat content
                    suggestions = generate_ai_suggestions(chat_data)
                    
                    return Response({
                        'success': True,
                        'message': 'Active chat analyzed successfully',
                        'data': {
                            'chatData': chat_data,
                            'suggestions': suggestions,
                            'messageCount': len(chat_data.get('messages', [])),
                            'conversationId': chat_data.get('conversationId'),
                            'participants': chat_data.get('participants', [])
                        }
                    })
                else:
                    return Response({
                        'success': False,
                        'error': chat_result.get('error', 'Unknown error from scraper')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except json.JSONDecodeError as parse_error:
                logger.error(f"Error parsing chat scraper output: {parse_error}")
                logger.error(f"Raw output length: {len(result.stdout)}")
                logger.error(f"Raw output: '{result.stdout}'")
                logger.error(f"Raw stderr: '{result.stderr}'")
                return Response({
                    'success': False,
                    'error': f'Error parsing scraper output: {str(parse_error)}',
                    'debug': {
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'stdout_length': len(result.stdout)
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        else:
            logger.error(f"❌ Active chat analysis failed with return code: {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            
            return Response({
                'success': False,
                'error': f'Chat analysis failed: {result.stderr or "Unknown error"}',
                'debug': {
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Active chat analysis timed out")
        return Response({
            'success': False,
            'error': 'Chat analysis timed out after 30 seconds'
        }, status=status.HTTP_408_REQUEST_TIMEOUT)
        
    except Exception as e:
        logger.error(f"❌ Unexpected error during chat analysis: {str(e)}")
        return Response({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def generate_ai_suggestions(chat_data):
    """Generate AI reply suggestions based on chat content"""
    try:
        if not chat_data or not chat_data.get('messages'):
            return ['No messages found to analyze']
        
        messages = chat_data['messages']
        last_messages = messages[-5:]  # Last 5 messages for context
        
        # Create context for AI
        context = f"Conversation with: {', '.join(chat_data.get('participants', ['Unknown']))}\n\n"
        context += "Recent messages:\n"
        
        for msg in last_messages:
            sender = msg.get('sender', 'Unknown')
            content = msg.get('content', '')
            context += f"{sender}: {content}\n"
        
        # Simple rule-based suggestions for now
        # TODO: Integrate with actual AI model
        suggestions = []
        
        last_message = last_messages[-1] if last_messages else None
        if last_message and not last_message.get('isFromMe', False):
            content = last_message.get('content', '').lower()
            
            if 'question' in content or '?' in content:
                suggestions.append("Thank you for your question. Let me provide a detailed response...")
                suggestions.append("I appreciate you reaching out. Here's what I can tell you...")
            elif 'thank' in content:
                suggestions.append("You're very welcome! I'm glad I could help.")
                suggestions.append("Happy to assist! Feel free to reach out if you need anything else.")
            elif 'meeting' in content or 'call' in content:
                suggestions.append("I'd be happy to schedule a call. What times work best for you?")
                suggestions.append("A meeting sounds great. Let me know your availability.")
            elif 'project' in content or 'work' in content:
                suggestions.append("I'm excited about this project opportunity. Let me share my approach...")
                suggestions.append("This project looks interesting. I have relevant experience that would be valuable.")
            else:
                suggestions.append("Thank you for your message. I'll review this and get back to you shortly.")
                suggestions.append("I appreciate you reaching out. Let me provide a thoughtful response...")
        else:
            suggestions.append("Follow up on the previous discussion")
            suggestions.append("Check if they need any clarification")
        
        return suggestions[:3]  # Return max 3 suggestions
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {str(e)}")
        return [f"Error generating suggestions: {str(e)}"]
