import logging
from django.core.management.base import BaseCommand
from core.models import AboutMe, Certificate, Skill, Trait, Experience, ProjectCategory, Project

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Delete demo entries from the database, keeping only real data."

    def handle(self, *args, **options):
        # Define criteria for demo detection per model
        demo_projects = Project.objects.filter(title="")
        demo_categories = ProjectCategory.objects.filter(name="")
        demo_certificates = Certificate.objects.filter(title="Demo Certificate")
        demo_skills = Skill.objects.filter(name="Demo Skill")
        demo_traits = Trait.objects.filter(text="Demo Trait")
        demo_experiences = Experience.objects.filter(role="Demo Role")
        demo_about = AboutMe.objects.filter(name="Demo")

        # Delete if any
        for qs, name in [
            (demo_projects, "Project"),
            (demo_categories, "ProjectCategory"),
            (demo_certificates, "Certificate"),
            (demo_skills, "Skill"),
            (demo_traits, "Trait"),
            (demo_experiences, "Experience"),
            (demo_about, "AboutMe"),
        ]:
            count = qs.count()
            if count:
                qs.delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted {count} demo {name} record(s)."))
            else:
                self.stdout.write(f"No demo {name} records found.")
