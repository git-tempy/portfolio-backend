from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core', '0036_alter_experience_options_experience_position')]
    operations = [migrations.AddField(model_name='aboutme', name='resume_pdf_' + language,
        field=models.FileField(blank=True, null=True, upload_to='about/resume/' + language + '/'))
        for language in ['uz', 'ru', 'en', 'jp']]
