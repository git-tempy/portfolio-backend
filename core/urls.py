"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    api_login, api_about, api_certificates, api_certificate_detail, 
    api_skills, api_skill_detail, api_traits, api_trait_detail, 
    api_experiences, api_experience_detail,
    api_categories, api_category_detail, api_projects, api_project_detail,
    api_contact, api_messages, api_message_detail, api_visitor_log, api_dashboard_stats,
    api_education, api_education_detail, api_resume_downloads, api_resume_download_detail
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', api_login, name='api_login'),
    path('api/about/', api_about, name='api_about'),
    path('api/certificates/', api_certificates, name='api_certificates'),
    path('api/certificates/<int:pk>/', api_certificate_detail, name='api_certificate_detail'),
    path('api/skills/', api_skills, name='api_skills'),
    path('api/skills/<int:pk>/', api_skill_detail, name='api_skill_detail'),
    path('api/traits/', api_traits, name='api_traits'),
    path('api/traits/<int:pk>/', api_trait_detail, name='api_trait_detail'),
    path('api/experiences/', api_experiences, name='api_experiences'),
    path('api/experiences/<int:pk>/', api_experience_detail, name='api_experience_detail'),
    path('api/education/', api_education, name='api_education'),
    path('api/education/<int:pk>/', api_education_detail, name='api_education_detail'),
    path('api/portfolio/categories/', api_categories, name='api_categories'),
    path('api/portfolio/categories/<int:pk>/', api_category_detail, name='api_category_detail'),
    path('api/portfolio/projects/', api_projects, name='api_projects'),
    path('api/portfolio/projects/<str:pk_or_slug>/', api_project_detail, name='api_project_detail'),
    
    path('api/contact/', api_contact, name='api_contact'),
    path('api/messages/', api_messages, name='api_messages'),
    path('api/messages/<int:pk>/', api_message_detail, name='api_message_detail'),
    path('api/visitor/log/', api_visitor_log, name='api_visitor_log'),
    path('api/dashboard/stats/', api_dashboard_stats, name='api_dashboard_stats'),
    path('api/resume-downloads/', api_resume_downloads, name='api_resume_downloads'),
    path('api/resume-downloads/<int:pk>/', api_resume_download_detail, name='api_resume_download_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




