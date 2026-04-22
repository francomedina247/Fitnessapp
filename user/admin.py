from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model


User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('email', 'username', 'name', 'is_staff', 'is_active', 'is_verified', 'date_joined')
    list_filter   = ('is_staff', 'is_active', 'is_verified', 'profile_completed')
    search_fields = ('email', 'username', 'name')
    ordering      = ('-date_joined',)

    fieldsets = (
        ('Account',     {'fields': ('email', 'username', 'password')}),
        ('Personal',    {'fields': ('name', 'birthdate', 'gender', 'age')}),
        ('Body',        {'fields': ('height', 'weight', 'goal_weight', 'weight_unit', 'height_unit', 'body_fat')}),
        ('Fitness',     {'fields': ('primary_goal', 'weekly_workout_target', 'experience_level')}),
        ('Health',      {'fields': ('resting_heart_rate', 'sleep_hours', 'bio')}),
        ('Status',      {'fields': ('is_verified', 'profile_completed', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions'), 'classes': ('collapse',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'name', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )
