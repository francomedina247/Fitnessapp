from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_user_is_verified'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='push_token',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
