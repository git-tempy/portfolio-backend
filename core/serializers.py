from rest_framework import serializers
from django.db import models
from .uploads import RemoteFileField, RemoteImageField

class StorageModelSerializer(serializers.ModelSerializer):
    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.FileField: RemoteFileField,
        models.ImageField: RemoteImageField,
    }

from .models import AboutMe, Certificate, Skill, Trait, Experience, ProjectCategory, Project, ContactMessage, VisitorLog, ProjectImage, Education, ResumeDownloadLog

class AboutMeSerializer(StorageModelSerializer):
    class Meta:
        model = AboutMe
        fields = [
            'name', 'name_uz', 'name_ru', 'name_en', 'name_jp',
            'bio', 'bio_uz', 'bio_ru', 'bio_en', 'bio_jp',
            'image', 'resume_pdf'
        ]

class CertificateSerializer(StorageModelSerializer):
    class Meta:
        model = Certificate
        fields = [
            'id', 'title', 'title_uz', 'title_ru', 'title_en', 'title_jp',
            'organization', 'year', 'file', 'image'
        ]

class SkillSerializer(StorageModelSerializer):
    level = serializers.IntegerField(min_value=0, max_value=100, allow_null=True, required=False)
    class Meta:
        model = Skill
        fields = ['id', 'name', 'name_uz', 'name_ru', 'name_en', 'name_jp', 'level', 'type', 'image']

class TraitSerializer(StorageModelSerializer):
    class Meta:
        model = Trait
        fields = ['id', 'text', 'text_uz', 'text_ru', 'text_en', 'text_jp', 'type']

class ExperienceSerializer(StorageModelSerializer):
    class Meta:
        model = Experience
        fields = [
            'id', 'role', 'role_uz', 'role_ru', 'role_en', 'role_jp',
            'company', 'company_uz', 'company_ru', 'company_en', 'company_jp',
            'period', 'desc', 'desc_uz', 'desc_ru', 'desc_en', 'desc_jp', 'logo'
        ]

class ProjectCategorySerializer(StorageModelSerializer):
    projects_count = serializers.IntegerField(source='projects.count', read_only=True)

    class Meta:
        model = ProjectCategory
        fields = ['id', 'name', 'name_uz', 'name_ru', 'name_en', 'name_jp', 'status', 'projects_count']

class ProjectCoverSerializer(StorageModelSerializer):
    class Meta:
        from .models import ProjectCover
        model = ProjectCover
        fields = ['id', 'image']


class ProjectImageSerializer(StorageModelSerializer):
    class Meta:
        model = ProjectImage
        fields = ['id', 'image']

class StableCategoryField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        from django.db.models import Q
        if isinstance(data, int) or (isinstance(data, str) and data.isdigit()):
            try:
                return ProjectCategory.objects.get(pk=int(data))
            except ProjectCategory.DoesNotExist:
                self.fail('does_not_exist', slug_name='id', value=data)
        query = Q()
        for code in ('uz','ru','en','jp'):
            query |= Q(**{f'name_{code}': data})
        matches = list(ProjectCategory.objects.filter(query)[:2])
        if len(matches) != 1:
            raise serializers.ValidationError('Select a category by its ID.')
        return matches[0]

class ProjectSerializer(StorageModelSerializer):
    type = serializers.ChoiceField(choices=['pdf','image'])
    category_id = serializers.IntegerField(source='category.pk', read_only=True)
    category_name_uz = serializers.CharField(source='category.name_uz', read_only=True)
    category_name_ru = serializers.CharField(source='category.name_ru', read_only=True)
    category_name_en = serializers.CharField(source='category.name_en', read_only=True)
    category_name_jp = serializers.CharField(source='category.name_jp', read_only=True)
    category = StableCategoryField(slug_field='name', queryset=ProjectCategory.objects.all())
    images = ProjectImageSerializer(many=True, read_only=True)
    covers = ProjectCoverSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'title_uz', 'title_ru', 'title_en', 'title_jp',
            'slug', 'category', 'category_id', 'category_name_uz', 'category_name_ru', 'category_name_en', 'category_name_jp', 'type', 'file', 'cover_image',
            'description', 'description_uz', 'description_ru', 'description_en', 'description_jp',
            'main_hashtag', 'regular_hashtags', 'total_pages', 'images', 'covers'
        ]

class ContactMessageSerializer(StorageModelSerializer):
    message = serializers.CharField(max_length=10000)
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'company', 'role', 'message', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']

class VisitorLogSerializer(StorageModelSerializer):
    class Meta:
        model = VisitorLog
        fields = ['id', 'ip_address', 'user_agent', 'created_at']


class EducationSerializer(StorageModelSerializer):
    def validate_links(self, links):
        from urllib.parse import urlsplit
        import re
        import json
        if isinstance(links, str):
            try:
                links = json.loads(links)
            except (ValueError, TypeError):
                raise serializers.ValidationError('Provide valid JSON links.')
        if not isinstance(links, list) or len(links) > 10:
            raise serializers.ValidationError('Provide at most 10 links.')
        for link in links:
            if not isinstance(link, dict) or link.get('kind') not in ('url', 'tag'):
                raise serializers.ValidationError('Invalid link type.')
            value = link.get('value', '')
            labels = link.get('labels', {})
            if not isinstance(value, str) or not isinstance(labels, dict) or not any(isinstance(v, str) and v.strip() for v in labels.values()):
                raise serializers.ValidationError('Link text and destination are required.')
            if len(value) > 2000 or any(not isinstance(v, str) or len(v) > 180 for v in labels.values()):
                raise serializers.ValidationError('Link text or destination is too long.')
            if link['kind'] == 'tag':
                if not re.fullmatch(r'#?[\w-]{1,80}', value, re.UNICODE):
                    raise serializers.ValidationError('Use one hashtag without spaces.')
            else:
                url = urlsplit(value)
                if not ((url.scheme in ('http', 'https') and url.netloc and not url.username and not url.password) or (value.startswith('/') and not value.startswith('//') and not url.scheme and not url.netloc)):
                    raise serializers.ValidationError('Use an HTTP(S) URL or a relative site path.')
        return links

    class Meta:
        model = Education
        fields = [
            'id', 'logo', 'name', 'name_uz', 'name_ru', 'name_en', 'name_jp',
            'period', 'description', 'description_uz', 'description_ru', 'description_en', 'description_jp', 'links'
        ]


class ResumeDownloadLogSerializer(StorageModelSerializer):
    class Meta:
        model = ResumeDownloadLog
        fields = ['id', 'name', 'phone', 'email', 'telegram', 'purpose', 'created_at', 'is_read']
        read_only_fields = ['is_read']


from .models import LifeMoment
class LifeMomentSerializer(StorageModelSerializer):
    class Meta:
        model = LifeMoment
        fields = ['id', 'title', 'title_uz', 'title_en', 'title_ru', 'title_jp', 'description', 'description_uz', 'description_en', 'description_ru', 'description_jp', 'date', 'image', 'is_sample']

