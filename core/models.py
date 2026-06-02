from django.db import models

class AboutMe(models.Model):
    name = models.CharField(max_length=255, default="Feruzxon Muxtarov")
    bio = models.TextField(default="Men Feruzxon Muxtarov — Toshkentda yashovchi ijodkor dizayner va art direktor. 5 yildan ortiq vaqt davomida brendlar uchun vizual identitet, raqamli mahsulotlar va marketing materiallarini yarataman. Maqsadim — har bir loyihaga estetika, ma'no va aniqlik kiritish.")
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
    file = models.FileField(upload_to='certificates/')
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
    level = models.IntegerField(default=90)
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

        if self.file and self.type == 'pdf':
            try:
                self.file.seek(0)
                content = self.file.read()
                self.file.seek(0)
                import re
                matches = re.findall(b'/Type\s*/Page\b', content)
                if matches:
                    self.total_pages = len(matches)
                else:
                    count_matches = re.findall(b'/Count\s*(\d+)', content)
                    if count_matches:
                        self.total_pages = max(int(m) for m in count_matches)
            except Exception as e:
                pass

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

class VisitorLog(models.Model):
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visitor from {self.ip_address or 'Unknown'} at {self.created_at}"

class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/images/')

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





