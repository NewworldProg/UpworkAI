from dataclasses import dataclass
from typing import List, Union
from rest_framework import serializers


@dataclass
class SkillsInput:
    skills: List[str]

    def as_string(self) -> str:
        return ','.join(self.skills)


class SkillsSerializer(serializers.Serializer):
    skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )

    def validate_skills(self, value: List[str]) -> List[str]:
        seen = set()
        out = []
        for s in value:
            s2 = s.strip()
            if not s2:
                continue
            if s2.lower() in seen:
                continue
            seen.add(s2.lower())
            out.append(s2)
        return out


def normalize_skills(raw: Union[str, List[str], None]) -> SkillsInput:
    if raw is None:
        return SkillsInput(skills=[])
    if isinstance(raw, str):
        # Accept comma, newline, or whitespace separated skills.
        # First replace newlines with spaces, then split on commas and whitespace.
        s = raw.replace('\n', ' ').replace('\r', ' ')
        # Split on commas first to preserve multi-word skills like "google analytics"
        parts = []
        for chunk in s.split(','):
            # split chunk by whitespace to allow space-separated lists, but keep multi-word
            # skills if they were quoted (not supported) — instead we treat contiguous words
            # as possible multi-word skills, so we only collapse extra spaces here.
            part = ' '.join(chunk.split()).strip()
            if part:
                parts.append(part)
        serializer = SkillsSerializer(data={'skills': parts})
        if serializer.is_valid():
            return SkillsInput(skills=serializer.validated_data['skills'])
        return SkillsInput(skills=parts)
    if isinstance(raw, list):
        serializer = SkillsSerializer(data={'skills': raw})
        try:
            serializer.is_valid(raise_exception=True)
            skills = serializer.validated_data['skills']
        except Exception:
            skills = [str(s).strip() for s in raw if str(s).strip()]
        return SkillsInput(skills=skills)
    return SkillsInput(skills=[])
