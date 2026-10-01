"""Database-backed limits shared by all Vercel instances."""
import time
from django.db import transaction
from django.utils.crypto import salted_hmac
from rest_framework.throttling import BaseThrottle
from .models import RequestLimit

class DatabaseThrottle(BaseThrottle):
    limit = 5
    scope = 'public'

    def allow_request(self, request, view):
        if request.method != 'POST':
            return True
        # Vercel supplies this header; local requests use REMOTE_ADDR.
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        address = forwarded.split(',')[-1].strip() or request.META.get('REMOTE_ADDR', 'unknown')
        key = salted_hmac('request-limit', self.scope + ':' + address).hexdigest()
        now = int(time.time())
        window = now // 60
        self.wait_seconds = 60 - now % 60
        with transaction.atomic():
            RequestLimit.objects.get_or_create(key=key)
            row = RequestLimit.objects.select_for_update().get(key=key)
            if row.window != window:
                row.window, row.count = window, 0
            if row.count >= self.limit:
                return False
            row.count += 1
            row.save()
        return True

    def wait(self):
        return self.wait_seconds

class LoginThrottle(DatabaseThrottle):
    scope = 'login'

class ContactThrottle(DatabaseThrottle):
    scope = 'contact'

class VisitorThrottle(DatabaseThrottle):
    scope = 'visitor'
    limit = 30
