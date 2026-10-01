from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.authentication import issue_token
from core.models import Project, ProjectCategory

class HardeningTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('auditadmin', password='test-only', is_staff=True)

    def test_root_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://desone.vercel.app/desone_adminstration')
        self.assertEqual(response['X-Frame-Options'], 'DENY')

    def test_login_limit(self):
        for _ in range(5):
            self.assertEqual(self.client.post('/api/login/', {'username': 'wrong', 'password': 'wrong'}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/login/', {'username': 'wrong', 'password': 'wrong'}, format='json').status_code, 429)

    def test_invalid_gallery_does_not_create_project(self):
        category = ProjectCategory.objects.create(name='design')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + issue_token(self.user))
        response = self.client.post('/api/portfolio/projects/', {'title': 'Test', 'category': category.name, 'type': 'image', 'images': ['arbitrary/storage/key.jpg']}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)

    def test_category_with_projects_is_preserved(self):
        category = ProjectCategory.objects.create(name='design')
        Project.objects.create(title='Test', category=category, type='image')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + issue_token(self.user))
        self.assertEqual(self.client.delete(f'/api/portfolio/categories/{category.pk}/').status_code, 409)
        self.assertTrue(Project.objects.exists())
