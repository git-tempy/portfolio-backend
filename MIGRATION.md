# Backend migration

The previous Render/API implementation is preserved on `old` at commit 43f0e56.
The new backend uses Vercel, Neon Postgres, and private Neon S3-compatible storage.
No portfolio content is seeded by the build. Database migrations preserve existing rows.

## Production environment

Configure secrets in Vercel, never in Git:

- DATABASE_URL (Neon Postgres with TLS)
- DJANGO_SECRET_KEY (random, persistent across deployments)
- S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY
- S3_BUCKET_NAME=portfolio-media, S3_REGION_NAME=eu-central-1
- DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD for first deployment
- Optional DJANGO_SUPERUSER_EMAIL
- Optional EMAIL_HOST_USER and EMAIL_HOST_PASSWORD to enable contact email

After the initial administrator exists, remove DJANGO_SUPERUSER_PASSWORD from Vercel.
Subsequent builds do not reset passwords. Contact messages are saved even without SMTP.

Set frontend VITE_API_BASE_URL=https://desonebackend.vercel.app and rebuild it.
Keep backend Production Branch set to main. GitHub pushes then trigger Vercel builds.
The build runs migrations, configures storage CORS, and checks that the media bucket exists.

Admin sessions expire after 12 hours and are invalidated by password changes.
Large uploads go directly to storage via short-lived signed URLs. Metadata is checked
before accepting an upload receipt. Public APIs cannot modify content or read messages.

## Checks

python manage.py check
python manage.py test core.test_admin_access core.test_uploads
python manage.py makemigrations --check --dry-run

Old database rows and files require an export from the old database/storage. A Git branch
backs up code only, not Render database contents or uploaded files.
