from rest_framework import serializers
from .models import Workout, Exercise, ProgressEntry, Measurement, PersonalRecord


class WorkoutSerializer(serializers.ModelSerializer):
    video_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    round_video_uris = serializers.JSONField(required=False, default=list)
    step_images = serializers.JSONField(required=False, default=list)
    rounds = serializers.IntegerField(required=False, default=1)
    round_duration_seconds = serializers.IntegerField(required=False, default=30)
    duration = serializers.FloatField()
    calories_burned = serializers.FloatField()

    class Meta:
        model  = Workout
        fields = ('id', 'name', 'description', 'duration', 'calories_burned', 'difficulty', 'category', 'video_url', 'rounds', 'round_duration_seconds', 'round_video_uris', 'step_images', 'created_by', 'created_at')
        read_only_fields = ('id', 'created_at', 'created_by')

    def validate_video_url(self, value):
        if not value or str(value).strip() == '':
            return None
        return value

    def validate_category(self, value):
        valid = [c[0] for c in self.Meta.model.CATEGORY_CHOICES]
        if value not in valid:
            return 'other'
        return value


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
