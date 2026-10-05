from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0032_update_device_exclusions')]
    operations = [
        migrations.AddField(model_name='education', name='links', field=models.JSONField(default=list, blank=True)),
        migrations.AddField(model_name='resumedownloadlog', name='is_read', field=models.BooleanField(default=False)),
    ]
