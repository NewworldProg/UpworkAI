from django.contrib import admin
from .models import Project

from .models import Skillset

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'status', 'match_score', 'created_at')
    search_fields = ('title', 'description', 'client', 'skills_required')


@admin.register(Skillset)
class SkillsetAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'skills', 'created_at')
    search_fields = ('name', 'owner', 'skills')
