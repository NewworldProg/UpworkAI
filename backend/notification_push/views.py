"""
NotificationPush Views
Django views for Upwork job monitoring through Chrome browser scraper
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging
import subprocess
import os
import json
import sys
import requests
import time
from datetime import datetime, timedelta
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
# ========== 🚀 call browser monitoring functions ==========

# ========== 🔎🌐 check if browser is running and send status ==========
@api_view(['GET']) # get method
@permission_classes([AllowAny]) # allow any user (no auth)
def notification_status(request): # take request as input

    try:
        # Check real Chrome debugging status, in helper function below
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

# ===== 🛸🖥️🙍start job monitoring based on keywords and profile ID ======
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
#===== 🛸🖥️🙍start job monitoring based on keywords and profile ID ======

# ========== 🔄️🖥️ reset monitoring state ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def stop_monitoring(request):

    try:
        # set monitoring_state ['is_running'] to false
        # set monitoring_state ['status'] to 'disconnected'
        monitoring_state['is_running'] = False
        monitoring_state['status'] = 'disconnected'

        # if monitoring_state ['process'] exists
        if monitoring_state['process']:
            try:
                # Terminate the process and set to None
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
# ========== 🔄️🖥️ reset monitoring state ==========

#========== 🗒️🖥️ notifications display  ==========
@api_view(['GET'])
@permission_classes([AllowAny])
def get_notifications(request):
    
    try:
        # set variables for GET rendering
        # limit rendering to 50
        limit = int(request.GET.get('limit', 50))
        # starting point of jobs rendered
        offset = int(request.GET.get('offset', 0))
        # show only unread
        unread_only = request.GET.get('unread_only', '').lower() == 'true'
        
        # Get notifications from database models.Notification
        notifications_query = Notification.objects.all()
        if unread_only:
            notifications_query = notifications_query.filter(is_read=False)
        # Limit the number of notifications returned and starting point
        notifications = notifications_query[offset:offset+limit]
        # count total notifications for
        total_count = notifications_query.count()

        # cleaned notifications in array for rendering
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
        # render response
        return Response({
            'success': True,
            'notifications': notifications_data,
            'total_count': total_count,
            'unread_count': Notification.objects.filter(is_read=False).count(),
            'limit': limit,
            'offset': offset
        })
    # or error
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# ================== 🗒️🖥️ notifications display ======================

#========================= 🗒️🖥️ jobs display =========================
@api_view(['GET'])
@permission_classes([AllowAny])
def get_jobs(request):
    """
    Get captured Upwork jobs from the most recent scraping session only
    """
    try:
        # Get the most recent session
        latest_session = ScrapingSession.objects.order_by('-started_at').first()
        
        if not latest_session:
            return Response({
                'success': True,
                'jobs': [],
                'total_count': 0,
                'session_info': None
            })
        
        # Get all jobs from the latest session based on time window
        # Jobs scraped between session start and completion
        session_jobs = Job.objects.filter(
            scraped_at__gte=latest_session.started_at,
            scraped_at__lte=latest_session.completed_at or timezone.now()
        ).order_by('-scraped_at')
        
        total_count = session_jobs.count()

        # cleaned jobs data for rendering
        jobs_data = []
        for job in session_jobs:
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
        # render response
        return Response({
            'success': True,
            'jobs': jobs_data,
            'total_count': total_count,
            'session_info': {
                'session_id': latest_session.session_id,
                'started_at': latest_session.started_at.isoformat(),
                'total_jobs_found': latest_session.total_jobs_found,
                'new_jobs_saved': latest_session.new_jobs_saved,
                'status': latest_session.status
            }
        })
    # or error
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_jobs(request):
    """
    Get all jobs from database with pagination for ProjectList
    """
    try:
        # limit rendering to 20 for ProjectList
        limit = int(request.GET.get('limit', 20))
        # starting point of jobs rendered
        offset = int(request.GET.get('offset', 0))

        # Get all jobs from database models.Job
        jobs = Job.objects.all().order_by('-scraped_at')[offset:offset+limit]
        # set total_count for 
        total_count = Job.objects.count()

        # cleaned jobs data for rendering
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
        # render response
        return Response({
            'success': True,
            'jobs': jobs_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': (offset + limit) < total_count,
            'has_previous': offset > 0
        })
    # or error
    except Exception as e:
        logger.error(f"Error getting all jobs: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#======================== 🗒️🖥️ jobs display =========================

# ==========  ➕🏢 job append methods ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def batch_jobs(request):

    try:
        # Receive jobs from Node.js scraper
        jobs = request.data.get('jobs', [])
        # Get profile ID from request
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
#=========  ➕🏢 job append methods ==========

# ========== 🚀🤖 scraping mode manual ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def manual_scrape(request):
    # run scraper with parameter for 
    # logged-in user
    # manual scrape (reads current Upwork page)
    return _run_scraper('logged-in', 'Manual scrape for logged-in user')
#========= 🚀🤖 scraping mode manual ==========

# ========== 🛸💼 helper function for saving scraped jobs in db ==========
# take jobs_data, scrape_mode and session as parameters
def save_scraped_jobs_to_database(jobs_data, scrape_mode='universal', session=None):
    """Save scraped jobs to notification_push Job model"""
    try:
        saved_count = 0
        
        # iterate through jobs_data
        for job in jobs_data:
            job_id = job.get('id') or job.get('url', f"job_{timezone.now().timestamp()}")
            title = job.get('title', 'Untitled Job')
            
            # Skip if job with same job_id already exists
            if not Job.objects.filter(job_id=job_id).exists():
                
                # Parse posted date
                posted_date = timezone.now()
                time_posted = job.get('timePosted') or job.get('time_posted')
                if time_posted:
                    try:
                        # Try to parse various date formats
                        from dateutil import parser
                        posted_date = parser.parse(time_posted)
                    except:
                        posted_date = timezone.now()
                
                # Create new Job in notification_push model
                new_job = Job.objects.create(
                    job_id=job_id,
                    title=title,
                    description=job.get('description', 'No description available'),
                    client_name=job.get('client', 'Unknown Client'),
                    budget=job.get('budget', ''),
                    hourly_rate=job.get('hourly_rate', ''),
                    posted_date=posted_date,
                    job_url=job.get('url', ''),
                    location=job.get('location', ''),
                    job_type=job.get('job_type', scrape_mode),
                    selector_used=job.get('selector_used', ''),
                    html_snippet=job.get('html', '')[:1000] if job.get('html') else ''
                )
                
                # Create notification for new job
                Notification.objects.create(
                    notification_id=f"job_{new_job.id}_{timezone.now().timestamp()}",
                    title=f"New Job Found: {title[:50]}",
                    message=f"Found new job from {new_job.client_name}",
                    type='info',
                    source='scraper',
                    job=new_job,
                    session=session,
                    data={'scrape_mode': scrape_mode}
                )
                
                saved_count += 1
                logger.info(f"💾 Saved job to notification_push DB: {title}")
                
        logger.info(f"💾 Saved {saved_count} new jobs to notification_push database")
        return saved_count
        
    except Exception as e:
        logger.error(f"❌ Error saving jobs to notification_push database: {e}")
        return 0

# ========= 🗒️💼 job into project conversion for frontend  rendering ==========
def convert_job_to_project(job_id):
    """Convert a Job from notification_push to Project for business workflow"""
    try:
        job = Job.objects.get(job_id=job_id)
        
        # Check if Project already exists
        if not Project.objects.filter(title=job.title, url=job.job_url).exists():
            project = Project.objects.create(
                title=job.title,
                client=job.client_name,
                budget=job.budget or 'Budget not specified',
                description=job.description,
                url=job.job_url,
                skills_required='',  # To be filled manually
                time_posted=job.posted_date.isoformat() if job.posted_date else '',
                scraped_at=timezone.now(),
                scrape_source='notification_push',
                is_scraped=True,
                status='scraped',
                tos_safe=True,
                fetch_method='converted_from_job'
            )
            logger.info(f"🔄 Converted Job {job_id} to Project {project.id}")
            return project
        else:
            logger.info(f"⚠️ Project already exists for Job {job_id}")
            return None
            
    except Job.DoesNotExist:
        logger.error(f"❌ Job {job_id} not found")
        return None
    except Exception as e:
        logger.error(f"❌ Error converting Job to Project: {e}")
        return None
# ========= 🗒️💼 job into project conversion for frontend  rendering ==========
# ==========  🚀🤖 scraping mode universal ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def universal_scrape(request):

    # run scraper with parameter for 
    # universal mode
    # DOM scraper (reads any page content)
    return _run_scraper('universal', 'Universal DOM scrape')

# ========== 🛸🤖 helper function for scraping ==========
def _run_scraper(mode, description):
    
    try:
        # 1. Cleanup old running sessions that are stuck (older than 10 minutes)
        stale_sessions = ScrapingSession.objects.filter(
            status='running',
            started_at__lt=timezone.now() - timedelta(minutes=10)
        )
        
        if stale_sessions.exists():
            stale_count = stale_sessions.count()
            stale_sessions.update(
                status='failed',
                error_message='Session timed out - possibly interrupted by multiple tabs or browser conflicts',
                completed_at=timezone.now()
            )
            logger.warning(f"Marked {stale_count} stale running sessions as failed")
        
        # 2. Check if there's already an active scraping session
        active_sessions = ScrapingSession.objects.filter(
            status='running',
            started_at__gte=timezone.now() - timedelta(minutes=10)  # Last 10 minutes
        )
        
        if active_sessions.exists():
            return Response({
                'success': False,
                'message': 'Another scraping session is already running. Please wait for it to complete or try again in a few minutes.'
            }, status=status.HTTP_409_CONFLICT)
        
        # 3. Check if Chrome debugging is available 
        if not check_chrome_debugging_available():
            # if not available
            # monitoring_state['is_running'] to false
            # monitoring_state['status'] to 'disconnected'
            monitoring_state['is_running'] = False
            monitoring_state['status'] = 'disconnected'
            # return error response
            return Response({
                'success': False,
                'message': 'Chrome debugging not available. Please start Chrome browser first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # else Chrome is available
            # monitoring_state['is_running'] to true
            # monitoring_state['status'] to 'connected'
            monitoring_state['is_running'] = True
            monitoring_state['status'] = 'connected'
        
        
        try:
            # 2. get path for
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

            # 3.  in variable cmd_args and run the scraper in subprocess
            # put
            # 1. node 
            # 2. frontend/src/scraper/enhanced_extractor.js
            # 3. mode (either 'logged-in' or 'universal')
            cmd_args = ['node', extractor_script, mode]
            # log everything
            logger.info(f"🔍 Using enhanced extractor with mode: {extractor_script}")
            
            # in subprocess run frontend/src/scraper/enhanced_extractor.js
            result = subprocess.run(
                cmd_args, # cmd_args
                cwd=scraper_dir,  # in cwd=scraper_dir (updated from browser_dir)
                capture_output=True, # capture output
                text=True, # text and not bytes
                encoding='utf-8', # encoding utf-8
                errors='replace',  # Replace problematic characters instead of crashing
                timeout=60  # Increased timeout for API-based scraping (scraper + API call)
            )
            # if returncode is 0 return standard output message
            if result.returncode == 0:
                logger.info(f"✅ {description} completed successfully")
                logger.info(f"Output: {result.stdout}")
                
                # Wait a moment for API call to complete
                time.sleep(1)
                
                # Get recent scraping sessions from last 5 minutes only
                # 🧱 Build
                # in variable five_minutes_ago
                # put timedelta(minutes=5)
                five_minutes_ago = timezone.now() - timedelta(minutes=5)
                
                # in variable recent_sessions
                # put ScrapingSession.objects.filter(
                recent_sessions = ScrapingSession.objects.filter(
                    session_id__startswith='api_session_',
                    started_at__gte=five_minutes_ago  # Only sessions from last 5 minutes
                ).order_by('-started_at')[:1]
                
                if recent_sessions.exists():
                    session = recent_sessions.first()
                    jobs_extracted = session.total_jobs_found
                    saved_count = session.new_jobs_saved
                    page_info = {'scraper_mode': mode, 'session_found': True}
                else:
                    # No recent session found - scraper might not have called API
                    jobs_extracted = 0
                    saved_count = 0
                    page_info = {'scraper_mode': mode, 'session_found': False}
                    logger.warning(f"No recent API session found for {mode} scraper - check if scraper is calling save API")
                
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

# ========== 💾 save from captured jobs to database ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def save_jobs_to_database_api(request):
    #
    try:
        data = request.data
        jobs = data.get('jobs', [])
        mode = data.get('mode', 'unknown')
        
        if not jobs:
            return Response({
                'success': True,
                'message': 'No jobs to save',
                'saved_count': 0
            })
        
        # Create scraping session
        session = ScrapingSession.objects.create(
            session_id=f"api_session_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            page_url=f"Scraper API - {mode} mode",
            selector_used=f"{mode}_api_extractor",
            total_jobs_found=len(jobs)
        )
        
        # Save jobs using the database function
        saved_count = save_scraped_jobs_to_database(jobs, mode, session)
        
        # Update session with results
        session.new_jobs_saved = saved_count
        session.status = 'completed' if saved_count > 0 else 'failed'
        session.completed_at = timezone.now()
        if saved_count == 0:
            session.error_message = 'No new jobs saved (possibly duplicates)'
        session.save()
        
        logger.info(f"📡 API saved {saved_count} jobs from {mode} scraper")
        
        return Response({
            'success': True,
            'message': f'Successfully saved {saved_count} jobs to database',
            'saved_count': saved_count,
            'total_found': len(jobs),
            'session_id': session.session_id
        })
        
    except Exception as e:
        logger.error(f"❌ Error in save_jobs_to_database_api: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error saving jobs: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ========== 💾 save from captured jobs to database ==========