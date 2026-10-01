from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
from django.core import signing
from django.test import SimpleTestCase
from rest_framework.exceptions import ParseError, ValidationError
from core.uploads import UploadJSONParser, UPLOAD_SALT, RemoteFileField, VerifiedStorageKey

class UploadTests(SimpleTestCase):
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
        key = self.parse(receipt)['image']
        self.assertIsInstance(key, VerifiedStorageKey)
        self.assertEqual(RemoteFileField().to_internal_value(key), 'uploads/1/test.webp')
        with self.assertRaises(ValidationError):
            RemoteFileField().to_internal_value(str(key))
