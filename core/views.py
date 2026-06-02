from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import AboutMe
from .serializers import AboutMeSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
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
                'username': user.username,
                'email': user.email
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'You do not have administrative privileges.'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({'error': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def api_about(request):
    about_obj, created = AboutMe.objects.get_or_create(id=1)
    
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
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
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
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
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
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
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
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
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
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def api_experiences(request):
    if request.method == 'GET':
        jobs = Experience.objects.all()
        serializer = ExperienceSerializer(jobs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = ExperienceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE', 'PUT', 'PATCH'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from .models import Education
from .serializers import EducationSerializer

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
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
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
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
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
def api_category_detail(request, pk):
    try:
        category = ProjectCategory.objects.get(pk=pk)
    except ProjectCategory.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'DELETE':
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    elif request.method in ['PUT', 'PATCH']:
        serializer = ProjectCategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def api_projects(request):
    if request.method == 'GET':
        projects = Project.objects.all().order_by('-created_at')
        serializer = ProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = ProjectSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            project = serializer.save()
            
            # Save multiple images for Image Gallery
            from .models import ProjectImage
            images_list = request.FILES.getlist('images')
            for img in images_list:
                ProjectImage.objects.create(project=project, image=img)
            
            # Return fresh serialized data with nested images
            fresh_serializer = ProjectSerializer(project, context={'request': request})
            return Response(fresh_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'DELETE', 'PUT', 'PATCH'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .models import ContactMessage, VisitorLog, ResumeDownloadLog
from .serializers import ContactMessageSerializer, VisitorLogSerializer, ResumeDownloadLogSerializer
from django.utils import timezone
from django.utils.timesince import timesince
from django.core.mail import send_mail
import datetime

@api_view(['POST'])
@permission_classes([AllowAny])
def api_contact(request):
    serializer = ContactMessageSerializer(data=request.data)
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
                from_email='xanter9656@gmail.com',
                recipient_list=['xanter9656@gmail.com'],
                html_message=html_content,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
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
                f"Email: {instance.email}\n"
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
                        <td class="label">Email:</td>
                        <td class="value"><a href="mailto:{instance.email}" style="color: #CCFF33; text-decoration: none;">{instance.email}</a></td>
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
                    from_email='xanter9656@gmail.com',
                    recipient_list=['xanter9656@gmail.com'],
                    html_message=html_content,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {e}")
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def api_resume_download_detail(request, pk):
    try:
        log = ResumeDownloadLog.objects.get(pk=pk)
    except ResumeDownloadLog.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    log.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_messages(request):
    messages = ContactMessage.objects.all().order_by('-created_at')
    serializer = ContactMessageSerializer(messages, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE', 'PATCH'])
@permission_classes([AllowAny])
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
def api_visitor_log(request):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_address:
        ip_address = ip_address.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Simple rate limit to prevent duplicate logs on immediate page refresh
    thirty_seconds_ago = timezone.now() - datetime.timedelta(seconds=30)
    recent_log = VisitorLog.objects.filter(ip_address=ip_address, created_at__gte=thirty_seconds_ago).exists()
    
    if not recent_log:
        VisitorLog.objects.create(ip_address=ip_address, user_agent=user_agent)
        return Response({'success': True}, status=status.HTTP_201_CREATED)
    return Response({'success': False, 'message': 'Too many requests'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def api_dashboard_stats(request):
    # Total counts
    total_real_views = VisitorLog.objects.count()
    total_views = total_real_views
    
    total_projects = Project.objects.count()
    total_messages = ContactMessage.objects.count()
    new_messages = ContactMessage.objects.filter(status='new').count()
    total_skills = Skill.objects.count()
    
    # 7-day visitor analytics
    # Let's count views for the last 7 calendar days
    today = timezone.now().date()
    days_data = []
    
    # We want Mon to Sun or last 7 days. Let's do last 7 days ending today.
    # To map to Mon, Tue, etc., let's get the weekday labels.
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))
        day_end = timezone.make_aware(datetime.datetime.combine(day, datetime.time.max))
        count = VisitorLog.objects.filter(created_at__range=(day_start, day_end)).count()
        days_data.append({
            'day': day.strftime('%a'), # E.g., 'Mon', 'Tue'
            'count': count
        })

    # Recent activities
    activities = []
    
    # Latest projects (up to 3)
    latest_projects = Project.objects.all().order_by('-created_at')[:3]
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

    # Latest skills (up to 3) - since Skill has no created_at, we order by id desc
    # and just give a dummy "recently" or "some days ago" timestamp to keep it simple,
    # or just show them if any
    latest_skills = Skill.objects.all().order_by('-id')[:3]
    for i, s in enumerate(latest_skills):
        # Deterministic dummy time since we don't have created_at
        time_str = f"{i+1} days ago"
        activities.append({
            'dot_class': 'dot-purple',
            'message': f"Skills yangilandi: '{s.name}' -> {s.level}%",
            'time': time_str,
            'timestamp': timezone.now() - datetime.timedelta(days=i+1)
        })

    # Sort activities by timestamp descending
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    # Map to clean items for frontend
    formatted_activities = [{
        'dot_class': act['dot_class'],
        'message': act['message'],
        'time': act['time']
    } for act in activities[:5]] # Top 5 recent activities

    # If activities is empty, supply default template ones
    if not formatted_activities:
        formatted_activities = [
            {'dot_class': 'dot-lime', 'message': "Yangi loyiha qo'shildi: 'Crypto Wallet Website'", 'time': '2 hours ago'},
            {'dot_class': 'dot-cyan', 'message': "Yangi murojaat qabul qilindi: Asrorbek Alimov", 'time': 'Yesterday'},
            {'dot_class': 'dot-purple', 'message': "Skills yangilandi: 'Figma UI/UX' -> 95%", 'time': '3 days ago'}
        ]

    return Response({
        'total_views': total_views,
        'total_projects': total_projects,
        'total_messages': total_messages,
        'new_messages': new_messages,
        'total_skills': total_skills,
        'visitor_analytics': days_data,
        'recent_activities': formatted_activities
    }, status=status.HTTP_200_OK)


