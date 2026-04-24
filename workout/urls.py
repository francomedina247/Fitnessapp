from django.urls import path
from .views import (
    WorkoutListView, WorkoutDetailView, WorkoutCreateView, WorkoutUpdateView, WorkoutDeleteView,
    ExerciseListCreateView, ExerciseUpdateView, ExerciseDeleteView,
    ProgressListCreateView, ProgressUpdateView, ProgressDeleteView,
    MeasurementListCreateView, MeasurementUpdateView, MeasurementDeleteView,
    PersonalRecordListCreateView, PersonalRecordUpdateView, PersonalRecordDeleteView,
)

urlpatterns = [
    # Workouts
    path('',                    WorkoutListView.as_view(),   name='workout_list'),
    path('<int:pk>/',           WorkoutDetailView.as_view(), name='workout_detail'),
    path('create/',             WorkoutCreateView.as_view(), name='workout_create'),
    path('<int:pk>/update/',    WorkoutUpdateView.as_view(), name='workout_update'),
    path('<int:pk>/partial-update/', WorkoutUpdateView.as_view(), name='workout_partial_update'),
    path('<int:pk>/delete/',    WorkoutDeleteView.as_view(), name='workout_delete'),

    # User data
    path('exercises/',                   ExerciseListCreateView.as_view(), name='exercise_list'),
    path('exercises/<int:pk>/update/',   ExerciseUpdateView.as_view(),     name='exercise_update'),
    path('exercises/<int:pk>/delete/',   ExerciseDeleteView.as_view(),     name='exercise_delete'),
    path('progress/',                    ProgressListCreateView.as_view(), name='progress_list'),
    path('progress/<int:pk>/update/',    ProgressUpdateView.as_view(),     name='progress_update'),
    path('progress/<int:pk>/delete/',    ProgressDeleteView.as_view(),     name='progress_delete'),
    path('measurements/',                  MeasurementListCreateView.as_view(), name='measurement_list'),
    path('measurements/<int:pk>/update/',   MeasurementUpdateView.as_view(),     name='measurement_update'),
    path('measurements/<int:pk>/delete/',   MeasurementDeleteView.as_view(),     name='measurement_delete'),
    path('prs/',                        PersonalRecordListCreateView.as_view(), name='pr_list'),
    path('prs/<int:pk>/update/',         PersonalRecordUpdateView.as_view(),     name='pr_update'),
    path('prs/<int:pk>/delete/',         PersonalRecordDeleteView.as_view(),     name='pr_delete'),
]
