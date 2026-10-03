from django.db import migrations, models

def exclude_owner_devices(apps, schema_editor):
    # The owner identified these permanent device numbers in the admin screenshot.
    apps.get_model('core', 'VisitorDevice').objects.filter(id__in=[2, 4]).update(excluded_from_analytics=True)

class Migration(migrations.Migration):
    dependencies = [('core', '0028_visitor_locations_and_device_numbers')]
    operations = [
        migrations.AddField(model_name='visitordevice', name='excluded_from_analytics', field=models.BooleanField(default=False)),
        migrations.RunPython(exclude_owner_devices, migrations.RunPython.noop),
    ]

