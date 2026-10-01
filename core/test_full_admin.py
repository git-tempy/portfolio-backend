from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import translation
from PIL import Image
from rest_framework.test import APIClient
from core.models import Project, ProjectImage, ProjectCategory, ContactMessage, AboutMe
from core.authentication import issue_token
from core.uploads import VerifiedStorageKey

class FullAdminTests(TestCase):
    def setUp(self):
        translation.activate('uz')
        self.addCleanup(translation.deactivate)
        self.media = TemporaryDirectory()
        self.storage = override_settings(MEDIA_ROOT=self.media.name)
        self.storage.enable()
        self.addCleanup(self.storage.disable)
        self.addCleanup(self.media.cleanup)
        self.admin = get_user_model().objects.create_user('full-test-admin',password='isolated-test-password',is_staff=True)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+issue_token(self.admin))
        self.public = APIClient()

    def pdf(self):
        from pypdf import PdfWriter
        writer=PdfWriter();writer.add_blank_page(width=100,height=100)
        stream=BytesIO();writer.write(stream);return stream.getvalue()

    def image(self,name='test.png'):
        stream=BytesIO(); Image.new('RGB',(40,30),'blue').save(stream,'PNG')
        return SimpleUploadedFile(name,stream.getvalue(),content_type='image/png')

    def test_login_staff_and_nonstaff(self):
        response=self.public.post('/api/login/',{'username':self.admin.username,'password':'isolated-test-password'},format='json')
        self.assertEqual(response.status_code,200)
        self.assertIn('token',response.data)
        get_user_model().objects.create_user('ordinary',password='test-password')
        self.assertEqual(self.public.post('/api/login/',{'username':'ordinary','password':'test-password'},format='json').status_code,403)

    def test_inactive_account(self):
        self.admin.is_active=False;self.admin.save()
        self.assertEqual(self.client.get('/api/dashboard/stats/').status_code,401)

    def test_all_admin_and_public_lists(self):
        for path in ['about','certificates','skills','traits','experiences','education','portfolio/categories','portfolio/projects']:
            with self.subTest(path=path):
                self.assertEqual(self.public.get('/api/'+path+'/').status_code,200)
        for path in ['messages','resume-downloads','dashboard/stats']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get('/api/'+path+'/').status_code,200)
                self.assertEqual(self.public.get('/api/'+path+'/').status_code,401)

    def test_public_cannot_change_content(self):
        for path in ['about','certificates','skills','traits','experiences','education','portfolio/categories','portfolio/projects','uploads/presign']:
            with self.subTest(path=path):
                self.assertEqual(self.public.post('/api/'+path+'/',{},format='json').status_code,401)

    def test_crud_text_sections(self):
        cases=[('skills',{'name':'Figma','level':80,'type':'Software'},'name'),('traits',{'text':'Careful','type':'Strength'},'text'),('experiences',{'role':'Designer','company':'Test company','period':'2024','desc':'Test description'},'role'),('education',{'name':'Test school','period':'2024','description':'Test education'},'name')]
        for path,payload,field in cases:
            with self.subTest(path=path):
                response=self.client.post('/api/'+path+'/',payload,format='json')
                self.assertEqual(response.status_code,201,response.data)
                pk=response.data['id']
                self.assertTrue(any(item['id']==pk for item in self.public.get('/api/'+path+'/').data))
                update=self.client.patch(f'/api/{path}/{pk}/',{field:'Updated'},format='json')
                self.assertEqual(update.status_code,200,update.data)
                self.assertEqual(update.data[field],'Updated')
                self.assertEqual(self.client.delete(f'/api/{path}/{pk}/').status_code,204)

    def test_profile_translations_and_image(self):
        response=self.client.post('/api/about/',{'name_uz':'Test UZ','name_ru':'Test RU','name_en':'Test EN','name_jp':'Test JP','bio_uz':'Bio','image':self.image()},format='multipart')
        self.assertEqual(response.status_code,200,response.data)
        public=self.public.get('/api/about/?lang=RU').data
        self.assertEqual(public['name_ru'],'Test RU')
        self.assertTrue(public['image'])

    def test_certificate_upload_update_delete(self):
        response=self.client.post('/api/certificates/',{'title':'Certificate','organization':'Test','year':'2026','file':SimpleUploadedFile('test.pdf',self.pdf(),content_type='application/pdf'),'image':self.image()},format='multipart')
        self.assertEqual(response.status_code,201,response.data)
        pk=response.data['id']
        self.assertEqual(self.client.patch(f'/api/certificates/{pk}/',{'title':'Updated'},format='json').status_code,200)
        self.assertEqual(self.client.delete(f'/api/certificates/{pk}/').status_code,204)

    def test_project_gallery_and_public_detail(self):
        category=ProjectCategory.objects.create(name='Design', name_uz='Design', name_ru='Design', name_en='Design', name_jp='Design')
        response=self.client.post('/api/portfolio/projects/',{'title':'Gallery','title_en':'Gallery','category':category.name,'type':'image','cover_image':self.image('cover.png'),'images':[self.image('one.png'),self.image('two.png')]},format='multipart')
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(len(response.data['images']),2)
        pk=response.data['id'];slug=response.data['slug']
        public=self.public.get(f'/api/portfolio/projects/{slug}/')
        self.assertEqual(public.status_code,200)
        self.assertEqual(len(public.data['images']),2)
        self.assertEqual(self.client.patch(f'/api/portfolio/projects/{pk}/',{'title':'Changed'},format='json').status_code,200)
        self.assertEqual(self.client.delete(f'/api/portfolio/projects/{pk}/').status_code,204)
        self.assertEqual(ProjectImage.objects.count(),0)

    def test_pdf_project(self):
        category=ProjectCategory.objects.create(name='PDF', name_uz='PDF', name_ru='PDF', name_en='PDF', name_jp='PDF')
        response=self.client.post('/api/portfolio/projects/',{'title':'PDF','category':category.name,'type':'pdf','file':SimpleUploadedFile('test.pdf',self.pdf(),content_type='application/pdf')},format='multipart')
        self.assertEqual(response.status_code,201,response.data)
        self.assertTrue(response.data['file'])

    def test_gallery_database_rollback(self):
        category=ProjectCategory.objects.create(name='Atomic', name_uz='Atomic', name_ru='Atomic', name_en='Atomic', name_jp='Atomic')
        with patch('core.views.RemoteImageField.run_validation',return_value='test.png'),patch('core.models.ProjectImage.objects.create',side_effect=RuntimeError('storage/database simulation')):
            with self.assertRaises(RuntimeError):
                self.client.post('/api/portfolio/projects/',{'title':'Atomic','category':category.name,'type':'image','images':['test']},format='json')
        self.assertEqual(Project.objects.count(),0)

    def test_gallery_limit(self):
        category=ProjectCategory.objects.create(name='Limit', name_uz='Limit', name_ru='Limit', name_en='Limit', name_jp='Limit')
        response=self.client.post('/api/portfolio/projects/',{'title':'Too many','category':category.name,'type':'image','images':['test']*31},format='json')
        self.assertEqual(response.status_code,400)
        self.assertEqual(Project.objects.count(),0)

    def test_invalid_image(self):
        response=self.client.post('/api/about/',{'image':SimpleUploadedFile('fake.png',b'not an image',content_type='image/png')},format='multipart')
        self.assertEqual(response.status_code,400)

    def test_skill_range(self):
        for value in [-1,101]:
            self.assertEqual(self.client.post('/api/skills/',{'name':'Test','level':value},format='json').status_code,400)

    def test_category_crud(self):
        response=self.client.post('/api/portfolio/categories/',{'name':'Test category'},format='json')
        self.assertEqual(response.status_code,201,response.data)
        pk=response.data['id']
        self.assertEqual(self.client.patch(f'/api/portfolio/categories/{pk}/',{'name':'Updated'},format='json').status_code,200)
        self.assertEqual(self.client.delete(f'/api/portfolio/categories/{pk}/').status_code,204)

    def test_contact_admin_status_and_delete(self):
        response=self.public.post('/api/contact/',{'name':'Test','email':'test@example.com','message':'Hello','status':'read'},format='json')
        self.assertEqual(response.status_code,201,response.data)
        message=ContactMessage.objects.get()
        self.assertEqual(message.status,'new')
        self.assertEqual(self.client.patch(f'/api/messages/{message.pk}/',{'status':'read'},format='json').status_code,200)
        self.assertEqual(self.client.delete(f'/api/messages/{message.pk}/').status_code,204)

    @patch('core.throttling.time.time', return_value=1800000000)
    def test_contact_rate_limit(self, clock):
        for _ in range(5):
            self.assertEqual(self.public.post('/api/contact/',{'name':'Test','email':'test@example.com','message':'Hello'},format='json').status_code,201)
        self.assertEqual(self.public.post('/api/contact/',{'name':'Test','email':'test@example.com','message':'Hello'},format='json').status_code,429)

    def test_resume_log_and_delete(self):
        response=self.public.post('/api/resume-downloads/',{'name':'Test','phone':'123','email':'test@example.com','purpose':'Test'},format='json')
        self.assertEqual(response.status_code,201,response.data)
        rows=self.client.get('/api/resume-downloads/').data
        self.assertEqual(len(rows),1)
        self.assertEqual(self.client.delete(f"/api/resume-downloads/{rows[0]['id']}/").status_code,204)

    def test_visitors_and_dashboard(self):
        self.assertEqual(self.public.post('/api/visitor/log/',{},format='json',REMOTE_ADDR='203.0.113.20').status_code,201)
        self.assertEqual(self.public.post('/api/visitor/log/',{},format='json',REMOTE_ADDR='203.0.113.20').status_code,200)
        stats=self.client.get('/api/dashboard/stats/').data
        self.assertEqual(stats['total_views'],1)
        self.assertEqual(len(stats['visitor_analytics']),7)

    def test_missing_details(self):
        for path in ['skills','traits','education','experiences','certificates','portfolio/categories','portfolio/projects','messages','resume-downloads']:
            with self.subTest(path=path):
                self.assertEqual(self.client.delete('/api/'+path+'/999999/').status_code,404)

    def test_known_defect_invalid_pdf_rejected(self):
        category=ProjectCategory.objects.create(name='PDF',name_uz='PDF',name_en='PDF',name_ru='PDF',name_jp='PDF')
        response=self.client.post('/api/portfolio/projects/',{'title':'Fake PDF','category':'PDF','type':'pdf','file':SimpleUploadedFile('fake.pdf',b'This is plain text',content_type='application/pdf')},format='multipart')
        self.assertEqual(response.status_code,400)

    def test_known_defect_invalid_project_type_rejected(self):
        category=ProjectCategory.objects.create(name='Type',name_uz='Type',name_en='Type',name_ru='Type',name_jp='Type')
        response=self.client.post('/api/portfolio/projects/',{'title':'Invalid','category':'Type','type':'unsupported'},format='json')
        self.assertEqual(response.status_code,400)

    def test_known_defect_gallery_patch(self):
        category=ProjectCategory.objects.create(name='Gallery',name_uz='Gallery',name_en='Gallery',name_ru='Gallery',name_jp='Gallery')
        project=Project.objects.create(title='Gallery',category=category,type='image')
        ProjectImage.objects.create(project=project,image='test.png')
        response=self.client.patch(f'/api/portfolio/projects/{project.pk}/',{'images':[]},format='json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(project.images.count(),0)

    def test_known_defect_category_reference_survives_locale_change(self):
        category=ProjectCategory.objects.create(name='Design',name_uz='Dizayn',name_en='Design',name_ru='Дизайн',name_jp='Design')
        response=self.client.post('/api/portfolio/projects/?lang=RU',{'title':'Test','category':'Design','type':'image'},format='json')
        self.assertEqual(response.status_code,201)

    def test_gallery_keep_order_and_append(self):
        category=ProjectCategory.objects.create(name='Order',name_en='Order')
        project=Project.objects.create(title='Order',category=category,type='image')
        first=ProjectImage.objects.create(project=project,image='one.png',position=0)
        second=ProjectImage.objects.create(project=project,image='two.png',position=1)
        response=self.client.patch(f'/api/portfolio/projects/{project.pk}/',{'keep_image_ids':[second.pk,first.pk]},format='json')
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual([image['id'] for image in response.data['images']],[second.pk,first.pk])

    def test_gallery_rejects_other_project_image(self):
        category=ProjectCategory.objects.create(name='Owner',name_en='Owner')
        project=Project.objects.create(title='One',category=category,type='image')
        other=Project.objects.create(title='Two',category=category,type='image')
        image=ProjectImage.objects.create(project=other,image='test.png')
        response=self.client.patch(f'/api/portfolio/projects/{project.pk}/',{'keep_image_ids':[image.pk]},format='json')
        self.assertEqual(response.status_code,400)
        self.assertTrue(other.images.exists())
