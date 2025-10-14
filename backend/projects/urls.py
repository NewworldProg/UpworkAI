from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, SkillsetViewSet, generate_cover_global
from django.urls import path, include

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'skillsets', SkillsetViewSet, basename='skillset')


urlpatterns = [
    path('', include(router.urls)),
    path('generate-cover-letter/', generate_cover_global, name='generate_cover_global')
   # path('', include('projects.ingest_job.ai_ingest.llm_urls')),
]
