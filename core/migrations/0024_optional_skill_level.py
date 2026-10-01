from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core', '0023_alter_projectimage_options_projectimage_position')]
    operations = [migrations.AlterField(model_name='skill', name='level', field=models.IntegerField(blank=True, default=None, null=True))]
