from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer
from . import services
from .models import Skillset
from .serializers import SkillsetSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
import json

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def generate_cover_global(request):
    """Global endpoint for generating cover letters without project context"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        job_title = data.get('job_title', '')
        company_name = data.get('company_name', '')
        job_description = data.get('job_description', '')
        skills = data.get('skills', 'Python, Django, React')
        
        # Use the cover generator service  
        cover = services.generate_cover_letter(
            project_description=job_description,
            skills=skills,
            job_title=job_title,
            company_name=company_name
        )
        
        return JsonResponse({
            'cover_letter': cover or '',
            'success': bool(cover),
            'error': 'No AI model configured - please integrate your model' if not cover else None
        })
        
    except Exception as e:
        return JsonResponse({
            'cover_letter': '',
            'success': False,
            'error': str(e)
        }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    # Development convenience: disable session-based auth (which enforces CSRF)
    # and allow anonymous access so frontend can POST without CSRF token.
    # IMPORTANT: remove or tighten this for production.
    authentication_classes = []
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'])
    def compute_score(self, request, pk=None):
        project = self.get_object()
        skills = request.data.get('skills', project.skills_required)
        score = services.compute_match_score(project.description or '', skills)
        project.match_score = score
        project.save()
        return Response({'match_score': score})

    @action(detail=True, methods=['post'])
    def generate_cover(self, request, pk=None):
        project = self.get_object()
        skills = request.data.get('skills', project.skills_required)
        mode = request.data.get('mode')
        cover = services.generate_cover_letter(project.description or '', skills, mode=mode, job_title=project.title)
        # Ensure we never write NULL into the TextField (DB expects empty string when absent)
        project.cover_letter = cover or ''
        project.status = 'proposal_ready'
        project.save()
        return Response({'cover_letter': cover or '', 'generated': bool(cover)})

    @action(detail=True, methods=['post'])
    def send_to_monday(self, request, pk=None):
        project = self.get_object()
        assignee = request.data.get('assignee', 'writer')
        api_key = request.auth if hasattr(request, 'auth') else None
        res = services.create_monday_task(project.title, str(project.deadline), assignee, api_key)
        if res.get('ok'):
            project.status = 'accepted'
            project.save()
            return Response({'monday': res})
        return Response({'error': 'monday failed', 'detail': res}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search projects by skills (POST { skills: 'a,b,c' }). Returns projects ordered by computed match_score."""
        skills = request.data.get('skills', '')
        qs = list(Project.objects.all())
        results = []
        for p in qs:
            score = services.compute_match_score(p.description or '', skills)
            results.append((score, p))
        # sort desc by score
        results.sort(key=lambda x: x[0], reverse=True)
        projects_ordered = [r[1] for r in results]
        serializer = ProjectSerializer(projects_ordered, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def extract_text(self, request):
        """Extract text from payload or URL. Body: { payload: {...}, allow_fetch: bool }

        Returns { text: '...' }
        """
        payload = request.data.get('payload') or {}
        allow_fetch = bool(request.data.get('allow_fetch'))
        tos_safe = bool(request.data.get('tos_safe'))
        # enforce global scraping setting
        from django.conf import settings
        if allow_fetch and not getattr(settings, 'ALLOW_SCRAPING', False) and not tos_safe:
            return Response({'error': 'fetch_disabled', 'detail': 'Fetching disabled by settings; set tos_safe=True or enable ALLOW_SCRAPING in settings'}, status=403)
        try:
            text = services.extract_project_text(payload, allow_fetch=allow_fetch)
            return Response({'text': text})
        except Exception as e:
            return Response({'error': 'fetch_failed', 'detail': str(e)}, status=400)

        @action(detail=False, methods=['post'])
        def ingest(self, request):
            """Ingest a job payload and create a Project. Body: { payload: {...}, allow_fetch: bool }

            Returns created Project serialized.
            """
            payload = request.data.get('payload') or {}
            allow_fetch = bool(request.data.get('allow_fetch'))
            tos_safe = bool(request.data.get('tos_safe'))
            from django.conf import settings
            if allow_fetch and not getattr(settings, 'ALLOW_SCRAPING', False) and not tos_safe:
                return Response({'error': 'fetch_disabled', 'detail': 'Fetching disabled by settings; set tos_safe=True or enable ALLOW_SCRAPING in settings'}, status=403)
            try:
                project = services.ingest_job_with_fetch(payload, allow_fetch=allow_fetch)
                serializer = ProjectSerializer(project)
                return Response(serializer.data, status=201)
            except ValueError as e:
                return Response({'error': 'ingest_invalid', 'detail': str(e)}, status=400)
            except Exception as e:
                return Response({'error': 'ingest_failed', 'detail': str(e)}, status=500)


        @action(detail=True, methods=['post'])
        def generate_cover_zephyr(self, request, pk=None):  # POMERITE OVO UNUTAR KLASE
            """Generate cover letter using Zephyr API"""
            project = self.get_object()
            
            import requests
            try:
                response = requests.post('http://localhost:8002/api/generate-cover-letter', 
                    json={
                        'job_title': project.title,
                        'company_name': project.client or '',
                        'job_description': project.description or '',
                        'skills': project.skills_required or 'Python, Django, React'
                    }, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        cover = data.get('cover_letter', '')
                        project.cover_letter = cover
                        project.status = 'proposal_ready'
                        project.save()
                        return Response({'cover_letter': cover, 'generated': True})
                
                return Response({'error': 'Zephyr API failed'}, status=500)
                
            except Exception as e:
                return Response({'error': f'Zephyr connection failed: {e}'}, status=500)

class SkillsetViewSet(viewsets.ModelViewSet):
    queryset = Skillset.objects.all()
    serializer_class = SkillsetSerializer



