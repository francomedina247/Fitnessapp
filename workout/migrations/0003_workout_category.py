from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0002_workout_video_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='workout',
            name='category',
            field=models.CharField(
                choices=[
                    ('cardio',      'Cardio'),
                    ('strength',    'Strength'),
                    ('flexibility', 'Flexibility'),
                    ('hiit',        'HIIT'),
                    ('sports',      'Sports'),
                    ('recovery',    'Recovery'),
                    ('other',       'Other'),
                ],
                default='other',
                max_length=20,
            ),
        ),
    ]
