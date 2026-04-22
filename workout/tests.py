import os
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Exercise, Measurement, PersonalRecord, ProgressEntry, Workout

User = get_user_model()

TEST_PASSWORD = os.environ.get('TEST_USER_PASSWORD', 'Test@Password#99!')


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(email='user@test.com', password=TEST_PASSWORD, is_staff=False):
    username = email.split('@')[0] + '_' + email.split('@')[1].split('.')[0]
    user = User.objects.create_user(email=email, password=password, username=username)
    user.is_verified = True
    user.is_staff = is_staff
    user.save(update_fields=['is_verified', 'is_staff'])
    return user


def auth_client(client, user):
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


def make_workout(admin):
    return Workout.objects.create(
        name='Running', description='Cardio', duration=30,
        calories_burned=300, difficulty='intermediate', created_by=admin,
    )


# ── Workout tests ─────────────────────────────────────────────────────────────

class WorkoutTests(APITestCase):

    def setUp(self):
        self.admin = make_user('admin@test.com', is_staff=True)
        self.user  = make_user('user@test.com')
        self.workout = make_workout(self.admin)

    def test_list_requires_auth(self):
        res = self.client.get(reverse('workout_list'))
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_authenticated(self):
        auth_client(self.client, self.user)
        res = self.client.get(reverse('workout_list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(data), 1)

    def test_create_requires_admin(self):
        auth_client(self.client, self.user)
        res = self.client.post(reverse('workout_create'), {
            'name': 'Yoga', 'duration': 45, 'calories_burned': 150, 'difficulty': 'easy',
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_as_admin(self):
        auth_client(self.client, self.admin)
        res = self.client.post(reverse('workout_create'), {
            'name': 'Yoga', 'duration': 45, 'calories_burned': 150, 'difficulty': 'easy',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Yoga')

    def test_update_as_admin(self):
        auth_client(self.client, self.admin)
        res = self.client.patch(
            reverse('workout_update', args=[self.workout.pk]),
            {'name': 'Sprint'},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Sprint')

    def test_delete_as_admin(self):
        auth_client(self.client, self.admin)
        res = self.client.delete(reverse('workout_delete', args=[self.workout.pk]))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Workout.objects.filter(pk=self.workout.pk).exists())

    def test_delete_requires_admin(self):
        auth_client(self.client, self.user)
        res = self.client.delete(reverse('workout_delete', args=[self.workout.pk]))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


# ── Exercise tests ────────────────────────────────────────────────────────────

class ExerciseTests(APITestCase):

    def setUp(self):
        self.admin   = make_user('admin@test.com', is_staff=True)
        self.user    = make_user('user@test.com')
        self.other   = make_user('other@test.com')
        self.workout = make_workout(self.admin)

    def _create_exercise(self):
        auth_client(self.client, self.user)
        return self.client.post(reverse('exercise_list'), {
            'workout': self.workout.pk,
            'date': '2025-01-01',
            'duration': 30,
            'calories_burned': 200,
            'notes': 'felt good',
        })

    def test_create_exercise(self):
        res = self._create_exercise()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['duration'], 30)

    def test_list_only_own_exercises(self):
        self._create_exercise()
        # other user creates their own
        auth_client(self.client, self.other)
        self.client.post(reverse('exercise_list'), {
            'workout': self.workout.pk, 'date': '2025-01-02',
            'duration': 20, 'calories_burned': 100, 'notes': '',
        })
        # user should only see their own
        auth_client(self.client, self.user)
        res = self.client.get(reverse('exercise_list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(data), 1)

    def test_update_own_exercise(self):
        self._create_exercise()
        ex = Exercise.objects.get(user=self.user)
        auth_client(self.client, self.user)
        res = self.client.patch(
            reverse('exercise_update', args=[ex.pk]),
            {'duration': 60},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['duration'], 60)

    def test_cannot_update_other_users_exercise(self):
        self._create_exercise()
        ex = Exercise.objects.get(user=self.user)
        auth_client(self.client, self.other)
        res = self.client.patch(
            reverse('exercise_update', args=[ex.pk]),
            {'duration': 60},
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_exercise(self):
        self._create_exercise()
        ex = Exercise.objects.get(user=self.user)
        auth_client(self.client, self.user)
        res = self.client.delete(reverse('exercise_delete', args=[ex.pk]))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_other_users_exercise(self):
        self._create_exercise()
        ex = Exercise.objects.get(user=self.user)
        auth_client(self.client, self.other)
        res = self.client.delete(reverse('exercise_delete', args=[ex.pk]))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ── Progress tests ────────────────────────────────────────────────────────────

class ProgressTests(APITestCase):

    def setUp(self):
        self.user  = make_user('user@test.com')
        self.other = make_user('other@test.com')

    def _create_entry(self):
        auth_client(self.client, self.user)
        return self.client.post(reverse('progress_list'), {
            'date': '2025-01-01', 'weight': 75.0,
            'calories_burned': 300, 'exercises_count': 2, 'notes': '',
        })

    def test_create_progress(self):
        res = self._create_entry()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['weight'], 75.0)

    def test_list_only_own_progress(self):
        self._create_entry()
        auth_client(self.client, self.other)
        res = self.client.get(reverse('progress_list'))
        data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 0)

    def test_update_progress(self):
        self._create_entry()
        entry = ProgressEntry.objects.get(user=self.user)
        auth_client(self.client, self.user)
        res = self.client.patch(
            reverse('progress_update', args=[entry.pk]),
            {'weight': 74.0},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['weight'], 74.0)

    def test_delete_progress(self):
        self._create_entry()
        entry = ProgressEntry.objects.get(user=self.user)
        auth_client(self.client, self.user)
        res = self.client.delete(reverse('progress_delete', args=[entry.pk]))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_other_users_progress(self):
        self._create_entry()
        entry = ProgressEntry.objects.get(user=self.user)
        auth_client(self.client, self.other)
        res = self.client.delete(reverse('progress_delete', args=[entry.pk]))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ── Measurement tests ─────────────────────────────────────────────────────────

class MeasurementTests(APITestCase):

    def setUp(self):
        self.user  = make_user('user@test.com')
        self.other = make_user('other@test.com')

    def _create_entry(self):
        auth_client(self.client, self.user)
        return self.client.post(reverse('measurement_list'), {
            'date': '2025-01-01', 'chest': 95.0, 'waist': 80.0,
            'hips': 100.0, 'thighs': 60.0, 'arms': 35.0,
        })

    def test_create_measurement(self):
        res = self._create_entry()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['chest'], 95.0)

    def test_list_only_own_measurements(self):
        self._create_entry()
        auth_client(self.client, self.other)
        res = self.client.get(reverse('measurement_list'))
        data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(data), 0)

    def test_update_measurement(self):
        self._create_entry()
        m = Measurement.objects.get(user=self.user)
        auth_client(self.client, self.user)
        res = self.client.patch(
            reverse('measurement_update', args=[m.pk]),
            {'waist': 78.0},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['waist'], 78.0)

    def test_delete_measurement(self):
        self._create_entry()
        m = Measurement.objects.get(user=self.user)
        auth_client(self.client, self.user)
        res = self.client.delete(reverse('measurement_delete', args=[m.pk]))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_other_users_measurement(self):
        self._create_entry()
        m = Measurement.objects.get(user=self.user)
        auth_client(self.client, self.other)
        res = self.client.delete(reverse('measurement_delete', args=[m.pk]))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ── Personal Record tests ─────────────────────────────────────────────────────

class PersonalRecordTests(APITestCase):

    def setUp(self):
        self.user  = make_user('user@test.com')
        self.other = make_user('other@test.com')

    def _create_pr(self):
        auth_client(self.client, self.user)
        return self.client.post(reverse('pr_list'), {
            'exercise': 'Bench Press', 'value': 100.0,
            'unit': 'kg', 'date': '2025-01-01',
        })

    def test_create_pr(self):
        res = self._create_pr()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['exercise'], 'Bench Press')

    def test_list_only_own_prs(self):
        self._create_pr()
        auth_client(self.client, self.other)
        res = self.client.get(reverse('pr_list'))
        data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(data), 0)

    def test_update_pr(self):
        self._create_pr()
        pr = PersonalRecord.objects.get(user=self.user)
        auth_client(self.client, self.user)
        res = self.client.patch(
            reverse('pr_update', args=[pr.pk]),
            {'value': 110.0},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['value'], 110.0)

    def test_delete_pr(self):
        self._create_pr()
        pr = PersonalRecord.objects.get(user=self.user)
        auth_client(self.client, self.user)
        res = self.client.delete(reverse('pr_delete', args=[pr.pk]))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_other_users_pr(self):
        self._create_pr()
        pr = PersonalRecord.objects.get(user=self.user)
        auth_client(self.client, self.other)
        res = self.client.delete(reverse('pr_delete', args=[pr.pk]))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
