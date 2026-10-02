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
    category = StableCategoryField(slug_field='name', queryset=ProjectCategory.objects.all())
    images = ProjectImageSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'title_uz', 'title_ru', 'title_en', 'title_jp',
            'slug', 'category', 'category_id', 'type', 'file', 'cover_image',
            'description', 'description_uz', 'description_ru', 'description_en', 'description_jp',
            'main_hashtag', 'regular_hashtags', 'total_pages', 'images'
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
    class Meta:
        model = Education
        fields = [
            'id', 'logo', 'name', 'name_uz', 'name_ru', 'name_en', 'name_jp',
            'period', 'description', 'description_uz', 'description_ru', 'description_en', 'description_jp'
        ]


class ResumeDownloadLogSerializer(StorageModelSerializer):
    class Meta:
        model = ResumeDownloadLog
        fields = ['id', 'name', 'phone', 'email', 'purpose', 'created_at']


from .models import LifeMoment
class LifeMomentSerializer(StorageModelSerializer):
    class Meta:
        model = LifeMoment
        fields = ['id', 'title', 'title_uz', 'title_en', 'title_ru', 'title_jp', 'description', 'description_uz', 'description_en', 'description_ru', 'description_jp', 'date', 'image', 'is_sample']
