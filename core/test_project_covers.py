from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import Project, ProjectCategory, ProjectCover
from core.authentication import issue_token

class ProjectCoverTests(TestCase):
    def setUp(self):
        self.client=APIClient()
        user=get_user_model().objects.create_user('cover-admin',is_staff=True)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+issue_token(user))
        category=ProjectCategory.objects.create(name='Design')
        self.project=Project.objects.create(title='Cover',category=category,type='image',cover_image='legacy.webp')
        self.a=ProjectCover.objects.create(project=self.project,image='a.webp',position=0)
        self.b=ProjectCover.objects.create(project=self.project,image='b.webp',position=1)
        self.url=f'/api/portfolio/projects/{self.project.id}/'
    def test_order_remove_and_legacy_preserved(self):
        response=self.client.patch(self.url,{'keep_cover_ids':[self.b.id,self.a.id]},format='json')
        self.assertEqual(response.status_code,200)
        self.assertEqual([item['id'] for item in response.data['covers']],[self.b.id,self.a.id])
        self.client.patch(self.url,{'keep_cover_ids':[self.a.id]},format='json')
        self.assertEqual(list(self.project.covers.values_list('id',flat=True)),[self.a.id])
        self.project.refresh_from_db();self.assertEqual(self.project.cover_image.name,'legacy.webp')
    def test_invalid_ids_duplicates_and_limits_do_not_mutate(self):
        for keep in [[999999],[self.a.id,self.a.id],[True]]:
            response=self.client.patch(self.url,{'title':'bad','keep_cover_ids':keep},format='json')
            self.assertEqual(response.status_code,400)
            self.project.refresh_from_db();self.assertNotEqual(self.project.title,'bad')
        response=self.client.patch(self.url,{'cover_images':['bad']*9},format='json')
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.project.covers.count(),2)
    def test_unauthorized_write(self):
        response=APIClient().patch(self.url,{'keep_cover_ids':[]},format='json')
        self.assertIn(response.status_code,[401,403]);self.assertEqual(self.project.covers.count(),2)
