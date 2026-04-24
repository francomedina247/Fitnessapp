from rest_framework import serializers
from .models import Workout, Exercise, ProgressEntry, Measurement, PersonalRecord


class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Workout
        fields = ('id', 'name', 'description', 'duration', 'calories_burned', 'difficulty', 'category', 'video_url', 'rounds', 'round_duration_seconds', 'round_video_uris', 'created_by', 'created_at')
        read_only_fields = ('id', 'created_at', 'created_by')


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Exercise
        fields = ('id', 'user', 'workout', 'date', 'duration', 'calories_burned', 'notes', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProgressEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProgressEntry
        fields = ('id', 'user', 'date', 'weight', 'calories_burned', 'exercises_count', 'notes', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Measurement
        fields = ('id', 'user', 'date', 'chest', 'waist', 'hips', 'thighs', 'arms', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class PersonalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PersonalRecord
        fields = ('id', 'user', 'exercise', 'value', 'unit', 'date', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
