"""Direct uploads keep large media out of the Vercel request body."""
import uuid
from django.core import signing
from django.core.files.storage import default_storage
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

UPLOAD_SALT = 'portfolio-upload-v1'
TYPES = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp', 'application/pdf': '.pdf'}

class VerifiedStorageKey(str):
    pass

@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_url(request):
    content_type = request.data.get('content_type')
    size = request.data.get('size')
    limit = 25 * 1024 * 1024 if content_type == 'application/pdf' else 40 * 1024 * 1024
    if content_type not in TYPES or not isinstance(size, int) or isinstance(size, bool) or not 0 < size <= limit:
        return Response({'error': 'Unsupported file type or size.'}, status=400)
    key = f'uploads/{request.user.pk}/{uuid.uuid4().hex}{TYPES[content_type]}'
    storage = default_storage
    if not hasattr(storage, 'bucket_name'):
        return Response({'error': 'Object storage is not configured.'}, status=503)
    url = storage.connection.meta.client.generate_presigned_url('put_object', Params={
        'Bucket': storage.bucket_name, 'Key': key, 'ContentType': content_type,
    }, ExpiresIn=600)
    receipt = signing.dumps({'key': key, 'size': size, 'type': content_type, 'user': request.user.pk}, salt=UPLOAD_SALT)
    return Response({'url': url, 'receipt': receipt})

class UploadJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        data = super().parse(stream, media_type, parser_context)
        user = parser_context['request'].user
        def resolve(value):
            if isinstance(value, dict) and set(value) == {'upload'}:
                try:
                    receipt = signing.loads(value['upload'], salt=UPLOAD_SALT, max_age=3600)
                    if receipt['user'] != user.pk:
                        raise ValueError('Upload owner mismatch')
                    head = default_storage.connection.meta.client.head_object(Bucket=default_storage.bucket_name, Key=receipt['key'])
                    if head['ContentLength'] != receipt['size'] or head['ContentType'] != receipt['type']:
                        raise ValueError('Upload metadata mismatch')
                    return VerifiedStorageKey(receipt['key'])
                except Exception as exc:
                    raise ParseError('Invalid or expired file upload.') from exc
            if isinstance(value, list):
                return [resolve(item) for item in value]
            if isinstance(value, dict):
                return {key: resolve(item) for key, item in value.items()}
            return value
        return resolve(data)

class RemoteFileField(serializers.FileField):
    def to_internal_value(self, data):
        if isinstance(data, VerifiedStorageKey):
            return str(data)
        return super().to_internal_value(data)

class RemoteImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, VerifiedStorageKey) and not data.endswith('.pdf'):
            return str(data)
        return super().to_internal_value(data)
