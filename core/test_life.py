from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import LifeMoment

class LifeTests(TestCase):
    def test_public_read_admin_crud_and_translations(self):
        client=APIClient()
        data={'title':'Namuna','title_uz':'Namuna','title_en':'Sample','title_ru':'Пример','title_jp':'サンプル','date':'2024-06-01','description_uz':'Tavsif','is_sample':True}
        self.assertEqual(client.post('/api/life/',data,format='json').status_code,401)
        admin=get_user_model().objects.create_user('life-admin',is_staff=True)
        client.force_authenticate(admin)
        created=client.post('/api/life/',data,format='json')
        self.assertEqual(created.status_code,201)
        pk=created.data['id']
        self.assertEqual(client.patch(f'/api/life/{pk}/',{'title_uz':'Yangi'},format='json').status_code,200)
        self.assertEqual(client.patch(f'/api/life/{pk}/',{'date':'bad'},format='json').status_code,400)
        client.force_authenticate(None)
        self.assertEqual(client.get('/api/life/').data[0]['title_en'],'Sample')
        self.assertIn(client.delete(f'/api/life/{pk}/').status_code,[401,403])
        client.force_authenticate(admin)
        self.assertEqual(client.delete(f'/api/life/{pk}/').status_code,204)
        self.assertEqual(LifeMoment.objects.count(),0)
