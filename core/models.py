from django.db import models

class AboutMe(models.Model):
    name = models.CharField(max_length=255, default="")
    bio = models.TextField(default="")
    image = models.ImageField(upload_to='about/', null=True, blank=True)
    resume_pdf = models.FileField(upload_to='about/resume/', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "About Me"
        verbose_name_plural = "About Me"

class Certificate(models.Model):
    title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    year = models.CharField(max_length=4, blank=True)
    file = models.FileField(upload_to='certificates/', blank=True)
    image = models.ImageField(upload_to='certificates/covers/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.year})"

class Skill(models.Model):
    TYPE_CHOICES = [
        ('Software', 'Software'),
        ('Personal', 'Personal'),
    ]
    name = models.CharField(max_length=255)
    level = models.IntegerField(null=True, blank=True, default=None)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Software')
    image = models.ImageField(upload_to='skills/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

class Trait(models.Model):
    TYPE_CHOICES = [
        ('Strength', 'Strength'),
        ('Weakness', 'Weakness'),
    ]
    text = models.CharField(max_length=500)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Strength')

    def __str__(self):
        return f"{self.text[:30]} ({self.type})"

class Experience(models.Model):
    role = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    period = models.CharField(max_length=100)
    desc = models.TextField()
    logo = models.ImageField(upload_to='experiences/logos/', null=True, blank=True)

    def __str__(self):
        return f"{self.role} at {self.company}"

class ProjectCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default="Active")

    def __str__(self):
        return self.name

from django.utils.text import slugify

class Project(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    category = models.ForeignKey(ProjectCategory, on_delete=models.CASCADE, related_name='projects')
    type = models.CharField(max_length=50) # 'pdf' or 'image'
    file = models.FileField(upload_to='projects/files/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='projects/covers/', null=True, blank=True)
    description = models.TextField(blank=True)
    main_hashtag = models.CharField(max_length=100, blank=True)
    regular_hashtags = models.CharField(max_length=500, blank=True)
    total_pages = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            if not base_slug:
                base_slug = "project"
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        previous_file = type(self).objects.filter(pk=self.pk).values_list('file', flat=True).first() if self.pk else None
        if self.file and self.type == 'pdf' and previous_file != self.file.name:
            from pypdf import PdfReader
            self.file.open('rb')
            try:
                self.total_pages = len(PdfReader(self.file).pages)
            finally:
                if self.file._committed:
                    self.file.close()
                else:
                    self.file.seek(0)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    company = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=20, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.company or 'No Company'}"

class VisitorDevice(models.Model):
    device_id = models.UUIDField(unique=True)

class VisitorLog(models.Model):
    device_id = models.UUIDField(null=True, blank=True, db_index=True)
    device_type = models.CharField(max_length=10, default='unknown', choices=[('mobile','Mobile'),('tablet','Tablet'),('desktop','Desktop'),('unknown','Unknown')])
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visitor from {self.ip_address or 'Unknown'} at {self.created_at}"

class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/images/')
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']

    def __str__(self):
        return f"Image for {self.project.title}"


class Education(models.Model):
    logo = models.ImageField(upload_to='education/logos/', null=True, blank=True)
    name = models.CharField(max_length=255)
    period = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class ResumeDownloadLog(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    purpose = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email}) at {self.created_at}"






class RequestLimit(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    window = models.BigIntegerField(default=0)
    count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

class LifeMoment(models.Model):
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    date = models.DateField()
    image = models.ImageField(upload_to='life/', null=True, blank=True)
    is_sample = models.BooleanField(default=False)
    class Meta:
        ordering = ['-date', '-id']
    def __str__(self):
        return self.title

