from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import AboutMe, Certificate, Skill, Trait, Experience, ProjectCategory, Project, ContactMessage, ResumeDownloadLog

import core.translation

@admin.register(ProjectCategory)
class ProjectCategoryAdmin(TranslationAdmin):
    list_display = ('name', 'status')
    search_fields = ('name',)

@admin.register(Project)
class ProjectAdmin(TranslationAdmin):
    list_display = ('title', 'slug', 'category', 'type')
    list_filter = ('type', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

# Register other models normally
admin.site.register(AboutMe)
admin.site.register(Certificate)
admin.site.register(Skill)
admin.site.register(Trait)
admin.site.register(Experience)
admin.site.register(ContactMessage)
admin.site.register(ResumeDownloadLog)
