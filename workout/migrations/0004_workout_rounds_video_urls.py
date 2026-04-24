from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0003_workout_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='workout',
            name='rounds',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='workout',
            name='round_duration_seconds',
            field=models.IntegerField(default=30),
        ),
        migrations.AddField(
            model_name='workout',
            name='round_video_uris',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
