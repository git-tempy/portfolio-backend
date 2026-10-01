from django.core import signing
from django.utils.crypto import salted_hmac, constant_time_compare
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission, SAFE_METHODS

TOKEN_SALT = 'portfolio-admin-v1'

def issue_token(user):
    return signing.dumps({'id': user.pk, 'version': salted_hmac(TOKEN_SALT, user.password).hexdigest()}, salt=TOKEN_SALT)

class AdminTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != b'bearer':
            return None
        if len(header) != 2:
            raise AuthenticationFailed('Invalid authorization header')
        try:
            payload = signing.loads(header[1].decode(), salt=TOKEN_SALT, max_age=43200)
            user = get_user_model().objects.get(pk=payload['id'], is_active=True)
            if not constant_time_compare(payload['version'], salted_hmac(TOKEN_SALT, user.password).hexdigest()) or not user.is_staff:
                raise ValueError('Invalid administrator')
        except (signing.BadSignature, ValueError, KeyError, UnicodeError, get_user_model().DoesNotExist):
            raise AuthenticationFailed('Session expired. Please sign in again.')
        return user, header[1]

    def authenticate_header(self, request):
        return 'Bearer'

class PublicReadAdminWrite(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_active and request.user.is_staff)

class PublicCreateAdminRead(BasePermission):
    def has_permission(self, request, view):
        return request.method == 'POST' or bool(request.user and request.user.is_active and request.user.is_staff)
