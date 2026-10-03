from django.db import migrations, models

def number_devices(apps, schema_editor):
    Log = apps.get_model('core', 'VisitorLog')
    Device = apps.get_model('core', 'VisitorDevice')
    seen = set()
    for device_id in Log.objects.exclude(device_id=None).order_by('created_at', 'id').values_list('device_id', flat=True):
        if device_id not in seen:
            Device.objects.get_or_create(device_id=device_id)
            seen.add(device_id)

class Migration(migrations.Migration):
    dependencies = [('core', '0027_lifemoment')]
    operations = [
        migrations.CreateModel(name='VisitorDevice', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('device_id', models.UUIDField(unique=True))]),
        migrations.AddField(model_name='visitorlog', name='country_code', field=models.CharField(max_length=2, blank=True)),
        migrations.AddField(model_name='visitorlog', name='region', field=models.CharField(max_length=100, blank=True)),
        migrations.AddField(model_name='visitorlog', name='city', field=models.CharField(max_length=100, blank=True)),
        migrations.RunPython(number_devices, migrations.RunPython.noop),
    ]

