import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Create the initial administrator from environment variables, without resetting existing accounts.'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
        if not username or not password:
            raise CommandError('Set DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD')
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write('Administrator already exists; credentials were not changed.')
            return
        User.objects.create_superuser(username=username, email=os.getenv('DJANGO_SUPERUSER_EMAIL', ''), password=password)
        self.stdout.write(self.style.SUCCESS('Administrator created.'))
