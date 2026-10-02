import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.authentication import issue_token
from core.models import VisitorLog, Skill, Experience, Education, Certificate, Project, ProjectCategory

class DeviceMediaTests(TestCase):
    def setUp(self):
        self.public=APIClient();self.admin=APIClient()
        user=get_user_model().objects.create_user('device-test',password='test-only',is_staff=True)
        self.admin.credentials(HTTP_AUTHORIZATION='Bearer '+issue_token(user))

    def test_returning_device_keeps_identity_and_counts_visits(self):
        device=str(uuid.uuid4())
        payload={'device_id':device,'device_type':'mobile'}
        self.assertEqual(self.public.post('/api/visitor/log/',payload,format='json').status_code,201)
        self.assertEqual(self.public.post('/api/visitor/log/',payload,format='json').status_code,200)
        VisitorLog.objects.update(created_at=timezone.now()-timedelta(minutes=2))
        self.assertEqual(self.public.post('/api/visitor/log/',payload,format='json').status_code,201)
        stats=self.admin.get('/api/dashboard/stats/').json()
        self.assertEqual(stats['visitor_devices'][0]['device_id'],device)
        self.assertEqual(stats['visitor_devices'][0]['visits'],2)
        self.assertEqual(stats['device_summary'],[{'device_type':'mobile','count':1}])
        self.assertIn(self.public.get('/api/dashboard/stats/').status_code,(401,403))

    def test_two_devices_behind_same_ip_are_distinct(self):
        for kind in ('desktop','tablet'):
            self.assertEqual(self.public.post('/api/visitor/log/',{'device_id':str(uuid.uuid4()),'device_type':kind},format='json',REMOTE_ADDR='203.0.113.8').status_code,201)
        self.assertEqual(VisitorLog.objects.count(),2)
        for payload in ({'device_id':'bad','device_type':'desktop'},{'device_id':str(uuid.uuid4()),'device_type':'invalid'}):
            self.assertEqual(self.public.post('/api/visitor/log/',payload,format='json').status_code,400)

    def test_optional_images_can_be_removed_without_deleting_records(self):
        category=ProjectCategory.objects.create(name='test')
        rows=[(Skill.objects.create(name='Figma',type='Software',image='old.webp'),'/api/skills/','image'),
              (Experience.objects.create(role='Designer',company='Test',logo='old.webp'),'/api/experiences/','logo'),
              (Education.objects.create(name='Test',logo='old.webp'),'/api/education/','logo'),
              (Certificate.objects.create(title='Test',image='old.webp'),'/api/certificates/','image'),
              (Project.objects.create(title='Test',category=category,type='image',cover_image='old.webp'),'/api/portfolio/projects/','cover_image')]
        for obj,path,field in rows:
            with self.subTest(path=path):
                response=self.admin.patch(f'{path}{obj.id}/',{field:None},format='json')
                self.assertEqual(response.status_code,200,response.data)
                obj.refresh_from_db();self.assertFalse(getattr(obj,field))
