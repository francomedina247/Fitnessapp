from django.contrib import admin
from .models import Workout, Exercise, ProgressEntry, Measurement, PersonalRecord


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display  = ('name', 'difficulty', 'duration', 'calories_burned', 'video_url', 'created_by', 'created_at')
    list_filter   = ('difficulty',)
    search_fields = ('name', 'description')
    ordering      = ('name',)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display  = ('user', 'workout', 'date', 'duration', 'calories_burned')
    list_filter   = ('date',)
    search_fields = ('user__email', 'workout__name')
    ordering      = ('-date',)


@admin.register(ProgressEntry)
class ProgressEntryAdmin(admin.ModelAdmin):
    list_display  = ('user', 'date', 'weight', 'calories_burned', 'exercises_count')
    list_filter   = ('date',)
    search_fields = ('user__email',)
    ordering      = ('-date',)


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display  = ('user', 'date', 'chest', 'waist', 'hips', 'thighs', 'arms')
    list_filter   = ('date',)
    search_fields = ('user__email',)
    ordering      = ('-date',)


@admin.register(PersonalRecord)
class PersonalRecordAdmin(admin.ModelAdmin):
    list_display  = ('user', 'exercise', 'value', 'unit', 'date')
    list_filter   = ('unit',)
    search_fields = ('user__email', 'exercise')
    ordering      = ('-date',)
