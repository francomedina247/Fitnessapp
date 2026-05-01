from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0008_workout_instructions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workout',
            name='step_images',
        ),
    ]
