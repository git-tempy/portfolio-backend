"""Serve public WebP previews without publishing object-storage URLs.

Fetch Metadata restricts ordinary browser navigation, not copying or scraping.
Original storage must remain private; it is never proxied or redirected here.
"""
import hashlib
from pathlib import PurePosixPath

from django.core import signing
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_http_methods
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from .authentication import AdminTokenAuthentication
from .image_processing import web_image

SALT = 'portfolio-public-webp-v1'
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_BYTES = 40 * 1024 * 1024


def valid_image_key(key):
    if not isinstance(key, str) or not key or len(key) > 1024:
        return False
    path = PurePosixPath(key)
    return (not path.is_absolute() and '..' not in path.parts and '\\' not in key
            and ':' not in key and path.parts[0] not in {'private', 'previews'}
            and path.suffix.lower() in IMAGE_EXTENSIONS)


def protected_image_url(key):
    if not valid_image_key(key):
        raise ValueError('Invalid public image key')
    token = signing.Signer(salt=SALT).sign_object({'key': key}, compress=True)
    return reverse('protected_image', kwargs={'token': token})


def browser_allowed(request):
    # Relative image URLs are loaded through the frontend's same-origin proxy.
    site = request.headers.get('Sec-Fetch-Site')
    destination = request.headers.get('Sec-Fetch-Dest')
    if site != 'same-origin':
        return False
    if destination == 'image':
        return True
    # The authenticated admin editor needs fetch()->Blob->canvas access.
    if destination == 'empty':
        try:
            authenticated = AdminTokenAuthentication().authenticate(request)
            return bool(authenticated and authenticated[0].is_staff)
        except AuthenticationFailed:
            return False
    return False


def response(body=b'', status=200, content_type='text/plain'):
    result = HttpResponse(body, status=status, content_type=content_type)
    result['Cache-Control'] = 'private, max-age=300' if status == 200 else 'no-store'
    # Critical: a cached <img> response must not satisfy a new-tab navigation.
    patch_vary_headers(result, ('Sec-Fetch-Dest', 'Sec-Fetch-Site', 'Authorization'))
    result['Cross-Origin-Resource-Policy'] = 'same-origin'
    result['X-Content-Type-Options'] = 'nosniff'
    return result


@require_http_methods(['GET', 'HEAD'])
def protected_image(request, token):
    if not browser_allowed(request):
        return response(status=403)
    try:
        payload = signing.Signer(salt=SALT).unsign_object(token)
        key = payload['key']
        if not valid_image_key(key):
            return response(status=404)
    except (signing.BadSignature, ValueError, KeyError, TypeError):
        return response(status=404)

    # Legacy JPG/PNG get a persistent WebP derivative on first access. No DB
    # rewrite or destructive bulk conversion; UUID storage keys are immutable.
    digest = hashlib.sha256(key.encode()).hexdigest()
    preview_key = f'previews/v1/{digest}.webp'
    try:
        if not default_storage.exists(preview_key):
            with default_storage.open(key, 'rb') as source:
                content = source.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES:
                return response(status=413)
            preview = web_image(content, key)
            preview_key = default_storage.save(preview_key, preview)
        with default_storage.open(preview_key, 'rb') as preview:
            body = preview.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            return response(status=413)
    except (FileNotFoundError, OSError):
        return response(status=404)
    except ValidationError:
        return response(status=415)
    result = response(b'' if request.method == 'HEAD' else body,
                      content_type='image/webp')
    result['Content-Length'] = str(len(body))
    return result
