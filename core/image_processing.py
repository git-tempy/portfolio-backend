"""Public image derivatives. Source bytes never become the public image key."""
from io import BytesIO
from pathlib import PurePosixPath
import math

from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError

MAX_WIDTH = 2560
MAX_EDGE = 20000
MAX_PIXELS = 16_000_000


def web_image(content, name):
    """Keep UI case-study text readable; preserve alpha and bake EXIF rotation."""
    try:
        with Image.open(BytesIO(content)) as source:
            if source.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValueError('Unsupported image')
            if source.width * source.height > MAX_PIXELS:
                raise ValueError('Image pixel limit')
            if getattr(source, 'n_frames', 1) != 1:
                raise ValueError('Animated images are not supported')
            source.load()
            image = ImageOps.exif_transpose(source)
            scale = min(1, MAX_WIDTH / image.width, MAX_EDGE / max(image.size),
                        math.sqrt(MAX_PIXELS / (image.width * image.height)))
            # Already optimized WebP: avoid another lossy encoding pass.
            if source.format == 'WEBP' and scale == 1 and not source.info.get('exif') and not source.info.get('xmp'):
                return ContentFile(content, name=PurePosixPath(name).stem + '.webp')
            image = image.convert('RGBA' if 'A' in image.getbands() or 'transparency' in image.info else 'RGB')
            if scale < 1:
                image = image.resize((max(1, round(image.width * scale)),
                                      max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format='WEBP', quality=88, method=4,
                       icc_profile=source.info.get('icc_profile'), exif=b'', xmp=b'')
            return ContentFile(output.getvalue(), name=PurePosixPath(name).stem + '.webp')
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValidationError('This image cannot be optimized. Use a static JPG, PNG or WebP within 16 megapixels.') from exc
