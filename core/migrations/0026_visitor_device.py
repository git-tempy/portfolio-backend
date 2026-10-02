from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core', '0025_certificate_file_optional')]
    operations = [
        migrations.AddField(model_name='visitorlog', name='device_id', field=models.UUIDField(blank=True, null=True, db_index=True)),
        migrations.AddField(model_name='visitorlog', name='device_type', field=models.CharField(max_length=10, default='unknown', choices=[('mobile','Mobile'),('tablet','Tablet'),('desktop','Desktop'),('unknown','Unknown')])),
    ]
