from django.db import migrations


def update_device_exclusions(apps, schema_editor):
    devices = apps.get_model('core', 'VisitorDevice').objects
    devices.filter(id__in=[1, 2]).update(excluded_from_analytics=True)
    devices.filter(id=4).update(excluded_from_analytics=False)


class Migration(migrations.Migration):
    dependencies = [('core', '0031_resumedownloadlog_telegram_visitordevice_nickname_and_more')]
    operations = [migrations.RunPython(update_device_exclusions, migrations.RunPython.noop)]
