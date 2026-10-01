from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.authentication import issue_token

class AdminAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('test-admin', password='test-password-only', is_staff=True)

    def test_public_access(self):
        for path in ['/api/messages/', '/api/dashboard/stats/', '/api/resume-downloads/']:
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.post('/api/portfolio/categories/', {'name': 'test'}).status_code, 401)
        self.assertEqual(self.client.get('/api/portfolio/projects/').status_code, 200)

    def test_admin_access(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + issue_token(self.user))
        self.assertEqual(self.client.get('/api/messages/').status_code, 200)
        self.assertEqual(self.client.get('/api/dashboard/stats/').data['recent_activities'], [])

    def test_revocation(self):
        token = issue_token(self.user)
        self.user.set_password('changed-test-password')
        self.user.save()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        self.assertEqual(self.client.get('/api/messages/').status_code, 401)

    def test_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid')
        self.assertEqual(self.client.get('/api/messages/').status_code, 401)
