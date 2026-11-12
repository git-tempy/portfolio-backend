from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
from django.core import signing
from django.test import SimpleTestCase
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate
from core.uploads import UploadJSONParser, UPLOAD_SALT, RemoteFileField, VerifiedStorageKey, upload_url

class UploadTests(SimpleTestCase):
    @patch('core.uploads.default_storage')
    def test_direct_image_uses_private_staging_prefix(self, storage):
        storage.bucket_name = 'media'
        user = SimpleNamespace(pk=1, is_staff=True, is_authenticated=True)
        request = APIRequestFactory().post('/upload-url/', {'content_type':'image/png', 'size':100}, format='json')
        force_authenticate(request, user=user)
        response = upload_url(request)
        self.assertEqual(response.status_code, 200)
        receipt = signing.loads(response.data['receipt'], salt=UPLOAD_SALT)
        self.assertTrue(receipt['key'].startswith('private/originals/1/'))

    @patch('core.uploads.default_storage')
    def test_jpeg_original_is_not_exposed_as_public_image(self, storage):
        from PIL import Image
        data = BytesIO(); Image.new('RGB', (20, 30)).save(data, 'JPEG')
        content = data.getvalue()
        source = 'private/originals/1/source.jpg'
        receipt = signing.dumps({'key':source, 'user':1, 'size':len(content), 'type':'image/jpeg'}, salt=UPLOAD_SALT)
        storage.connection.meta.client.head_object.return_value={'ContentLength':len(content), 'ContentType':'image/jpeg'}
        storage.connection.meta.client.get_object.return_value={'Body':BytesIO(content)}
        storage.save.return_value='uploads/1/display.webp'
        self.assertEqual(self.parse(receipt)['image'], 'uploads/1/display.webp')
        with Image.open(storage.save.call_args.args[1]) as preview:
            self.assertEqual(preview.format, 'WEBP')
        storage.delete.assert_not_called()

    def parse(self, receipt, user=1):
        import json
        stream = BytesIO(json.dumps({'image': {'upload': receipt}}).encode())
        return UploadJSONParser().parse(stream, parser_context={'request': SimpleNamespace(user=SimpleNamespace(pk=user))})

    def receipt(self):
        return signing.dumps({'key': 'uploads/1/test.webp', 'user': 1, 'size': 100, 'type': 'image/webp'}, salt=UPLOAD_SALT)

    def test_invalid_receipt(self):
        with self.assertRaises(ParseError):
            self.parse('invalid')

    def test_owner_validation(self):
        with self.assertRaises(ParseError):
            self.parse(self.receipt(), user=2)

    @patch('core.uploads.default_storage')
    def test_metadata_validation(self, storage):
        storage.connection.meta.client.head_object.return_value = {'ContentLength': 99, 'ContentType': 'image/webp'}
        with self.assertRaises(ParseError):
            self.parse(self.receipt())

    @patch('core.uploads.default_storage')
    def test_verified_upload(self, storage):
        storage.connection.meta.client.head_object.return_value = {'ContentLength': 100, 'ContentType': 'image/webp'}
        from PIL import Image
        image=BytesIO();Image.new('RGB',(10,10)).save(image,'WEBP');content=image.getvalue()
        receipt=signing.dumps({'key':'uploads/1/test.webp','user':1,'size':len(content),'type':'image/webp'},salt=UPLOAD_SALT)
        storage.connection.meta.client.head_object.return_value={'ContentLength':len(content),'ContentType':'image/webp'}
        storage.connection.meta.client.get_object.return_value={'Body':BytesIO(content)}
        storage.save.return_value='uploads/1/preview.webp'
        key = self.parse(receipt)['image']
        self.assertIsInstance(key, VerifiedStorageKey)
        self.assertEqual(RemoteFileField().to_internal_value(key), 'uploads/1/preview.webp')
        self.assertTrue(storage.save.call_args.args[0].endswith('.webp'))
        self.assertEqual(storage.save.call_args.args[1].read(), content)
        with self.assertRaises(ValidationError):
            RemoteFileField().to_internal_value(str(key))
