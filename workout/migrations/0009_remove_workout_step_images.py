from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0008_workout_instructions'),
    ]

    operations = [
        # Set a default first so the column is not null-constrained during removal.
        migrations.AlterField(
            model_name='workout',
            name='step_images',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RemoveField(
            model_name='workout',
            name='step_images',
        ),
    ]
