from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0007_alter_workout_video_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='workout',
            name='instructions',
            field=models.JSONField(blank=True, default=list, help_text='List of step-by-step instruction strings'),
        ),
    ]
