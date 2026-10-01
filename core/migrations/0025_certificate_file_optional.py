from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core', '0024_optional_skill_level')]
    operations = [migrations.AlterField(model_name='certificate', name='file', field=models.FileField(blank=True, upload_to='certificates/'))]
