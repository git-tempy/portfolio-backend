import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.authentication import issue_token
from core.models import VisitorLog, VisitorDevice, Skill, Experience, Education, Certificate, Project, ProjectCategory

class DeviceMediaTests(TestCase):
    def setUp(self):
        self.public=APIClient();self.admin=APIClient()
        user=get_user_model().objects.create_user('device-test',password='test-only',is_staff=True)
        self.admin.credentials(HTTP_AUTHORIZATION='Bearer '+issue_token(user))

    def test_owner_device_is_excluded_from_past_and_future_visits(self):
        device = str(uuid.uuid4())
        payload = {'device_id':device, 'device_type':'mobile'}
        self.public.post('/api/visitor/log/', payload, format='json')
        VisitorDevice.objects.filter(device_id=device).update(excluded_from_analytics=True)
        response = self.public.post('/api/visitor/log/', payload, format='json')
        self.assertTrue(response.json()['excluded'])
        self.assertEqual(VisitorLog.objects.count(), 1)
        stats = self.admin.get('/api/dashboard/stats/').json()
        self.assertEqual(stats['total_views'], 0)
        self.assertEqual(stats['visitor_entries'], [])
        self.assertEqual(stats['visitor_devices'], [])
        self.assertEqual(sum(row['count'] for row in stats['visitor_analytics']), 0)

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

    def test_device_numbers_ignore_repeat_visits_and_store_geo(self):
        first = {'device_id': str(uuid.uuid4()), 'device_type': 'mobile'}
        headers = {'HTTP_X_VERCEL_IP_COUNTRY': 'UZ', 'HTTP_X_VERCEL_IP_COUNTRY_REGION': 'TK', 'HTTP_X_VERCEL_IP_CITY': 'Tashkent'}
        self.assertEqual(self.public.post('/api/visitor/log/', first, format='json', **headers).status_code, 201)
        VisitorLog.objects.update(created_at=timezone.now()-timedelta(minutes=2))
        self.public.post('/api/visitor/log/', first, format='json', **headers)
        for _ in range(2):
            self.public.post('/api/visitor/log/', {'device_id':str(uuid.uuid4()),'device_type':'mobile'}, format='json', **headers)
        devices = self.admin.get('/api/dashboard/stats/').json()['visitor_devices']
        self.assertEqual(sorted(row['short_id'] for row in devices), [1, 2, 3])
        self.assertEqual(len(devices), 3)
        self.assertEqual(next(row for row in devices if row['device_id']==first['device_id'])['visits'], 2)
        self.assertTrue(all(row['country_code']=='UZ' and row['region']=='TK' and row['city']=='Tashkent' for row in devices))
        history = self.admin.get('/api/dashboard/stats/').json()['visitor_entries']
        self.assertEqual(len(history), 4)
        device_history = self.admin.get('/api/dashboard/stats/', {'visits_device':first['device_id']}).json()['visitor_entries']
        self.assertEqual(len(device_history), 2)
        self.assertEqual({row['short_id'] for row in device_history}, {1})
        self.assertEqual(self.admin.get('/api/dashboard/stats/', {'visits_device':'invalid'}).status_code, 400)
        for period, length in [('week',7), ('month',30), ('year',12)]:
            chart = self.admin.get('/api/dashboard/stats/', {'period':period}).json()['visitor_analytics']
            self.assertEqual(len(chart), length)
            self.assertEqual(sum(row['count'] for row in chart), 4)
            self.assertTrue(all(row['count']==sum(row['devices'].values()) for row in chart))

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

