from django.db import models
from django.conf import settings


class Workout(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy',         'Easy'),
        ('intermediate', 'Intermediate'),
        ('difficult',    'Difficult'),
        ('hard',         'Hard'),
    ]
    CATEGORY_CHOICES = [
        ('cardio',      'Cardio'),
        ('strength',    'Strength'),
        ('flexibility', 'Flexibility'),
        ('hiit',        'HIIT'),
        ('sports',      'Sports'),
        ('recovery',    'Recovery'),
        ('other',       'Other'),
    ]
    name            = models.CharField(max_length=150)
    description     = models.TextField(blank=True)
    duration        = models.IntegerField(help_text='Minutes')
    calories_burned = models.IntegerField()
    difficulty      = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    category        = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    video_url            = models.URLField(blank=True, null=True)
    rounds               = models.IntegerField(default=1)
    round_duration_seconds = models.IntegerField(default=30)
    round_video_uris     = models.JSONField(default=list, blank=True)
    created_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_workouts')
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Exercise(models.Model):
    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exercises')
    workout         = models.ForeignKey(Workout, on_delete=models.SET_NULL, null=True, related_name='exercises')
    date            = models.DateField()
    duration        = models.IntegerField(help_text='Minutes')
    calories_burned = models.IntegerField()
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} — {self.workout} on {self.date}'


class ProgressEntry(models.Model):
    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress_entries')
    date            = models.DateField()
    weight          = models.FloatField(default=0)
    calories_burned = models.IntegerField(default=0)
    exercises_count = models.IntegerField(default=0)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} — {self.date}'


class Measurement(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='measurements')
    date       = models.DateField()
    chest      = models.FloatField(blank=True, null=True)
    waist      = models.FloatField(blank=True, null=True)
    hips       = models.FloatField(blank=True, null=True)
    thighs     = models.FloatField(blank=True, null=True)
    arms       = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} — {self.date}'


class PersonalRecord(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personal_records')
    exercise   = models.CharField(max_length=150)
    value      = models.FloatField()
    unit       = models.CharField(max_length=20)
    date       = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} — {self.exercise}: {self.value} {self.unit}'
