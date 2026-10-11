from django.test import TestCase
from rest_framework.test import APIClient
from core.models import Education


class EducationOrderTests(TestCase):
    def test_public_order_is_stable_after_description_updates_in_all_languages(self):
        rows = [Education.objects.create(name=name, period='Unchanged', description='Original', links=[])
                for name in ['Japan Digital University', 'Jahon tillari', 'Kyoto Tachibana']]
        for row in reversed(rows):
            row.description = 'Updated description'
            row.save(update_fields=['description'])
        for language in ['uz', 'ru', 'en', 'jp']:
            response = APIClient().get('/api/education/?lang=' + language)
            self.assertEqual(response.status_code, 200)
            self.assertEqual([item['id'] for item in response.data], [row.id for row in rows])
        self.assertEqual(list(Education.objects.order_by('id').values_list('period', flat=True)), ['Unchanged'] * 3)
