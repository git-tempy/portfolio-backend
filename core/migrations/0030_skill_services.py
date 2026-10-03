from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [('core','0029_exclude_owner_devices')]
    operations = [migrations.AlterField(model_name='skill',name='type',field=models.CharField(max_length=50,choices=[('Software','Software'),('Personal','Personal'),('Service','Service')],default='Software'))]

