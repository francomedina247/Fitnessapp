from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0004_workout_rounds_video_urls'),
    ]

    operations = [
        migrations.AddField(
            model_name='workout',
            name='step_images',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
