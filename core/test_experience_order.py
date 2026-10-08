from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import Experience
from core.authentication import issue_token
class ExperienceOrderTests(TestCase):
 def setUp(self):
  self.client=APIClient();user=get_user_model().objects.create_user('order-admin',is_staff=True);self.client.credentials(HTTP_AUTHORIZATION='Bearer '+issue_token(user));self.rows=[Experience.objects.create(role=str(i),company='Studio',period='2024',desc='Work',position=i) for i in range(3)]
 def test_order_public_and_append(self):
  ids=[x.id for x in reversed(self.rows)];r=self.client.post('/api/experiences/order/',{'ids':ids},format='json');self.assertEqual(r.status_code,200)
  for language in ['uz','ru','en','jp']:self.assertEqual([x['id'] for x in APIClient().get('/api/experiences/?lang='+language).data],ids)
  r=self.client.post('/api/experiences/',{'role':'New','company':'Studio','period':'2025','desc':'Work'},format='json');self.assertEqual(r.status_code,201);self.assertEqual(Experience.objects.last().id,r.data['id'])
 def test_invalid_atomic_and_permission(self):
  ids=[x.id for x in self.rows]
  for bad in [ids[:2],[ids[0]]*3,[999]+ids[1:],[True]+ids[1:]]:
   r=self.client.post('/api/experiences/order/',{'ids':bad},format='json');self.assertEqual(r.status_code,400);self.assertEqual(list(Experience.objects.values_list('id',flat=True)),ids)
  r=APIClient().post('/api/experiences/order/',{'ids':list(reversed(ids))},format='json');self.assertIn(r.status_code,[401,403]);self.assertEqual(list(Experience.objects.values_list('id',flat=True)),ids)
