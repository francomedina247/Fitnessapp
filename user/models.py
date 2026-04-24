from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # ── Core auth fields ──────────────────────────────────────────────────────
    email       = models.EmailField(unique=True)
    username    = models.CharField(max_length=150, unique=True)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # ── Registration fields ───────────────────────────────────────────────────
    name         = models.CharField(max_length=150, blank=True, null=True)
    birthdate    = models.CharField(max_length=20, blank=True, null=True)
    is_verified  = models.BooleanField(default=False)
    push_token   = models.CharField(max_length=200, blank=True, null=True)

    # ── Profile / onboarding fields ───────────────────────────────────────────
    gender               = models.CharField(max_length=10, blank=True, null=True)
    height               = models.FloatField(blank=True, null=True)   # cm
    weight               = models.FloatField(blank=True, null=True)   # kg
    age                  = models.IntegerField(blank=True, null=True)
    goal_weight          = models.FloatField(blank=True, null=True)   # kg
    weight_unit          = models.CharField(max_length=5, default='kg')
    height_unit          = models.CharField(max_length=5, default='cm')
    primary_goal         = models.CharField(max_length=30, blank=True, null=True)
    weekly_workout_target= models.IntegerField(default=3)
    experience_level     = models.CharField(max_length=20, blank=True, null=True)
    bio                  = models.TextField(blank=True, null=True)
    body_fat             = models.FloatField(blank=True, null=True)
    resting_heart_rate   = models.IntegerField(blank=True, null=True)
    sleep_hours          = models.FloatField(blank=True, null=True)
    profile_completed    = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
