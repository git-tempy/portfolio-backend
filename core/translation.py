from modeltranslation.translator import translator, TranslationOptions
from .models import Project, ProjectCategory, AboutMe, Certificate, Skill, Trait, Experience, Education

class ProjectTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'main_hashtag', 'regular_hashtags')

class ProjectCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

class AboutMeTranslationOptions(TranslationOptions):
    fields = ('name', 'bio')

class CertificateTranslationOptions(TranslationOptions):
    fields = ('title',)

class SkillTranslationOptions(TranslationOptions):
    fields = ('name',)

class TraitTranslationOptions(TranslationOptions):
    fields = ('text',)

class ExperienceTranslationOptions(TranslationOptions):
    fields = ('role', 'company', 'desc')

class EducationTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

translator.register(Project, ProjectTranslationOptions)
translator.register(ProjectCategory, ProjectCategoryTranslationOptions)
translator.register(AboutMe, AboutMeTranslationOptions)
translator.register(Certificate, CertificateTranslationOptions)
translator.register(Skill, SkillTranslationOptions)
translator.register(Trait, TraitTranslationOptions)
translator.register(Experience, ExperienceTranslationOptions)
translator.register(Education, EducationTranslationOptions)
