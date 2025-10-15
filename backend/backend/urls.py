from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="UpworkApply API",
        default_version='v1',
        description="API for project ingestion, scoring and Monday integration",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('projects.urls')),
    path('api/ai/', include('ai_cover_letters.urls')),  # AI Cover Letters endpoints
    path('api/notification-push/', include('notification_push.urls')),  # NotificationPush endpoints
    path('api/messages/', include('upwork_messages.urls')),  # Upwork Messages and AI Chat endpoints
    path('api/interview/', include('AI_interview_chat.urls')),  # AI Interview Chat system endpoints
    # Swagger/OpenAPI endpoints
    path('swagger(<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # Static simple Swagger UI wrapper (optional)
    path('swagger-ui/', TemplateView.as_view(template_name='swagger_ui/index.html'), name='swagger-ui'),
]
