"""
NotificationPush Views
Django views for Upwork job monitoring through Chrome browser scraper
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
# ==========  🚀🤖 scraping mode universal ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def universal_scrape(request):
    """
    Universal DOM scraping with enhanced error handling and state cleanup
    """
    
    # run scraper with parameter for 
    # universal mode
    # DOM scraper (reads any page content)
    return _run_scraper('universal', 'Universal DOM scrape')
import logging
import subprocess
import os
import json
import sys
import requests
import time
from datetime import datetime
from django.utils import timezone
from projects.models import Project  # Import Project model for scraped jobs integration
from .models import Job, ScrapingSession, Notification, ChromeSession  # Import new database models

# Logger setup
logger = logging.getLogger(__name__)

# variable to hold important values that  browser monitoring needs to track
monitoring_state = {
    'is_running': False,
    'process': None,
    'jobs': [],
    'status': 'disconnected',
    'config': {
        'keywords': 'javascript,react,node.js',
        'profile_id': ''
    }
}
# ========== 🚀 call browser monitoring functions ==========

# ========== 🖥️ view of browser monitoring functions ==========
@api_view(['GET']) # get method
@permission_classes([AllowAny]) # allow any user (no auth)
def notification_status(request): # take request as input

    try:
        # Check real Chrome debugging status
        chrome_available = check_chrome_debugging_available()
        
        # Update monitoring_state based on True/False is_running status
        if chrome_available:
            if not monitoring_state['is_running']:
                monitoring_state['is_running'] = True
                monitoring_state['status'] = 'connected'
        else:
            if monitoring_state['is_running']:
                monitoring_state['is_running'] = False
                monitoring_state['status'] = 'disconnected'
        
        # render current status, keywords, job count and last check time
        return Response({
            'status': monitoring_state['status'],
            'is_running': monitoring_state['is_running'],
            'chrome_debugging': chrome_available,
            'keywords': monitoring_state['config']['keywords'],
            'jobs_count': len(monitoring_state['jobs']),
            'last_check': datetime.now().isoformat()
        })
        # or error
    except Exception as e:
        logger.error(f"Error getting scraper status: {e}")
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========== start monitoring based on user input ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def start_monitoring(request):

    try:
        # check if already running
        if monitoring_state['is_running']:
            return Response({
                'success': False,
                'message': 'Browser scraper is already running'
            })
        
        # Update config from request
        config_data = request.data
        if 'keywords' in config_data:
            monitoring_state['config']['keywords'] = config_data['keywords']
        if 'profileId' in config_data:
            monitoring_state['config']['profile_id'] = config_data['profileId']
        
        # Start browser scraper for manual login
        monitoring_state['is_running'] = True
        monitoring_state['status'] = 'monitoring'
        
        # Start Chrome browser
        start_chrome_browser()
        
        logger.info(f"🚀 Started Chrome browser for manual Upwork login")
        
        # return info on monitor_state
        return Response({
            'success': True,
            'message': 'Chrome browser opened - you can now manually login to Upwork',
            'config': {
                'keywords': monitoring_state['config']['keywords'],
                'manual_mode': True
            }
        })
        
    except Exception as e:
        logger.error(f"Error starting scraper: {e}")
        monitoring_state['is_running'] = False
        monitoring_state['status'] = 'error'
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#========== start monitoring based on user input end ==========

# ========== reset monitoring state ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def stop_monitoring(request):

    try:
        # Reset monitoring state regardless of current state
        monitoring_state['is_running'] = False
        monitoring_state['status'] = 'disconnected'
        
        # Kill scraper process if it exists
        if monitoring_state['process']:
            try:
                monitoring_state['process'].terminate()
                monitoring_state['process'] = None
            except:
                pass
        
        # Try to kill Chrome processes (optional cleanup)
        try:
            import subprocess
            # taskkill the chrome processes on Windows
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], 
                         capture_output=True, shell=True)
            logger.info("Chrome processes terminated")
        except Exception as chrome_kill_error:
            logger.warning(f"Could not kill Chrome processes: {chrome_kill_error}")
        
        logger.info("🛑 Stopped NotificationPush browser scraper and reset state")
        
        return Response({
            'success': True,
            'message': 'Browser scraper stopped and state reset successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping scraper: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#========== notifications get methods (same as jobs) ==========
@api_view(['GET'])
@permission_classes([AllowAny])
def get_notifications(request):
    """
    Get system notifications from database
    """
    try:
        # Get pagination parameters
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        unread_only = request.GET.get('unread_only', '').lower() == 'true'
        
        # Get notifications from database
        notifications_query = Notification.objects.all()
        if unread_only:
            notifications_query = notifications_query.filter(is_read=False)
        
        notifications = notifications_query[offset:offset+limit]
        total_count = notifications_query.count()
        
        # Serialize notifications data
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.notification_id,
                'title': notif.title,
                'message': notif.message,
                'type': notif.type,
                'source': notif.source,
                'is_read': notif.is_read,
                'is_dismissed': notif.is_dismissed,
                'created_at': notif.created_at.isoformat(),
                'job_id': notif.job.job_id if notif.job else None,
                'session_id': notif.session.session_id if notif.session else None,
                'data': notif.data,
            })
        
        return Response({
            'success': True,
            'notifications': notifications_data,
            'total_count': total_count,
            'unread_count': Notification.objects.filter(is_read=False).count(),
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#========== job get methods (same as notifications) ==========
@api_view(['GET'])
@permission_classes([AllowAny])
def get_jobs(request):
    """
    Get captured Upwork jobs from database
    """
    try:
        # Get pagination parameters
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        # Get jobs from database
        jobs = Job.objects.all()[offset:offset+limit]
        total_count = Job.objects.count()
        
        # Serialize jobs data
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                'id': job.job_id,
                'title': job.title,
                'description': job.description,
                'client_name': job.client_name,
                'budget': job.budget,
                'hourly_rate': job.hourly_rate,
                'posted_date': job.posted_date.isoformat() if job.posted_date else None,
                'job_url': job.job_url,
                'location': job.location,
                'job_type': job.job_type,
                'is_applied': job.is_applied,
                'is_favorite': job.is_favorite,
                'scraped_at': job.scraped_at.isoformat(),
            })
        
        return Response({
            'success': True,
            'jobs': jobs_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==========  ➕🏢 job append methods ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def batch_jobs(request):

    try:
        # Receive jobs from Node.js scraper
        jobs = request.data.get('jobs', [])
        profile_id = request.data.get('profile_id', '1')
        # if jobs are received
        if jobs:
            # Add jobs to monitoring state
            monitoring_state['jobs'].extend(jobs)
            logger.info(f"📋 Received {len(jobs)} jobs from manual scrape")
            # Update profile ID for each job
        return Response({
            'success': True,
            'message': f'Added {len(jobs)} jobs',
            'total_jobs': len(monitoring_state['jobs'])
        })
        
    except Exception as e:
        logger.error(f"Error processing batch jobs: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========== 🚀🤖 scraping mode manual ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def manual_scrape(request):
    # run scraper with parameter for 
    # logged-in user
    # manual scrape (reads current Upwork page)
    return _run_scraper('logged-in', 'Manual scrape for logged-in user')

# ==========  � Save scraped jobs to database ==========
def save_scraped_jobs_to_db(jobs_data, scrape_mode='universal'):
    """Save scraped jobs to Project model"""
    try:
        saved_count = 0
        
        for job in jobs_data:
            title = job.get('title', 'Untitled Job')
            
            # Skip if job with same title already exists (avoid duplicates)
            if not Project.objects.filter(
                title=title,
                is_scraped=True
            ).exists():
                
                # Extract client name from different possible fields
                client = job.get('client', '')
                if not client:
                    # Try to extract from URL or other fields
                    url = job.get('url', '')
                    if 'upwork.com' in url:
                        client = 'Upwork Client'
                    else:
                        client = 'Unknown Client'
                
                # Create new project from scraped job
                project = Project.objects.create(
                    title=title,
                    client=client,
                    budget=job.get('budget', 'Budget not specified'),
                    description=job.get('description', 'No description available'),
                    url=job.get('url', ''),
                    skills_required=job.get('skills_required', ''),
                    time_posted=job.get('timePosted', job.get('time_posted', 'Unknown time')),
                    scraped_at=timezone.now(),
                    scrape_source=scrape_mode,
                    is_scraped=True,
                    status='scraped',
                    tos_safe=True,  # Manual scraping is TOS-safe
                    fetch_method='scrape'
                )
                saved_count += 1
                logger.info(f"💾 Saved scraped job: {title}")
                
        logger.info(f"💾 Saved {saved_count} new scraped jobs to database")
        return saved_count
        
    except Exception as e:
        logger.error(f"❌ Error saving scraped jobs: {e}")
        return 0

# ==========  �🚀🤖 scraping mode universal ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def universal_scrape(request):

    # run scraper with parameter for 
    # universal mode
    # DOM scraper (reads any page content)
    return _run_scraper('universal', 'Universal DOM scrape')

# ==========  scraping main logic ==========
def _run_scraper(mode, description):
    
    try:
        # Check if Chrome debugging is available 
        if not check_chrome_debugging_available():
            # if not available, update state to disconnected + return 400
            monitoring_state['is_running'] = False
            monitoring_state['status'] = 'disconnected'
            return Response({
                'success': False,
                'message': 'Chrome debugging not available. Please start Chrome browser first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Chrome is available, update state to connected
            monitoring_state['is_running'] = True
            monitoring_state['status'] = 'connected'
        
        
        try:
            # get path for
            # root
            current_dir = os.path.dirname(__file__)
            # project root
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
            # scraper directory in frontend/src/scraper (moved from NotificationPushBrowser)
            scraper_dir = os.path.join(project_root, 'frontend', 'src', 'scraper')
            # extractor script in frontend/src/scraper/enhanced_extractor.js
            extractor_script = os.path.join(scraper_dir, 'enhanced_extractor.js')
            # if extractor script does not exist, return error
            if not os.path.exists(extractor_script):
                return Response({
                    'success': False,
                    'message': f'Enhanced extractor not found: {extractor_script}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # log description and enhanced extractor script path from
            # manual_scrape or universal_scrape
            logger.info(f"🔍 Running {description} with: {extractor_script}")

            # in variable cmd_args
            # put
            # 1. node 
            # 2. frontend/src/scraper/enhanced_extractor.js
            # 3. mode (either 'logged-in' or 'universal')
            cmd_args = ['node', extractor_script, mode]
            # log everything
            logger.info(f"🔍 Using enhanced extractor with mode: {extractor_script}")
            
            # in subprocess run
            result = subprocess.run(
                cmd_args, # cmd_args
                cwd=scraper_dir,  # in cwd=scraper_dir (updated from browser_dir)
                capture_output=True, # capture output
                text=True, # text and not bytes
                encoding='utf-8', # encoding utf-8
                errors='replace',  # Replace problematic characters instead of crashing
                timeout=10  # Very short timeout for faster failures
            )
            # if returncode is 0 return standard output message
            if result.returncode == 0:
                logger.info(f"✅ {description} completed successfully")
                logger.info(f"Output: {result.stdout}")
                
                # Try to read extracted data from backend/notification_push/data/extracted_jobs.json
                data_file = os.path.join(project_root, 'backend', 'notification_push', 'data', 'extracted_jobs.json')
                jobs_extracted = 0
                saved_count = 0  # Initialize saved_count
                page_info = None

                # Check if the data file exists
                if os.path.exists(data_file):
                    try:
                        with open(data_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # if data exists
                            if isinstance(data, list):
                                # append job list
                                jobs_extracted = len(data)
                                monitoring_state['jobs'].extend(data)
                                # Save scraped jobs to database
                                saved_count = save_scraped_jobs_to_db(data, mode)
                            else:
                                # else append job list from data['jobs']
                                # and pageInfo from data['pageInfo']
                                jobs_extracted = len(data.get('jobs', []))
                                monitoring_state['jobs'].extend(data.get('jobs', []))
                                page_info = data.get('pageInfo')
                                # Save scraped jobs to database
                                saved_count = save_scraped_jobs_to_db(data.get('jobs', []), mode)
                                
                    except Exception as read_error:
                        logger.warning(f"Could not read extracted data: {read_error}")
                        saved_count = 0
                
                # prepare response data
                response_data = {
                    'success': True,
                    'message': f'{description} completed - extracted {jobs_extracted} items, saved {saved_count} new jobs to database',
                    'jobs_found': jobs_extracted,
                    'saved_to_db': saved_count,
                    'mode': mode
                }
                
                if page_info:
                    response_data['page_info'] = page_info
                
                return Response(response_data)
            else:
                logger.error(f"{description} failed: {result.stderr}")
                return Response({
                    'success': False,
                    'message': f'Scrape failed: {result.stderr}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Handle timeout
        except subprocess.TimeoutExpired:
            return Response({
                'success': False,
                'message': f'{description} timed out - try again'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as proc_error:
            logger.error(f"Error running {description}: {proc_error}")
            return Response({
                'success': False,
                'message': f'Failed to run scraper: {str(proc_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # general exception
    except Exception as e:
        logger.error(f"Error triggering {description}: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========== 🔄️ refresh_chrome_status ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_chrome_status(request):
    """
    Refresh Chrome debugging status and update monitoring state
    """
    try:
        # variable to hold data from requests call bellow ⬇️
        chrome_available = check_chrome_debugging_available()
        
        # read from variable and print massage that contains status
        if chrome_available:
            monitoring_state['is_running'] = True
            monitoring_state['status'] = 'connected'
            message = 'Chrome debugging is available and connected'
        else:
            monitoring_state['is_running'] = False
            monitoring_state['status'] = 'disconnected'
            message = 'Chrome debugging is not available'
        # log message
        logger.info(f"Chrome status refreshed: {message}")
        # return response with collected data
        return Response({
            'success': True,
            'message': message,
            'chrome_debugging': chrome_available,
            'status': monitoring_state['status'],
            'is_running': monitoring_state['is_running']
        })
        
    except Exception as e:
        logger.error(f"Error refreshing Chrome status: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==========  📋 Get scraped jobs from database ==========
@api_view(['GET'])
@permission_classes([AllowAny])
def get_scraped_projects(request):
    """Get all scraped jobs from database"""
    try:
        scraped_projects = Project.objects.filter(is_scraped=True).order_by('-scraped_at')[:50]  # Limit to 50 recent jobs
        
        jobs_data = []
        for project in scraped_projects:
            jobs_data.append({
                'id': project.id,
                'title': project.title,
                'client': project.client,
                'budget': project.budget,
                'description': project.description,
                'url': project.url,
                'skills_required': project.skills_required,
                'time_posted': project.time_posted,
                'scraped_at': project.scraped_at.isoformat() if project.scraped_at else None,
                'status': project.status,
                'cover_letter': project.cover_letter,
                'scrape_source': project.scrape_source
            })
        
        logger.info(f"📋 Retrieved {len(jobs_data)} scraped projects from database")
        
        return Response({
            'success': True,
            'jobs': jobs_data,
            'count': len(jobs_data)
        })
        
    except Exception as e:
        logger.error(f"❌ Error retrieving scraped projects: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========== 🧐 helper to check if Chrome debugging is available ==========
def check_chrome_debugging_available():

    try:
        # variable to hold return value from requests call to localhost:9222/json/version
        response = requests.get('http://localhost:9222/json/version', timeout=3)
        if response.status_code == 200:
            version_info = response.json()
            logger.info(f"✅ Chrome debugging available: {version_info.get('Browser', 'Unknown')}")
            return True
    except Exception as e:
        logger.info(f"Chrome debugging not available: {e}")
        return False
    
    return False

# ========== ▶️🌐 start real Chrome browser ==========
def start_chrome_browser():

    try:
        # First check if Chrome debugging is already available
        if check_chrome_debugging_available():
            logger.info("🔄 Chrome debugging already available - using existing session")
            monitoring_state['status'] = 'connected'
            return True
        
        # Get project root directory (go up from backend to project root)
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        scraper_dir = os.path.join(project_root, 'frontend', 'src', 'scraper')
        
        logger.info(f"Project root: {project_root}")
        logger.info(f"Scraper directory: {scraper_dir}")
        
        # Check if scraper directory exists
        if not os.path.exists(scraper_dir):
            raise Exception(f"Scraper directory not found: {scraper_dir}")
        
        # Check if Chrome launcher exists
        chrome_launcher = os.path.join(scraper_dir, 'chrome_launcher_simple.py')
        if not os.path.exists(chrome_launcher):
            raise Exception(f"Chrome launcher script not found: {chrome_launcher}")
        
        logger.info(f"Using Chrome launcher: {chrome_launcher}")
        
        # Start the real Chrome browser with debugging (with venv activation)
        if sys.platform == "win32":
            # Try simple launcher first (no venv needed)
            if 'simple' in chrome_launcher:
                cmd_args = ['python', 'chrome_launcher_simple.py']
            else:
                # Windows - remove batch script logic (simplified)
                cmd_args = ['python', 'chrome_launcher_simple.py']
        else:
            cmd_args = ['python', 'chrome_launcher_simple.py']
        
        logger.info(f"Starting real Chrome browser with command: {' '.join(cmd_args)}")
        logger.info(f"Working directory: {scraper_dir}")  # Updated from browser_dir
        
        # Start process in scraper directory
        if 'simple' in chrome_launcher:
            # Simple launcher - just run and wait for completion
            logger.info("Using simple Chrome launcher (non-blocking)")
            result = subprocess.run(
                cmd_args,
                cwd=scraper_dir,  # Updated from browser_dir
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=15
            )
            
            if result.returncode == 0:
                logger.info("✅ Simple Chrome launcher completed successfully")
                logger.info(f"Output: {result.stdout}")
                # Verify Chrome debugging is available
                if check_chrome_debugging_available():
                    logger.info("✅ Chrome debugging confirmed working")
                    monitoring_state['status'] = 'connected'
                    return True
                else:
                    raise Exception("Chrome debugging not available after launch")
            else:
                raise Exception(f"Chrome launcher failed: {result.stderr}")
        
        else:
            # Original launcher with background process
            if sys.platform == "win32":
                logger.info("Using Windows subprocess flags")
                monitoring_state['process'] = subprocess.Popen(
                    cmd_args,
                    cwd=scraper_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                logger.info("Using default subprocess flags")
                monitoring_state['process'] = subprocess.Popen(
                    cmd_args,
                    cwd=scraper_dir,  # Updated from browser_dir
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True
                )
            
            logger.info(f"✅ Real Chrome browser process started with PID: {monitoring_state['process'].pid}")
            logger.info("✅ Chrome will open with debugging enabled - you can login manually!")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error starting browser: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        monitoring_state['is_running'] = False
        monitoring_state['status'] = 'error'
        raise e

# ========== 📬 Message Scraping Functions ==========

@api_view(['POST'])
@permission_classes([AllowAny])
def scrape_messages(request):
    """
    Scrape Upwork messages/notifications from logged-in Chrome browser
    """
    try:
        # Check if Chrome debugging is available 
        if not check_chrome_debugging_available():
            monitoring_state['is_running'] = False
            monitoring_state['status'] = 'disconnected'
            return Response({
                'success': False,
                'message': 'Chrome debugging not available. Please start Chrome browser first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            monitoring_state['is_running'] = True
            monitoring_state['status'] = 'connected'
        
        # Get paths
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        scraper_dir = os.path.join(project_root, 'frontend', 'src', 'scraper')
        message_script = os.path.join(scraper_dir, 'message_extractor.js')
        
        if not os.path.exists(message_script):
            return Response({
                'success': False,
                'message': f'Message extractor not found: {message_script}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"📬 Running message extraction with: {message_script}")
        
        # Run message extractor
        cmd_args = ['node', message_script]
        
        result = subprocess.run(
            cmd_args,
            cwd=scraper_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120  # Povećano na 2 minuta za message extraction
        )
        
        if result.returncode == 0:
            logger.info("✅ Message extraction completed successfully")
            logger.info(f"Output: {result.stdout}")
            
            # Try to load extracted messages from file
            data_dir = os.path.join(project_root, 'backend', 'notification_push', 'data')
            
            # Find the most recent message file
            message_files = []
            if os.path.exists(data_dir):
                for file in os.listdir(data_dir):
                    if file.startswith('upwork_messages_') and file.endswith('.json'):
                        message_files.append(os.path.join(data_dir, file))
            
            if message_files:
                # Get most recent file
                latest_file = max(message_files, key=os.path.getctime)
                
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        message_data = json.load(f)
                    
                    return Response({
                        'success': True,
                        'message': 'Messages extracted successfully',
                        'data': {
                            'messages': message_data.get('messages', []),
                            'pageInfo': message_data.get('pageInfo', {}),
                            'extractedAt': message_data.get('extractedAt'),
                            'file': latest_file
                        }
                    })
                    
                except Exception as parse_error:
                    logger.error(f"Error parsing message data: {parse_error}")
                    return Response({
                        'success': False,
                        'message': f'Error parsing extracted messages: {str(parse_error)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'success': False,
                    'message': 'No message files found after extraction'
                }, status=status.HTTP_404_NOT_FOUND)
                
        else:
            logger.error(f"❌ Message extraction failed with return code: {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            
            return Response({
                'success': False,
                'message': f'Message extraction failed: {result.stderr or "Unknown error"}',
                'debug': {
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Message extraction timed out after 2 minutes")
        return Response({
            'success': False,
            'message': 'Message extraction timed out after 2 minutes. Try reducing the page complexity or check Chrome connection.'
        }, status=status.HTTP_408_REQUEST_TIMEOUT)
        
    except Exception as e:
        logger.error(f"❌ Unexpected error during message extraction: {str(e)}")
        return Response({
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)