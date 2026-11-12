from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from core.image_processing import web_image
from core.uploads import RemoteFileField, RemoteImageField


class WebImageTests(SimpleTestCase):
    def image(self, fmt='PNG', mode='RGB', size=(30, 20), **options):
        data = BytesIO()
        Image.new(mode, size).save(data, fmt, **options)
        return data.getvalue()

    def test_multipart_image_and_generic_file_are_webp(self):
        for field in (RemoteImageField(), RemoteFileField()):
            for fmt, ext, mime in [('PNG', 'png', 'image/png'), ('JPEG', 'jpg', 'image/jpeg')]:
                result = field.run_validation(SimpleUploadedFile('design.' + ext, self.image(fmt), content_type=mime))
                self.assertTrue(result.name.endswith('.webp'))
                with Image.open(result) as image:
                    self.assertEqual(image.format, 'WEBP')

    def test_transparency_preserved(self):
        result = web_image(self.image(mode='RGBA'), 'alpha.png')
        with Image.open(result) as image:
            self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_pdf_document_bytes_unchanged(self):
        from pypdf import PdfWriter
        writer = PdfWriter(); writer.add_blank_page(width=100, height=100)
        data = BytesIO(); writer.write(data)
        file = SimpleUploadedFile('resume.pdf', data.getvalue(), content_type='application/pdf')
        result = RemoteFileField().run_validation(file)
        self.assertEqual(result.name, 'resume.pdf')
        self.assertEqual(result.read(), data.getvalue())

    def test_long_case_study_keeps_readable_width_and_aspect_ratio(self):
        result = web_image(self.image(size=(1000, 7000)), 'case.png')
        with Image.open(result) as image:
            self.assertEqual(image.size, (1000, 7000))

    def test_oversized_width_reduced(self):
        result = web_image(self.image(size=(4000, 1000)), 'wide.png')
        with Image.open(result) as image:
            self.assertEqual(image.size, (2560, 640))

    def test_rotation_baked_and_exif_stripped(self):
        exif = Image.Exif(); exif[274] = 6
        result = web_image(self.image('JPEG', size=(20, 30), exif=exif), 'rotated.jpg')
        with Image.open(result) as image:
            self.assertEqual(image.size, (30, 20))
            self.assertFalse(image.getexif())

    def test_existing_webp_not_encoded_twice(self):
        content = self.image('WEBP')
        self.assertEqual(web_image(content, 'ready.webp').read(), content)

    def test_invalid_or_animated_image_rejected(self):
        with self.assertRaises(ValidationError):
            web_image(b'not an image', 'fake.png')
        data = BytesIO()
        Image.new('RGB', (10, 10), 'red').save(data, 'WEBP', save_all=True,
              append_images=[Image.new('RGB', (10, 10), 'blue')], duration=100, loop=0)
        with self.assertRaises(ValidationError):
            web_image(data.getvalue(), 'animated.webp')
