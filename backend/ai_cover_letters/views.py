"""
AI Cover Letter Views
Django views for cover letter generation using AI
"""
# library for defining API views and setting permissions
from rest_framework.decorators import api_view, permission_classes 
# library for setting permissions
from rest_framework.permissions import AllowAny
# library for sending HTTP responses
from rest_framework.response import Response
# library for HTTP status codes
from rest_framework import status
# Django HTTP response
from django.http import JsonResponse
# Django CSRF exemption decorator
from django.views.decorators.csrf import csrf_exempt
# Django method decorator
from django.utils.decorators import method_decorator
# AI Model Manager from our models
from .models import AIModelManager
# logging for debugging
import logging

def create_resume_for_job(job_title, skills):
    """Create resume content optimized for Content Writer and related roles"""
    
    # Content Writer focused resume template
    content_writer_resume = """
EXPERIENCE:
• Senior Content Writer at Digital Marketing Agency (2021-2023)
  - Created engaging blog posts, articles, and web copy that increased organic traffic by 45%
  - Developed content strategies for 20+ clients across various industries
  - Managed editorial calendars and content workflows using project management tools
  
• Freelance Content Creator (2019-2021)
  - Wrote SEO-optimized content for SaaS companies, increasing search rankings by 60%
  - Produced technical documentation, user guides, and marketing materials
  - Collaborated with design teams to create compelling visual content

SKILLS:
• SEO Writing & Keyword Research
• Content Strategy Development  
• WordPress & CMS Management
• Social Media Content Creation
• Technical Writing & Documentation
• Email Marketing Campaigns
• Google Analytics & Performance Tracking
• Copywriting & Brand Voice Development

EDUCATION:
• Bachelor's Degree in Communications/Marketing
• Google Analytics Certified
• HubSpot Content Marketing Certification

ACHIEVEMENTS:
• Increased client website traffic by average of 50% through strategic content
• Successfully managed content calendars for multiple high-traffic websites
• Expert in creating conversion-focused copy that drives engagement
"""
    
    # Customize resume based on job requirements
    if "seo" in job_title.lower() or "seo" in skills.lower():
        return content_writer_resume + "\n• SEO Specialist certification\n• Advanced keyword research expertise"
    elif "social media" in job_title.lower() or "social" in skills.lower():
        return content_writer_resume + "\n• Social Media Marketing expertise\n• Content creation for Instagram, LinkedIn, Twitter"
    elif "technical" in job_title.lower() or "technical" in skills.lower():
        return content_writer_resume + "\n• Technical writing specialization\n• API documentation experience"
    else:
        return content_writer_resume

# Set up logging
logger = logging.getLogger(__name__)

# Import from .models.py the AIModelManager instance
ai_manager = AIModelManager()

# dont need csrf for API endpoints
@csrf_exempt
# take POST request with job details and return generated cover letter
@api_view(['POST'])
# anyone can access this endpoint
@permission_classes([AllowAny])

# ========================== ✍️🤖 generate cover letter ==========================
def generate_cover_letter(request):

    # ======= get request data =======
    try:
        data = request.data # get JSON data from request body ⬇️
        job_title = data.get('job_title', '') # job title for the cover letter
        company_name = data.get('company_name', '') # company name for the cover letter
        skills = data.get('skills', 'Python, Django, React') # skills for the cover letter
        # if job_title is missing, return error response
        if not job_title:
            return Response({
                'success': False,
                'error': 'job_title is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        # log the request details
        logger.info(f"📝 Generating cover letter for: {job_title}")
    #======== get request data =======

        # Load model if not already loaded
        if not ai_manager.model_loaded:
            logger.info("Loading AI model...")
            success = ai_manager.load_model()
            if not success:
                return Response({
                    'success': False,
                    'error': 'Failed to load AI model'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create detailed resume based on job type
        resume_content = create_resume_for_job(job_title, skills)
        
        # Create prompt in format expected by cover-letter-t5-base model
        cover_prompt = f"""coverletter name: Content Writer job: {job_title} at {company_name} background: Senior Content Writer with 3+ years experience experiences: I created engaging content that increased organic traffic by 45%. I managed 20+ client accounts and developed content strategies across various industries. I have expertise in {skills}, SEO optimization, WordPress management, and email marketing campaigns. I am passionate about creating compelling content that drives results and engagement."""
        
        # Generate cover letter with optimized prompt
        ai_response = ai_manager.generate_response(
            prompt=cover_prompt,
            max_tokens=400,  # Good balance for quality and server constraints
            temperature=0.7  # Standard temperature for creativity
        )
        
        return Response({
            'cover_letter': ai_response,
            'success': True,
            'error': None
        })
        
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        return Response({
            'cover_letter': '',
            'success': False,
            'error': f'Cover letter generation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def direct_prompt(request):
    """
    Direct prompt endpoint for AI model
    """
    try:
        data = request.data
        prompt = data.get('prompt', '')
        max_tokens = data.get('max_tokens', 300)
        temperature = data.get('temperature', 0.7)
        
        if not prompt:
            return Response({
                'success': False,
                'error': 'prompt is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"🧠 Processing prompt: {prompt[:100]}...")
        
        # Load model if not already loaded
        if not ai_manager.model_loaded:
            logger.info("Loading AI model...")
            success = ai_manager.load_model()
            if not success:
                return Response({
                    'success': False,
                    'error': 'Failed to load AI model'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Generate AI response
        ai_response = ai_manager.generate_response(
            prompt, 
            max_tokens=max_tokens, 
            temperature=temperature
        )
        
        return Response({
            'response': ai_response,
            'success': True,
            'error': None
        })
        
    except Exception as e:
        logger.error(f"Error in direct_prompt: {e}")
        return Response({
            'response': '',
            'success': False,
            'error': f'Prompt processing error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def ai_status(request):
    """
    AI model status endpoint
    """
    try:
        status_info = ai_manager.get_model_status()
        status_info.update({
            'hardware_optimization': 'CPU optimized for Django integration',
            'model_type': 'LoRA fine-tuned for cover letters',
            'integration': 'Django native (no microservice overhead)'
        })
        
        return Response(status_info)
        
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
