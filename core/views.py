from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Count, Max, Min, OuterRef, Subquery
import uuid
from urllib.parse import unquote
from .models import VisitorDevice
from rest_framework.exceptions import ValidationError
from .uploads import RemoteImageField
from rest_framework.decorators import api_view, permission_classes, parser_classes, throttle_classes
from .throttling import LoginThrottle, ContactThrottle, VisitorThrottle
from rest_framework.permissions import AllowAny, IsAdminUser
from .authentication import PublicReadAdminWrite, PublicCreateAdminRead, issue_token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .uploads import UploadJSONParser, VerifiedStorageKey
from .models import AboutMe
from .serializers import AboutMeSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_staff or user.is_superuser:
            return Response({
                'success': True,
                'token': issue_token(user),
                'username': user.username,
                'email': user.email
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'You do not have administrative privileges.'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({'error': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_about(request):
    about_obj, created = AboutMe.objects.get_or_create(id=1, defaults={'name': '', 'bio': ''})
    
    if request.method == 'GET':
        serializer = AboutMeSerializer(about_obj, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == 'POST':
        # Handled as partial update since admin can submit name, bio, or image
        serializer = AboutMeSerializer(about_obj, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .models import Certificate
from .serializers import CertificateSerializer

@api_view(['GET', 'POST'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_certificates(request):
    """List all certificates or create a new one."""
    if request.method == 'GET':
        certs = Certificate.objects.all()
        serializer = CertificateSerializer(certs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = CertificateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE', 'PUT', 'PATCH'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_certificate_detail(request, pk):
    """Delete or update a certificate by primary key."""
    try:
        cert = Certificate.objects.get(pk=pk)
    except Certificate.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'DELETE':
        cert.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method in ['PUT', 'PATCH']:
        serializer = CertificateSerializer(cert, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .models import Skill, Trait
from .serializers import SkillSerializer, TraitSerializer

@api_view(['GET', 'POST'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_skills(request):
    if request.method == 'GET':
        skills = Skill.objects.all()
        serializer = SkillSerializer(skills, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = SkillSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE', 'PUT', 'PATCH'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_skill_detail(request, pk):
    try:
        skill = Skill.objects.get(pk=pk)
    except Skill.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'DELETE':
        skill.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method in ['PUT', 'PATCH']:
        serializer = SkillSerializer(skill, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([PublicReadAdminWrite])
def api_traits(request):
    if request.method == 'GET':
        traits = Trait.objects.all()
        serializer = TraitSerializer(traits, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = TraitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE', 'PUT', 'PATCH'])
@permission_classes([PublicReadAdminWrite])
def api_trait_detail(request, pk):
    try:
        trait = Trait.objects.get(pk=pk)
    except Trait.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'DELETE':
        trait.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method in ['PUT', 'PATCH']:
        serializer = TraitSerializer(trait, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .models import Experience
from .serializers import ExperienceSerializer

def validate_experience_frames(request, job=None):
    files = request.data.get('animation_files', []) if request.content_type == 'application/json' else request.FILES.getlist('animation_files')
    keep = request.data.get('keep_frame_ids')
    order = request.data.get('animation_order')
    if not isinstance(files, list):
        raise ValidationError({'animation_files': 'Invalid frame files.'})
    owned = set(job.animation_frames.values_list('id', flat=True)) if job else set()
    if keep is not None and (not isinstance(keep, list) or not all(isinstance(pk,int) and not isinstance(pk,bool) for pk in keep) or len(keep)!=len(set(keep)) or not set(keep).issubset(owned)):
        raise ValidationError({'keep_frame_ids': 'Frames must belong to this experience.'})
    if order is not None:
        if not isinstance(order,list):
            raise ValidationError({'animation_order': 'Invalid order.'})
        refs=[]
        for ref in order:
            if not isinstance(ref,dict) or len(ref)!=1 or next(iter(ref)) not in ('id','new'):
                raise ValidationError({'animation_order': 'Invalid order.'})
            kind,value=next(iter(ref.items()))
            if not isinstance(value,int) or isinstance(value,bool):
                raise ValidationError({'animation_order': 'Invalid order.'})
            refs.append((kind,value))
        if len(refs)!=len(set(refs)) or set(refs)!={('id',pk) for pk in (keep or [])}|{('new',i) for i in range(len(files))}:
            raise ValidationError({'animation_order': 'Every frame must appear exactly once.'})
    return keep,[RemoteImageField().run_validation(image) for image in files],order


def save_experience_frames(job,keep,files,order):
    from .models import ExperienceFrame
    saved={}
    if keep is not None:
        job.animation_frames.exclude(id__in=keep).delete()
        for position,pk in enumerate(keep):
            saved[pk]=job.animation_frames.get(pk=pk)
            saved[pk].position=position;saved[pk].save(update_fields=['position'])
    start=job.animation_frames.count()
    new=[ExperienceFrame.objects.create(experience=job,image=image,position=start+i) for i,image in enumerate(files)]
    if order is not None:
        for position,ref in enumerate(order):
            frame=saved[ref['id']] if 'id' in ref else new[ref['new']]
            frame.position=position;frame.save(update_fields=['position'])


@api_view(['GET', 'POST'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_experiences(request):
    if request.method == 'GET':
        jobs = Experience.objects.prefetch_related('animation_frames').all()
        serializer = ExperienceSerializer(jobs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = ExperienceSerializer(data=request.data)
        if serializer.is_valid():
            keep,files,order=validate_experience_frames(request)
            with transaction.atomic():
                from django.db.models import Max
                last=Experience.objects.aggregate(last=Max('position'))['last']
                job=serializer.save(position=0 if last is None else last+1)
                save_experience_frames(job,keep,files,order)
            return Response(ExperienceSerializer(job,context={'request':request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([PublicReadAdminWrite])
def api_experience_order(request):
    ids=request.data.get('ids')
    if not isinstance(ids,list) or not all(isinstance(pk,int) and not isinstance(pk,bool) for pk in ids) or len(ids)!=len(set(ids)):
        raise ValidationError({'ids':'Provide each experience ID exactly once.'})
    with transaction.atomic():
        rows=list(Experience.objects.select_for_update().all())
        if set(ids)!={row.id for row in rows}:
            raise ValidationError({'ids':'Experience list changed. Reload and try again.'})
        by_id={row.id:row for row in rows}
        for position,pk in enumerate(ids): by_id[pk].position=position
        Experience.objects.bulk_update(rows,['position'])
    return Response(ExperienceSerializer(Experience.objects.prefetch_related('animation_frames').all(),many=True,context={'request':request}).data)


@api_view(['DELETE', 'PUT', 'PATCH'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_experience_detail(request, pk):
    try:
        job = Experience.objects.get(pk=pk)
    except Experience.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'DELETE':
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method in ['PUT', 'PATCH']:
        serializer = ExperienceSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            keep,files,order=validate_experience_frames(request,job)
            with transaction.atomic():
                serializer.save()
                save_experience_frames(job,keep,files,order)
            return Response(ExperienceSerializer(job,context={'request':request}).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from .models import Education
from .serializers import EducationSerializer

@api_view(['GET', 'POST'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_education(request):
    if request.method == 'GET':
        items = Education.objects.all()
        serializer = EducationSerializer(items, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = EducationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE', 'PUT', 'PATCH'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_education_detail(request, pk):
    try:
        item = Education.objects.get(pk=pk)
    except Education.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method in ['PUT', 'PATCH']:
        serializer = EducationSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from .models import ProjectCategory, Project
from .serializers import ProjectCategorySerializer, ProjectSerializer

@api_view(['GET', 'POST'])
@permission_classes([PublicReadAdminWrite])
def api_categories(request):
    if request.method == 'GET':
        categories = ProjectCategory.objects.all()
        serializer = ProjectCategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = ProjectCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE', 'PUT', 'PATCH'])
@permission_classes([PublicReadAdminWrite])
def api_category_detail(request, pk):
    try:
        category = ProjectCategory.objects.get(pk=pk)
    except ProjectCategory.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'DELETE':
        if category.projects.exists():
            return Response({'error': 'Move or delete the projects before deleting this category.'}, status=409)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method in ['PUT', 'PATCH']:
        serializer = ProjectCategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def validate_project_covers(request, project=None):
    files = request.data.get('cover_images', []) if request.content_type == 'application/json' else request.FILES.getlist('cover_images')
    keep = request.data.get('keep_cover_ids')
    order = request.data.get('cover_order')
    if not isinstance(files, list):
        raise ValidationError({'cover_images': 'Invalid cover files.'})
    owned = set(project.covers.values_list('id', flat=True)) if project else set()
    if project and project.cover_image:
        owned.add(0)  # Legacy cover is converted only when an explicit ordered edit is saved.
    if keep is not None:
        if not isinstance(keep, list) or not all(isinstance(pk, int) and not isinstance(pk, bool) for pk in keep) or len(keep) != len(set(keep)) or not set(keep).issubset(owned):
            raise ValidationError({'keep_cover_ids': 'Covers must belong to this project.'})
    if order is not None:
        expected = {('id', pk) for pk in (keep or [])} | {('new', index) for index in range(len(files))}
        if not isinstance(order, list):
            raise ValidationError({'cover_order': 'Invalid cover order.'})
        refs = []
        for ref in order:
            if not isinstance(ref, dict) or len(ref) != 1 or next(iter(ref)) not in ('id', 'new'):
                raise ValidationError({'cover_order': 'Invalid cover order.'})
            kind, value = next(iter(ref.items()))
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValidationError({'cover_order': 'Invalid cover order.'})
            refs.append((kind, value))
        if len(refs) != len(set(refs)) or set(refs) != expected:
            raise ValidationError({'cover_order': 'Every cover must appear exactly once.'})
    return keep, [RemoteImageField().run_validation(image) for image in files], order


def save_project_covers(project, keep, files, order=None):
    from .models import ProjectCover
    if keep is None and not files and order is None:
        return
    saved = {}
    if keep is not None:
        project.covers.exclude(id__in=keep).delete()
        for position, pk in enumerate(keep):
            if pk == 0:
                saved[0] = ProjectCover.objects.create(project=project, image=project.cover_image.name, position=position)
            else:
                saved[pk] = project.covers.get(pk=pk)
                saved[pk].position = position
                saved[pk].save(update_fields=['position'])
    start = project.covers.count()
    new = [ProjectCover.objects.create(project=project, image=image, position=start+index) for index, image in enumerate(files)]
    if order is not None:
        for position, ref in enumerate(order):
            cover = saved[ref['id']] if 'id' in ref else new[ref['new']]
            cover.position = position
            cover.save(update_fields=['position'])
        first = project.covers.first()
        Project.objects.filter(pk=project.pk).update(cover_image=first.image.name if first else '')
        project.cover_image = first.image.name if first else ''


@api_view(['GET', 'POST'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_projects(request):
    if request.method == 'GET':
        projects = Project.objects.prefetch_related('images', 'covers').select_related('category').order_by('-created_at')
        serializer = ProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = ProjectSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            images_list = (request.data.get('images', []) if request.content_type == 'application/json' else request.FILES.getlist('images'))
            if not isinstance(images_list, list) or len(images_list) > 30:
                raise ValidationError({'images': 'Upload at most 30 images.'})
            field = RemoteImageField()
            validated_images = [field.run_validation(image) for image in images_list]
            keep_covers, cover_files, cover_order = validate_project_covers(request)
            from .models import ProjectImage
            with transaction.atomic():
                project = serializer.save()
                save_project_covers(project, keep_covers, cover_files, cover_order)
                for position, image in enumerate(validated_images):
                    ProjectImage.objects.create(project=project, image=image, position=position)

            # Return fresh serialized data with nested images
            fresh_serializer = ProjectSerializer(project, context={'request': request})
            return Response(fresh_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'DELETE', 'PUT', 'PATCH'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_project_detail(request, pk_or_slug):
    try:
        if str(pk_or_slug).isdigit():
            project = Project.objects.get(pk=pk_or_slug)
        else:
            project = Project.objects.get(slug=pk_or_slug)
    except Project.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'GET':
        serializer = ProjectSerializer(project, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'DELETE':
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method in ['PUT', 'PATCH']:
        serializer = ProjectSerializer(project, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            replacement = None
            if 'images' in request.data:
                images_list = request.data.get('images') if request.content_type == 'application/json' else request.FILES.getlist('images')
                if not isinstance(images_list, list) or len(images_list) > 30:
                    raise ValidationError({'images':'Upload at most 30 images.'})
                replacement = [RemoteImageField().run_validation(image) for image in images_list]
            keep = request.data.get('keep_image_ids')
            if keep is not None:
                if not isinstance(keep, list) or not all(isinstance(pk,int) and not isinstance(pk,bool) for pk in keep) or len(keep) != len(set(keep)):
                    raise ValidationError({'keep_image_ids':'Invalid gallery selection.'})
                owned = set(project.images.values_list('id', flat=True))
                if not set(keep).issubset(owned):
                    raise ValidationError({'keep_image_ids':'Images must belong to this project.'})
                if len(keep) + len(replacement or []) > 30:
                    raise ValidationError({'images':'Upload at most 30 images.'})
            keep_covers, cover_files, cover_order = validate_project_covers(request, project)
            from .models import ProjectImage
            with transaction.atomic():
                serializer.save()
                save_project_covers(project, keep_covers, cover_files, cover_order)
                if keep is not None:
                    project.images.exclude(id__in=keep).delete()
                    for position, pk in enumerate(keep):
                        project.images.filter(pk=pk).update(position=position)
                elif replacement is not None:
                    project.images.all().delete()
                for position, image in enumerate(replacement or [], start=len(keep or [])):
                    ProjectImage.objects.create(project=project, image=image, position=position)
            return Response(ProjectSerializer(project, context={'request': request}).data, status=200)
        return Response(serializer.errors, status=400)


from .models import ContactMessage, VisitorLog, ResumeDownloadLog
from .serializers import ContactMessageSerializer, VisitorLogSerializer, ResumeDownloadLogSerializer
from django.utils import timezone
from django.utils.timesince import timesince
from django.core.mail import send_mail
import datetime

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ContactThrottle])
def api_contact(request):
    serializer = ContactMessageSerializer(data={**request.data, 'status': 'new'})
    if serializer.is_valid():
        instance = serializer.save()
        
        # Send email notification with rich HTML
        subject = f"Yangi Murojaat: {instance.name}"
        message_body = (
            f"Yangi xabar keldi:\n\n"
            f"Ism: {instance.name}\n"
            f"Email: {instance.email}\n"
            f"Kompaniya: {instance.company or 'Kiritilmagan'}\n"
            f"Lavozim: {instance.role or 'Kiritilmagan'}\n\n"
            f"Xabar:\n{instance.message}\n"
        )
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body {{
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              background-color: #f5f6f8;
              color: #2d3748;
              margin: 0;
              padding: 0;
            }}
            .wrapper {{
              width: 100%;
              background-color: #f5f6f8;
              padding: 40px 15px;
              box-sizing: border-box;
            }}
            .container {{
              max-width: 580px;
              margin: 0 auto;
              background: #ffffff;
              border: 1px solid #e2e8f0;
              border-radius: 24px;
              overflow: hidden;
            }}
            .header {{
              background: #111215;
              padding: 30px;
              text-align: center;
              border-bottom: 1px solid #111215;
            }}
            .logo-des {{
              color: #ffffff;
              font-size: 26px;
              font-weight: 800;
              letter-spacing: -1px;
            }}
            .logo-one {{
              color: #CCFF33;
              font-size: 26px;
              font-weight: 800;
              letter-spacing: -1px;
            }}
            .content {{
              padding: 35px 30px;
            }}
            .title {{
              font-size: 20px;
              font-weight: 700;
              color: #1a202c;
              margin-top: 0;
              margin-bottom: 25px;
              text-align: center;
            }}
            .data-table {{
              width: 100%;
              border-collapse: collapse;
              margin-bottom: 25px;
            }}
            .data-table td {{
              padding: 14px 0;
              border-bottom: 1px solid #edf2f7;
            }}
            .label {{
              font-size: 12px;
              color: #718096;
              text-transform: uppercase;
              letter-spacing: 1px;
              font-weight: 600;
              width: 30%;
            }}
            .value {{
              font-size: 15px;
              color: #1a202c;
              font-weight: 500;
            }}
            .message-box {{
              background: rgba(204, 255, 51, 0.05);
              border-left: 3px solid #CCFF33;
              padding: 20px;
              border-radius: 4px 12px 12px 4px;
              margin-top: 20px;
            }}
            .message-text {{
              font-size: 15px;
              color: #2d3748;
              line-height: 1.6;
              margin: 0;
              white-space: pre-wrap;
            }}
            .footer {{
              background-color: #fafafa;
              padding: 20px;
              text-align: center;
              font-size: 12px;
              color: #718096;
              border-top: 1px solid #e2e8f0;
            }}
          </style>
        </head>
        <body>
          <div class="wrapper">
            <div class="container">
              <div class="header">
                <span class="logo-des">des</span><span class="logo-one">one</span>
              </div>
              <div class="content">
                <h2 class="title">Yangi Murojaat Qabul Qilindi</h2>
                <table class="data-table">
                  <tr>
                    <td class="label">Ism:</td>
                    <td class="value">{instance.name}</td>
                  </tr>
                  <tr>
                    <td class="label">Email:</td>
                    <td class="value"><a href="mailto:{instance.email}" style="color: #CCFF33; text-decoration: none;">{instance.email}</a></td>
                  </tr>
                  <tr>
                    <td class="label">Kompaniya:</td>
                    <td class="value">{instance.company or 'Kiritilmagan'}</td>
                  </tr>
                  <tr>
                    <td class="label">Lavozim:</td>
                    <td class="value">{instance.role or 'Kiritilmagan'}</td>
                  </tr>
                </table>
                
                <div style="font-size: 12px; color: rgba(255, 255, 255, 0.4); text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">
                  Xabar matni:
                </div>
                <div class="message-box">
                  <p class="message-text">{instance.message}</p>
                </div>
              </div>
              <div class="footer">
                Ushbu xabar DesOne Portfoliosidagi bog'lanish formasi orqali avtomatik ravishda yuborildi.
              </div>
            </div>
          </div>
        </body>
        </html>
        """
        
        try:
            send_mail(
                subject=subject,
                message=message_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_HOST_USER] if settings.EMAIL_HOST_USER else [],
                html_message=html_content,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([PublicCreateAdminRead])
@throttle_classes([ContactThrottle])
def api_resume_downloads(request):
    if request.method == 'GET':
        logs = ResumeDownloadLog.objects.all().order_by('-created_at')
        serializer = ResumeDownloadLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == 'POST':
        serializer = ResumeDownloadLogSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            
            # Send email notification
            subject = f"Rezyume yuklab olindi: {instance.name}"
            message_body = (
                f"Rezyume yuklab olish so'rovi amalga oshirildi:\n\n"
                f"Ism: {instance.name}\n"
                f"Telefon: {instance.phone}\n"
                f"Telegram / Email: {instance.telegram or instance.email}\n"
                f"Maqsad: {instance.purpose}\n"
            )
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <style>
                body {{
                  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                  background-color: #f5f6f8;
                  color: #2d3748;
                  margin: 0;
                  padding: 0;
                }}
                .wrapper {{
                  width: 100%;
                  background-color: #f5f6f8;
                  padding: 40px 15px;
                  box-sizing: border-box;
                }}
                .container {{
                  max-width: 580px;
                  margin: 0 auto;
                  background: #ffffff;
                  border: 1px solid #e2e8f0;
                  border-radius: 24px;
                  overflow: hidden;
                }}
                .header {{
                  background: #111215;
                  padding: 30px;
                  text-align: center;
                  border-bottom: 1px solid #111215;
                }}
                .logo-des {{
                  color: #ffffff;
                  font-size: 26px;
                  font-weight: 800;
                  letter-spacing: -1px;
                }}
                .logo-one {{
                  color: #CCFF33;
                  font-size: 26px;
                  font-weight: 800;
                  letter-spacing: -1px;
                }}
                .content {{
                  padding: 35px 30px;
                }}
                .title {{
                  font-size: 20px;
                  font-weight: 700;
                  color: #1a202c;
                  margin-top: 0;
                  margin-bottom: 25px;
                  text-align: center;
                }}
                .data-table {{
                  width: 100%;
                  border-collapse: collapse;
                  margin-bottom: 25px;
                }}
                .data-table td {{
                  padding: 14px 0;
                  border-bottom: 1px solid #edf2f7;
                }}
                .label {{
                  font-size: 12px;
                  color: #718096;
                  text-transform: uppercase;
                  letter-spacing: 1px;
                  font-weight: 600;
                  width: 30%;
                }}
                .value {{
                  font-size: 15px;
                  color: #1a202c;
                  font-weight: 500;
                }}
                .message-box {{
                  background: rgba(204, 255, 51, 0.05);
                  border-left: 3px solid #CCFF33;
                  padding: 20px;
                  border-radius: 4px 12px 12px 4px;
                  margin-top: 20px;
                }}
                .message-text {{
                  font-size: 15px;
                  color: #2d3748;
                  line-height: 1.6;
                  margin: 0;
                  white-space: pre-wrap;
                }}
                .footer {{
                  background-color: #fafafa;
                  padding: 20px;
                  text-align: center;
                  font-size: 12px;
                  color: #718096;
                  border-top: 1px solid #e2e8f0;
                }}
              </style>
            </head>
            <body>
              <div class="wrapper">
                <div class="container">
                  <div class="header">
                    <span class="logo-des">des</span><span class="logo-one">one</span>
                  </div>
                  <div class="content">
                    <h2 class="title">Rezyume Yuklab Olindi</h2>
                    <table class="data-table">
                      <tr>
                        <td class="label">Ism:</td>
                        <td class="value">{instance.name}</td>
                      </tr>
                      <tr>
                        <td class="label">Telefon:</td>
                        <td class="value">{instance.phone}</td>
                      </tr>
                      <tr>
                        <td class="label">Telegram / Email:</td>
                        <td class="value">{instance.telegram or instance.email or "—"}</td>
                      </tr>
                    </table>
                    
                    <div style="font-size: 12px; color: rgba(255, 255, 255, 0.4); text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">
                      Yuklab olish maqsadi:
                    </div>
                    <div class="message-box">
                      <p class="message-text">{instance.purpose}</p>
                    </div>
                  </div>
                  <div class="footer">
                    Ushbu bildirishnoma DesOne Portfoliosidagi Rezyume yuklab olish so'rovi orqali avtomatik ravishda yuborildi.
                  </div>
                </div>
              </div>
            </body>
            </html>
            """
            
            try:
                send_mail(
                    subject=subject,
                    message=message_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.EMAIL_HOST_USER] if settings.EMAIL_HOST_USER else [],
                    html_message=html_content,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {e}")
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE', 'PATCH'])
@permission_classes([IsAdminUser])
def api_resume_download_detail(request, pk):
    try:
        log = ResumeDownloadLog.objects.get(pk=pk)
    except ResumeDownloadLog.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'PATCH':
        log.is_read = True
        log.save(update_fields=['is_read'])
        return Response(ResumeDownloadLogSerializer(log).data)
    log.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_messages(request):
    messages = ContactMessage.objects.all().order_by('-created_at')
    serializer = ContactMessageSerializer(messages, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE', 'PATCH'])
@permission_classes([IsAdminUser])
def api_message_detail(request, pk):
    try:
        msg = ContactMessage.objects.get(pk=pk)
    except ContactMessage.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        msg.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method == 'PATCH':
        serializer = ContactMessageSerializer(msg, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([VisitorThrottle])
def api_visitor_log(request):
    device_id = request.data.get('device_id')
    try:
        device_id = uuid.UUID(str(device_id)) if device_id else None
    except (ValueError, AttributeError):
        return Response({'device_id': 'Invalid device ID.'}, status=400)
    if device_id and VisitorDevice.objects.filter(device_id=device_id, excluded_from_analytics=True).exists():
        return Response({'success': True, 'excluded': True}, status=200)
    device_type = request.data.get('device_type', 'unknown')
    if device_type not in ('mobile', 'tablet', 'desktop', 'unknown'):
        return Response({'device_type': 'Invalid device type.'}, status=400)
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_address:
        ip_address = ip_address.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Simple rate limit to prevent duplicate logs on immediate page refresh
    thirty_seconds_ago = timezone.now() - datetime.timedelta(seconds=30)
    recent = VisitorLog.objects.filter(created_at__gte=thirty_seconds_ago)
    recent_log = (recent.filter(device_id=device_id) if device_id else recent.filter(ip_address=ip_address)).exists()
    
    if not recent_log:
        if device_id:
            VisitorDevice.objects.get_or_create(device_id=device_id)
        VisitorLog.objects.create(ip_address=ip_address, user_agent=user_agent, device_id=device_id, device_type=device_type, country_code=request.META.get('HTTP_X_VERCEL_IP_COUNTRY', '')[:2], region=unquote(request.META.get('HTTP_X_VERCEL_IP_COUNTRY_REGION', ''))[:100], city=unquote(request.META.get('HTTP_X_VERCEL_IP_CITY', ''))[:100])
        return Response({'success': True}, status=status.HTTP_201_CREATED)
    return Response({'success': False, 'message': 'Too many requests'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_dashboard_stats(request):
    visible_visits = VisitorLog.objects.exclude(device_id__in=VisitorDevice.objects.filter(excluded_from_analytics=True).values('device_id'))
    # Total counts
    total_real_views = visible_visits.count()
    total_views = total_real_views
    
    total_projects = Project.objects.count()
    total_messages = ContactMessage.objects.count()
    new_messages = ContactMessage.objects.filter(status='new').count()
    total_skills = Skill.objects.count()
    
    from zoneinfo import ZoneInfo
    chart_timezone = ZoneInfo('Asia/Tashkent')
    today = timezone.localtime(timezone.now(), chart_timezone).date()
    period = request.query_params.get('period', 'week')
    if period not in ('week', 'month', 'year'):
        return Response({'error': 'Invalid analytics period.'}, status=400)
    days_data = []
    for i in range((11 if period == 'year' else 29 if period == 'month' else 6), -1, -1):
        if period == 'year':
            month_index = today.year * 12 + today.month - 1 - i
            day = datetime.date(month_index // 12, month_index % 12 + 1, 1)
            next_index = month_index + 1
            next_day = datetime.date(next_index // 12, next_index % 12 + 1, 1)
        else:
            day = today - datetime.timedelta(days=i)
            next_day = day + datetime.timedelta(days=1)
        start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min), chart_timezone)
        end = timezone.make_aware(datetime.datetime.combine(next_day, datetime.time.min), chart_timezone)
        counts = dict(visible_visits.filter(created_at__gte=start, created_at__lt=end).values('device_type').annotate(total=Count('id')).values_list('device_type', 'total'))
        days_data.append({'day':day.strftime('%a'), 'date':day.isoformat(), 'count':sum(counts.values()), 'devices':{kind:counts.get(kind, 0) for kind in ('desktop', 'mobile', 'tablet', 'unknown')}})

    # Recent activities
    activities = []
    
    # Latest projects (up to 3)
    latest_projects = Project.objects.prefetch_related('images', 'covers').select_related('category').order_by('-created_at')[:3]
    for p in latest_projects:
        # Time ago string
        time_str = timesince(p.created_at).split(',')[0] + ' ago'
        if '0 minutes' in time_str:
            time_str = 'Just now'
        activities.append({
            'dot_class': 'dot-lime',
            'message': f"Yangi loyiha qo'shildi: '{p.title}'",
            'time': time_str,
            'timestamp': p.created_at
        })
        
    # Latest messages (up to 3)
    latest_msgs = ContactMessage.objects.all().order_by('-created_at')[:3]
    for m in latest_msgs:
        time_str = timesince(m.created_at).split(',')[0] + ' ago'
        if '0 minutes' in time_str:
            time_str = 'Just now'
        activities.append({
            'dot_class': 'dot-cyan',
            'message': f"Yangi murojaat qabul qilindi: {m.name}",
            'time': time_str,
            'timestamp': m.created_at
        })

    # Sort activities by timestamp descending
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    # Map to clean items for frontend
    formatted_activities = [{
        'dot_class': act['dot_class'],
        'message': act['message'],
        'time': act['time'],
        'timestamp': act['timestamp']
    } for act in activities[:5]] # Top 5 recent activities

    visits = visible_visits.exclude(device_id=None).order_by('-created_at', '-id')
    requested_device = request.query_params.get('visits_device')
    if requested_device:
        try:
            visits = visits.filter(device_id=uuid.UUID(requested_device))
        except (ValueError, AttributeError):
            return Response({'error': 'Invalid device ID.'}, status=400)
    try:
        visits_page = max(0, int(request.query_params.get('visits_page', 0)))
    except ValueError:
        return Response({'error': 'Invalid page.'}, status=400)
    visits = visits.annotate(nickname=Subquery(VisitorDevice.objects.filter(device_id=OuterRef('device_id')).values('nickname')[:1]), short_id=Subquery(VisitorDevice.objects.filter(device_id=OuterRef('device_id')).values('id')[:1]))
    visit_rows = list(visits.values('id', 'device_id', 'short_id', 'nickname', 'device_type', 'ip_address', 'country_code', 'region', 'city', 'created_at')[visits_page * 30:(visits_page + 1) * 30 + 1])

    return Response({
        'visitor_entries': visit_rows[:30],
        'visitor_entries_more': len(visit_rows) > 30,
        'total_views': total_views,
        'total_projects': total_projects,
        'total_messages': total_messages,
        'new_messages': new_messages,
        'total_skills': total_skills,
        'visitor_analytics': days_data,
        'device_summary': list(visible_visits.exclude(device_id=None).values('device_type').annotate(count=Count('device_id', distinct=True)).order_by('device_type')),
        'visitor_devices': list(visible_visits.exclude(device_id=None).values('device_id').annotate(short_id=Subquery(VisitorDevice.objects.filter(device_id=OuterRef('device_id')).values('id')[:1]), visits=Count('id'), first_seen=Min('created_at'), last_seen=Max('created_at'), device_type=Max('device_type'), ip_address=Subquery(visible_visits.filter(device_id=OuterRef('device_id')).order_by('-created_at').values('ip_address')[:1]), country_code=Subquery(visible_visits.filter(device_id=OuterRef('device_id')).order_by('-created_at').values('country_code')[:1]), region=Subquery(visible_visits.filter(device_id=OuterRef('device_id')).order_by('-created_at').values('region')[:1]), city=Subquery(visible_visits.filter(device_id=OuterRef('device_id')).order_by('-created_at').values('city')[:1])).order_by('-last_seen')[:100]),
        'recent_activities': formatted_activities
    }, status=status.HTTP_200_OK)



from .models import LifeMoment
from .serializers import LifeMomentSerializer
@api_view(['GET', 'POST'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_life(request):
    if request.method == 'GET':
        return Response(LifeMomentSerializer(LifeMoment.objects.all(), many=True, context={'request': request}).data)
    serializer = LifeMomentSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=201)

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([PublicReadAdminWrite])
@parser_classes([MultiPartParser, FormParser, UploadJSONParser])
def api_life_detail(request, pk):
    from django.shortcuts import get_object_or_404
    item = get_object_or_404(LifeMoment, pk=pk)
    if request.method == 'DELETE':
        item.delete()
        return Response(status=204)
    serializer = LifeMomentSerializer(item, data=request.data, partial=True, context={'request': request}) if request.method == 'PATCH' else LifeMomentSerializer(item, context={'request': request})
    if request.method == 'PATCH':
        serializer.is_valid(raise_exception=True)
        serializer.save()
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def api_device_nickname(request, device_id):
    try:
        device = VisitorDevice.objects.get(device_id=device_id)
    except VisitorDevice.DoesNotExist:
        return Response({'error': 'Device not found'}, status=404)
    nickname = request.data.get('nickname')
    if not isinstance(nickname, str) or len(nickname.strip()) > 80:
        return Response({'error': 'Nickname must contain at most 80 characters'}, status=400)
    device.nickname = nickname.strip()
    device.save(update_fields=['nickname'])
    return Response({'nickname': device.nickname})

