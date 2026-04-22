from rest_framework import generics, permissions
from .models import Workout, Exercise, ProgressEntry, Measurement, PersonalRecord
from .serializers import (
    WorkoutSerializer, ExerciseSerializer,
    ProgressEntrySerializer, MeasurementSerializer, PersonalRecordSerializer,
)


# ── Workouts (read-only for users, full access for admin) ─────────────────────
class WorkoutListView(generics.ListAPIView):
    queryset         = Workout.objects.all().order_by('name')
    serializer_class = WorkoutSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = None  # Workouts are a small fixed set, load all at once


class WorkoutDetailView(generics.RetrieveAPIView):
    queryset         = Workout.objects.all()
    serializer_class = WorkoutSerializer
    permission_classes = (permissions.IsAuthenticated,)


class WorkoutCreateView(generics.CreateAPIView):
    queryset         = Workout.objects.all()
    serializer_class = WorkoutSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class WorkoutUpdateView(generics.UpdateAPIView):
    queryset         = Workout.objects.all()
    serializer_class = WorkoutSerializer
    permission_classes = (permissions.IsAdminUser,)


class WorkoutDeleteView(generics.DestroyAPIView):
    queryset         = Workout.objects.all()
    serializer_class = WorkoutSerializer
    permission_classes = (permissions.IsAdminUser,)


# ── Exercises ─────────────────────────────────────────────────────────────────
class ExerciseListCreateView(generics.ListCreateAPIView):
    serializer_class   = ExerciseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Exercise.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExerciseUpdateView(generics.UpdateAPIView):
    serializer_class   = ExerciseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Exercise.objects.filter(user=self.request.user)


class ExerciseDeleteView(generics.DestroyAPIView):
    serializer_class   = ExerciseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Exercise.objects.filter(user=self.request.user)


# ── Progress entries ──────────────────────────────────────────────────────────
class ProgressListCreateView(generics.ListCreateAPIView):
    serializer_class   = ProgressEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ProgressEntry.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProgressUpdateView(generics.UpdateAPIView):
    serializer_class   = ProgressEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ProgressEntry.objects.filter(user=self.request.user)


class ProgressDeleteView(generics.DestroyAPIView):
    serializer_class   = ProgressEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ProgressEntry.objects.filter(user=self.request.user)


# ── Measurements ──────────────────────────────────────────────────────────────
class MeasurementListCreateView(generics.ListCreateAPIView):
    serializer_class   = MeasurementSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Measurement.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MeasurementUpdateView(generics.UpdateAPIView):
    serializer_class   = MeasurementSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Measurement.objects.filter(user=self.request.user)


class MeasurementDeleteView(generics.DestroyAPIView):
    serializer_class   = MeasurementSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Measurement.objects.filter(user=self.request.user)


# ── Personal Records ──────────────────────────────────────────────────────────
class PersonalRecordListCreateView(generics.ListCreateAPIView):
    serializer_class   = PersonalRecordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return PersonalRecord.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PersonalRecordUpdateView(generics.UpdateAPIView):
    serializer_class   = PersonalRecordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return PersonalRecord.objects.filter(user=self.request.user)


class PersonalRecordDeleteView(generics.DestroyAPIView):
    serializer_class   = PersonalRecordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return PersonalRecord.objects.filter(user=self.request.user)
