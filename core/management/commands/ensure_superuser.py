from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates or updates the superuser desone with the specified password'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'desone'
        password = 'feruzxondesone'
        email = 'xanter9656@gmail.com'

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' updated successfully."))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
