from django.contrib.auth import get_user_model
from rest_framework import serializers
import re

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'name', 'birthdate')

    def _generate_username(self, name, email):
        base = (name or email.split('@')[0])
        base = base.lower().strip()
        base = re.sub(r'\s+', '_', base)
        base = re.sub(r'[^a-z0-9_]', '', base) or 'user'
        username = base
        n = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{n}'
            n += 1
        return username

    def create(self, validated_data):
        if not validated_data.get('username'):
            validated_data['username'] = self._generate_username(
                validated_data.get('name', ''),
                validated_data['email'],
            )
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'name', 'birthdate',
            'is_staff', 'is_verified', 'date_joined',
        )
        read_only_fields = ('id', 'email', 'is_staff', 'is_verified', 'date_joined')


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'name', 'birthdate',
            'gender', 'height', 'weight', 'age',
            'goal_weight', 'weight_unit', 'height_unit',
            'primary_goal', 'weekly_workout_target',
            'experience_level', 'bio',
            'body_fat', 'resting_heart_rate', 'sleep_hours',
            'profile_completed', 'is_verified', 'is_staff', 'date_joined',
        )
        read_only_fields = ('id', 'email', 'is_staff', 'is_verified', 'date_joined')

    def update(self, instance, validated_data):
        if any(f in validated_data for f in ('height', 'weight', 'age', 'gender')):
            validated_data['profile_completed'] = True
        return super().update(instance, validated_data)
