from rest_framework import serializers
from .models import Project
from .models import Skillset

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class SkillsetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skillset
        fields = '__all__'
