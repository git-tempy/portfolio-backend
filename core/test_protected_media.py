from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image
from django.core import signing
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from core.protected_media import SALT, protected_image_url
from core.uploads import RemoteImageField, RemoteFileField


class ProtectedMediaTests(SimpleTestCase):
    def setUp(self):
        context = override_settings(STORAGES={
            'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
            'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
        })
        context.enable(); self.addCleanup(context.disable)
        stream = BytesIO(); Image.new('RGBA', (30, 20), (20, 100, 200, 80)).save(stream, 'PNG')
        self.original = stream.getvalue()
        self.key = default_storage.save('uploads/1/test.png', ContentFile(self.original))
        self.url = protected_image_url(self.key)
        self.headers = {'HTTP_SEC_FETCH_SITE':'same-origin', 'HTTP_SEC_FETCH_DEST':'image'}

    def test_public_serializer_never_calls_storage_url(self):
        class File:
            name = self.key
            @property
            def url(self):
                raise AssertionError('Storage URL must never reach the browser')
        for field in (RemoteImageField(), RemoteFileField()):
            self.assertEqual(field.to_representation(File()), self.url)
            self.assertTrue(self.url.endswith('/preview.webp'))

    def test_image_request_is_webp_and_preserves_original(self):
        result = self.client.get(self.url, **self.headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result['Content-Type'], 'image/webp')
        self.assertNotIn('Location', result)
        self.assertEqual(default_storage.open(self.key).read(), self.original)
        with Image.open(BytesIO(result.content)) as image:
            self.assertEqual(image.format, 'WEBP')
            self.assertEqual(image.size, (30, 20))
            self.assertEqual(image.getpixel((0, 0))[3], 80)

    def test_open_in_new_tab_denied_even_after_image_load(self):
        self.assertEqual(self.client.get(self.url, **self.headers).status_code, 200)
        for site in ('same-origin', 'none'):
            result = self.client.get(self.url, HTTP_SEC_FETCH_SITE=site, HTTP_SEC_FETCH_DEST='document')
            self.assertEqual(result.status_code, 403)
            self.assertEqual(result['Cache-Control'], 'no-store')

    def test_missing_headers_and_hotlink_denied(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.get(self.url, HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_DEST='image').status_code, 403)

    def test_browser_cache_varies_by_request_context(self):
        result = self.client.get(self.url, **self.headers)
        for header in ('Sec-Fetch-Site', 'Sec-Fetch-Dest', 'Authorization'):
            self.assertIn(header, result['Vary'])
        self.assertEqual(result['Cross-Origin-Resource-Policy'], 'same-origin')
        self.assertEqual(result['X-Content-Type-Options'], 'nosniff')

    def test_legacy_derivative_cached_without_reencoding_every_request(self):
        from core.image_processing import web_image
        with patch('core.protected_media.web_image', wraps=web_image) as convert:
            for _ in range(2):
                self.assertEqual(self.client.get(self.url, **self.headers).status_code, 200)
            self.assertEqual(convert.call_count, 1)

    def test_admin_editor_fetch_requires_authenticated_staff(self):
        headers = {**self.headers, 'HTTP_SEC_FETCH_DEST':'empty'}
        self.assertEqual(self.client.get(self.url, **headers).status_code, 403)
        with patch('core.protected_media.AdminTokenAuthentication.authenticate',
                   return_value=(SimpleNamespace(is_staff=True), 'token')):
            self.assertEqual(self.client.get(self.url, **headers).status_code, 200)

    def test_bad_token_missing_file_and_private_paths_denied(self):
        self.assertEqual(self.client.get(reverse('protected_image', kwargs={'token':'invalid'}), **self.headers).status_code, 404)
        for key in ('private/originals/1/source.jpg', '../secret.png', '/etc/secret.png', 'https://example.com/a.png'):
            token = signing.Signer(salt=SALT).sign_object({'key':key})
            self.assertEqual(self.client.get(reverse('protected_image', kwargs={'token':token}), **self.headers).status_code, 404)
        self.assertEqual(self.client.get(protected_image_url('uploads/1/missing.png'), **self.headers).status_code, 404)

    def test_pdf_still_downloadable(self):
        value = SimpleNamespace(name='about/resume/cv.pdf', url='https://storage.example/cv.pdf')
        self.assertEqual(RemoteFileField().to_representation(value), value.url)

    def test_head_has_same_length_and_no_body(self):
        get = self.client.get(self.url, **self.headers)
        head = self.client.head(self.url, **self.headers)
        self.assertEqual(head.status_code, 200)
        self.assertEqual(head['Content-Length'], str(len(get.content)))
        self.assertEqual(head.content, b'')
