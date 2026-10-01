"""Vercel build: schema upgrades and persistent media configuration."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
from django.core.management import call_command
from django.core.files.storage import default_storage
from django.conf import settings

call_command('migrate', interactive=False)
if os.getenv('DJANGO_SUPERUSER_PASSWORD'):
    call_command('ensure_superuser')
else:
    from django.contrib.auth import get_user_model
    if not get_user_model().objects.filter(is_staff=True, is_active=True).exists():
        raise RuntimeError('Set the initial DJANGO_SUPERUSER_PASSWORD in Vercel before deploying')
if hasattr(default_storage, 'bucket_name'):
    client = default_storage.connection.meta.client
    client.head_bucket(Bucket=default_storage.bucket_name)
    client.put_bucket_cors(Bucket=default_storage.bucket_name, CORSConfiguration={
        'CORSRules': [{
            'AllowedOrigins': settings.CORS_ALLOWED_ORIGINS,
            'AllowedMethods': ['GET', 'HEAD', 'PUT'],
            'AllowedHeaders': ['*'], 'ExposeHeaders': ['ETag'], 'MaxAgeSeconds': 3600,
        }],
    })
call_command('collectstatic', interactive=False)
