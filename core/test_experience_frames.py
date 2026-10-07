from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import Experience, ExperienceFrame
from core.authentication import issue_token
from unittest.mock import patch

class ExperienceFrameTests(TestCase):
    def setUp(self):
        self.client=APIClient()
        user=get_user_model().objects.create_user('frame-admin',is_staff=True)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+issue_token(user))
        self.job=Experience.objects.create(role='Designer',company='Studio',period='2024',desc='Work')
        self.a=ExperienceFrame.objects.create(experience=self.job,image='a.png',position=0)
        self.b=ExperienceFrame.objects.create(experience=self.job,image='b.png',position=1)
        self.url=f'/api/experiences/{self.job.id}/'
    def test_order_remove_and_speed(self):
        r=self.client.patch(self.url,{'keep_frame_ids':[self.b.id,self.a.id],'animation_order':[{'id':self.b.id},{'id':self.a.id}],'animation_interval':150},format='json')
        self.assertEqual(r.status_code,200)
        self.assertEqual([f['id'] for f in r.data['animation_frames']],[self.b.id,self.a.id])
        self.assertEqual(r.data['animation_interval'],150)
        r=self.client.patch(self.url,{'keep_frame_ids':[],'animation_order':[]},format='json')
        self.assertEqual(r.status_code,200);self.assertEqual(self.job.animation_frames.count(),0)
    def test_invalid_order_ownership_and_speed_atomic(self):
        for data in [{'keep_frame_ids':[999]}, {'keep_frame_ids':[True]}, {'keep_frame_ids':[self.a.id],'animation_order':[{'new':0}]}, {'animation_interval':49}, {'animation_interval':5001}]:
            r=self.client.patch(self.url,dict(data,company='Bad'),format='json')
            self.assertEqual(r.status_code,400);self.job.refresh_from_db();self.assertEqual(self.job.company,'Studio')
        self.assertEqual(self.job.animation_frames.count(),2)
    def test_unlimited_frames_and_new_order(self):
        with patch('core.views.RemoteImageField.to_internal_value',side_effect=lambda value:value):
            r=self.client.patch(self.url,{'keep_frame_ids':[],'animation_files':[f'{i}.png' for i in range(12)],'animation_order':[{'new':i} for i in reversed(range(12))]},format='json')
        self.assertEqual(r.status_code,200);self.assertEqual(self.job.animation_frames.count(),12)
        self.assertEqual(self.job.animation_frames.first().image.name,'11.png')
    def test_legacy_default_and_unauthorized(self):
        legacy=Experience.objects.create(role='Old',company='Legacy',period='2020',desc='Old')
        r=APIClient().get('/api/experiences/')
        row=next(x for x in r.data if x['id']==legacy.id)
        self.assertEqual(row['animation_frames'],[]);self.assertEqual(row['animation_interval'],700)
        r=APIClient().patch(self.url,{'keep_frame_ids':[]},format='json')
        self.assertIn(r.status_code,[401,403]);self.assertEqual(self.job.animation_frames.count(),2)
