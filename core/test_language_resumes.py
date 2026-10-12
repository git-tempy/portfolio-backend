from io import BytesIO
from tempfile import TemporaryDirectory
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from pypdf import PdfWriter
from core.authentication import issue_token
from core.models import AboutMe

class LanguageResumeTests(TestCase):
    def setUp(self):
        self.media=TemporaryDirectory();self.addCleanup(self.media.cleanup)
        self.settings_override=override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable();self.addCleanup(self.settings_override.disable)
        self.client=APIClient()
        user=get_user_model().objects.create_user('resume-admin',is_staff=True)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+issue_token(user))
        AboutMe.objects.create(id=1,resume_pdf='about/resume/legacy.pdf')
    def test_independent_uploads_preserve_legacy_and_other_languages(self):
        for language in ['uz','ru','en','jp']:
            writer=PdfWriter();writer.add_blank_page(width=100,height=100);stream=BytesIO();writer.write(stream)
            response=self.client.post('/api/about/',{'resume_pdf_'+language:SimpleUploadedFile(language+'.pdf',stream.getvalue(),content_type='application/pdf')},format='multipart')
            self.assertEqual(response.status_code,200)
        row=AboutMe.objects.get(id=1)
        self.assertEqual(row.resume_pdf.name,'about/resume/legacy.pdf')
        for language in ['uz','ru','en','jp']:
            self.assertTrue(getattr(row,'resume_pdf_'+language).name.endswith(language+'.pdf'))
            data=APIClient().get('/api/about/?lang='+language).data
            self.assertTrue(data['resume_pdf_'+language])
            self.assertTrue(data['resume_pdf'])
    def test_public_cannot_replace_cv(self):
        response=APIClient().post('/api/about/',{'resume_pdf_uz':None},format='json')
        self.assertIn(response.status_code,[401,403])
