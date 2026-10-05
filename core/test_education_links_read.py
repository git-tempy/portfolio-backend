from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.authentication import issue_token
from core.models import Education, ResumeDownloadLog
from core.serializers import EducationSerializer, ResumeDownloadLogSerializer


class EducationNavigationTests(TestCase):
    def test_admin_form_encoded_links_persist(self):
        import json
        item = Education.objects.create(name='University', period='2026')
        admin = get_user_model().objects.create_user('education-admin', is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + issue_token(admin))
        links = [{'kind': 'tag', 'value': 'noq', 'labels': {'uz': 'Diplom ishini ko‘rish'}}]
        response = client.patch(f'/api/education/{item.pk}/', {'links': json.dumps(links)}, format='multipart')
        self.assertEqual(response.status_code, 200, response.data)
        item.refresh_from_db()
        self.assertEqual(item.links, links)
        serializer = EducationSerializer(item, data={'links': json.dumps(links)}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save().links, links)

    def test_links_persist_on_partial_update_and_reject_unsafe_destinations(self):
        item = Education.objects.create(name='University', period='2026', description='Study')
        for kind, value in [('tag', '#noq'), ('url', 'https://university.example'), ('url', '/portfolio?tag=noq')]:
            links = [{'kind': kind, 'value': value, 'labels': {'uz': 'Diplom ishini ko‘rish'}}]
            serializer = EducationSerializer(item, data={'links': links}, partial=True)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            serializer.save()
            item.refresh_from_db()
            self.assertEqual(EducationSerializer(item).data['links'], links)
        for kind, value in [('url', 'javascript:alert(1)'), ('url', '//evil.example'), ('tag', 'noq other')]:
            serializer = EducationSerializer(item, data={'links': [{'kind': kind, 'value': value, 'labels': {'uz': 'Open'}}]}, partial=True)
            self.assertFalse(serializer.is_valid())

    def test_resume_read_state_requires_admin_and_survives_new_requests(self):
        log = ResumeDownloadLog.objects.create(name='Applicant', phone='123', purpose='Review')
        client = APIClient()
        url = f'/api/resume-downloads/{log.pk}/'
        self.assertIn(client.patch(url, {'is_read': True}, format='json').status_code, (401, 403))
        admin = get_user_model().objects.create_user('read-admin', is_staff=True)
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + issue_token(admin))
        self.assertFalse(client.get('/api/resume-downloads/').json()[0]['is_read'])
        self.assertEqual(client.patch(url, {'is_read': True}, format='json').status_code, 200)
        log.refresh_from_db()
        self.assertTrue(log.is_read)
        self.assertTrue(client.get('/api/resume-downloads/').json()[0]['is_read'])
        serializer = ResumeDownloadLogSerializer(data={'name': 'New', 'phone': '456', 'purpose': 'Review', 'is_read': True})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertFalse(serializer.save().is_read)
