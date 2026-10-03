import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.authentication import issue_token
from core.models import VisitorDevice, VisitorLog
from core.serializers import ResumeDownloadLogSerializer

class NicknameResumeTests(TestCase):
    def test_nickname_is_admin_only_and_persists_without_changing_identity(self):
        device=VisitorDevice.objects.create(device_id=uuid.uuid4())
        VisitorLog.objects.create(device_id=device.device_id, device_type='desktop')
        client=APIClient()
        url=f'/api/devices/{device.device_id}/nickname/'
        self.assertIn(client.patch(url, {'nickname':'My laptop'}, format='json').status_code, [401,403])
        user=get_user_model().objects.create_user('nickname-admin',is_staff=True)
        client.credentials(HTTP_AUTHORIZATION='Bearer '+issue_token(user))
        self.assertEqual(client.patch(url, {'nickname':'My laptop'}, format='json').status_code,200)
        device.refresh_from_db()
        rows=client.get('/api/dashboard/stats/').json()['visitor_entries']
        self.assertEqual(rows[0]['nickname'],'My laptop')
        self.assertEqual(rows[0]['short_id'],device.pk)
        self.assertEqual(client.patch(url, {'nickname':'x'*81}, format='json').status_code,400)

    def test_resume_accepts_optional_telegram_without_email(self):
        for telegram in ['', '@example']:
            serializer=ResumeDownloadLogSerializer(data={'name':'Example','phone':'123','purpose':'Review','telegram':telegram})
            self.assertTrue(serializer.is_valid(),serializer.errors)

