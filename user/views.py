import random
import string
from datetime import timedelta
from email.utils import parseaddr

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Max, Sum
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import generics, permissions, serializers as drf_serializers, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from workout.models import Exercise, Workout
from .serializers import ProfileSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class OtpRateThrottle(AnonRateThrottle):
    """5 OTP requests per hour per IP address."""

    scope = "otp"


def _resolve_from_email() -> str:
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "").strip()
    _, address = parseaddr(from_email)
    email_backend = getattr(settings, "EMAIL_BACKEND", "")
    email_host = getattr(settings, "EMAIL_HOST", "")

    if not from_email or not address:
        raise ImproperlyConfigured("DEFAULT_FROM_EMAIL must be set to a valid sender email address.")

    if email_backend == "django.core.mail.backends.console.EmailBackend":
        raise ImproperlyConfigured(
            "Email delivery is using the console backend. Configure Brevo SMTP before allowing OTP signup."
        )

    if "brevo" in email_host.lower() and address.lower().endswith("@smtp-brevo.com"):
        raise ImproperlyConfigured(
            "DEFAULT_FROM_EMAIL must be a verified Brevo sender address, not the SMTP login address."
        )

    return from_email


def send_otp(email: str, cache_prefix: str, subject: str) -> str:
    code = "".join(random.choices(string.digits, k=6))
    from_email = _resolve_from_email()

    try:
        send_mail(
            subject=subject,
            message=(
                f"Your verification code is: {code}\n\n"
                "This code expires in 10 minutes.\n"
                "If you did not request this, please ignore this email."
            ),
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as exc:
        raise Exception(f"Failed to send email: {exc}") from exc

    cache.set(f"{cache_prefix}_{email}", code, timeout=600)
    return code


class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            serializer = TokenObtainPairSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            if not user.is_verified:
                return Response(
                    {"detail": "Email not verified. Please verify your email before signing in."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            response.data["user"] = UserSerializer(user).data
        return response


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                user = serializer.save()
                send_otp(user.email, "verify", "Verify your FitPro account")
        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "detail": "Registration successful. Verification code sent.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


@extend_schema(
    request=inline_serializer("SendVerification", fields={"email": drf_serializers.EmailField()}),
    responses={200: OpenApiResponse(description="Code sent")},
)
class SendVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [OtpRateThrottle]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "An account with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            send_otp(email, "verify", "Verify your FitPro account")
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "Verification code sent."}, status=status.HTTP_200_OK)


@extend_schema(
    request=inline_serializer(
        "VerifyEmail",
        fields={"email": drf_serializers.EmailField(), "code": drf_serializers.CharField()},
    ),
    responses={200: OpenApiResponse(description="Email verified")},
)
class VerifyEmailView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        code = request.data.get("code", "").strip()

        if not email or not code:
            return Response(
                {"detail": "Email and code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cached = cache.get(f"verify_{email}")
        if not cached:
            return Response(
                {"detail": "Code has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if cached != code:
            return Response(
                {"detail": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete(f"verify_{email}")

        try:
            user = User.objects.get(email=email)
            user.is_verified = True
            user.save(update_fields=["is_verified"])
        except User.DoesNotExist:
            pass

        return Response({"detail": "Email verified successfully."}, status=status.HTTP_200_OK)


@extend_schema(
    request=inline_serializer("ResendVerification", fields={"email": drf_serializers.EmailField()}),
    responses={200: OpenApiResponse(description="Code resent")},
)
class ResendVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [OtpRateThrottle]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Verification code sent."}, status=status.HTTP_200_OK)
        if user.is_verified:
            return Response({"detail": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            send_otp(email, "verify", "Verify your FitPro account")
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"detail": "Verification code sent."}, status=status.HTTP_200_OK)


@extend_schema(
    request=inline_serializer("ForgotPassword", fields={"email": drf_serializers.EmailField()}),
    responses={200: OpenApiResponse(description="Reset code sent if email exists")},
)
class ForgotPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [OtpRateThrottle]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            try:
                send_otp(email, "reset", "Your FitPro Password Reset Code")
            except Exception as exc:
                return Response(
                    {"detail": f"Failed to send reset email: {exc}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {"detail": "If that email exists, a reset code has been sent."},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    request=inline_serializer(
        "ResetPassword",
        fields={
            "email": drf_serializers.EmailField(),
            "code": drf_serializers.CharField(),
            "password": drf_serializers.CharField(),
        },
    ),
    responses={200: OpenApiResponse(description="Password reset successfully")},
)
class ResetPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        code = request.data.get("code", "").strip()
        password = request.data.get("password", "")

        if not email or not code or not password:
            return Response(
                {"detail": "Email, code, and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(password)
        except ValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        cached = cache.get(f"reset_{email}")
        if not cached:
            return Response(
                {"detail": "Code has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if cached != code:
            return Response({"detail": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No account found with this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.set_password(password)
        user.save(update_fields=["password"])
        cache.delete(f"reset_{email}")

        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)


@extend_schema(
    request=inline_serializer(
        "ChangePassword",
        fields={
            "current_password": drf_serializers.CharField(),
            "new_password": drf_serializers.CharField(),
        },
    ),
    responses={200: OpenApiResponse(description="Password changed")},
)
class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        current = request.data.get("current_password", "")
        new_pass = request.data.get("new_password", "")

        if not current or not new_pass:
            return Response(
                {"detail": "current_password and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not current.strip():
            return Response(
                {"detail": "Current password cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not new_pass.strip():
            return Response(
                {"detail": "New password cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(current):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_pass, user=request.user)
        except ValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_pass)
        request.user.save(update_fields=["password"])
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


@extend_schema(
    request=inline_serializer("DeleteAccount", fields={"password": drf_serializers.CharField()}),
    responses={204: OpenApiResponse(description="Account deleted")},
)
class DeleteAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        password = request.data.get("password", "")
        if not password or not password.strip():
            return Response(
                {"detail": "Password is required to confirm account deletion."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(password, user=request.user)
        except ValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(password):
            return Response({"detail": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)

        request.user.delete()
        return Response({"detail": "Account deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=inline_serializer("RegisterPushToken", fields={"token": drf_serializers.CharField()}),
    responses={200: OpenApiResponse(description="Token registered")},
)
class RegisterPushTokenView(APIView):
    """Store the Expo push token for the authenticated user."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        token = request.data.get("token", "").strip()
        if not token:
            return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not token.startswith("ExponentPushToken["):
            return Response({"detail": "Invalid Expo push token format."}, status=status.HTTP_400_BAD_REQUEST)
        request.user.push_token = token
        request.user.save(update_fields=["push_token"])
        return Response({"detail": "Push token registered."}, status=status.HTTP_200_OK)


@extend_schema(
    request=inline_serializer(
        "AdminSendNotification",
        fields={
            "title": drf_serializers.CharField(),
            "body": drf_serializers.CharField(),
            "user_ids": drf_serializers.ListField(child=drf_serializers.IntegerField(), required=False),
        },
    ),
    responses={200: OpenApiResponse(description="Notification sent")},
)
class AdminSendNotificationView(APIView):
    """
    Admin endpoint to send a push notification.
    If user_ids is omitted or empty, broadcasts to ALL users with a push token.
    """
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        from .push import broadcast_push

        title = request.data.get("title", "").strip()
        body = request.data.get("body", "").strip()
        user_ids = request.data.get("user_ids", [])

        if not title or not body:
            return Response({"detail": "title and body are required."}, status=status.HTTP_400_BAD_REQUEST)

        qs = User.objects.filter(push_token__isnull=False).exclude(push_token="")
        if user_ids:
            qs = qs.filter(id__in=user_ids)

        sent = broadcast_push(list(qs), title, body)
        return Response({"detail": f"Notification sent to {sent} device(s).", "sent": sent})


class AdminUserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return User.objects.filter(is_staff=False).order_by("-date_joined")


class AdminUserDeleteView(generics.DestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return User.objects.filter(is_staff=False)


class AdminUserDetailView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk, is_staff=False)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        exercises = (
            Exercise.objects
            .filter(user_id=pk)
            .select_related("workout")
            .order_by("-date")[:50]
        )

        exercise_list = [
            {
                "id": e.id,
                "workoutId": str(e.workout_id),
                "workoutName": e.workout.name if e.workout else str(e.workout_id),
                "date": str(e.date),
                "duration": e.duration,
                "caloriesBurned": e.calories_burned,
                "notes": e.notes or "",
            }
            for e in exercises
        ]

        return Response({
            "id": str(user.id),
            "email": user.email,
            "name": user.name or user.username or None,
            "joinedAt": user.date_joined.isoformat(),
            "isVerified": user.is_verified,
            "gender": user.gender,
            "height": user.height,
            "weight": user.weight,
            "age": user.age,
            "goalWeight": user.goal_weight,
            "weightUnit": user.weight_unit,
            "heightUnit": user.height_unit,
            "primaryGoal": user.primary_goal,
            "experienceLevel": user.experience_level,
            "weeklyWorkoutTarget": user.weekly_workout_target,
            "bodyFat": user.body_fat,
            "restingHeartRate": user.resting_heart_rate,
            "sleepHours": user.sleep_hours,
            "bio": user.bio,
            "recentExercises": exercise_list,
        })


def _compute_streak(active_dates: set) -> int:
    """Count consecutive days ending today (or yesterday) that have activity."""

    streak = 0
    day = timezone.now().date()
    while day in active_dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


STREAK_MILESTONES = {3, 7, 14, 30, 60, 100}


def maybe_send_streak_email(user) -> None:
    """Send a congratulatory email if the user just hit a streak milestone."""
    from workout.models import Exercise

    active_dates = set(
        Exercise.objects.filter(user=user).values_list("date", flat=True)
    )
    streak = _compute_streak(active_dates)
    if streak not in STREAK_MILESTONES:
        return

    try:
        from_email = _resolve_from_email()
    except Exception:
        return

    subject = f"🔥 {streak}-Day Streak — Keep it up, {user.name or user.username}!"
    message = (
        f"Hi {user.name or user.username},\n\n"
        f"You've worked out {streak} days in a row — that's incredible!\n"
        "Keep the momentum going and crush your next session.\n\n"
        "— The FitPro Team"
    )
    try:
        send_mail(subject, message, from_email, [user.email], fail_silently=True)
    except Exception:
        pass


def maybe_send_goal_email(user, new_weight: float) -> None:
    """Send a congratulatory email if the user has reached their goal weight."""
    if not user.goal_weight or not user.weight:
        return

    # Determine direction: losing or gaining
    losing = user.goal_weight < user.weight
    reached = (losing and new_weight <= user.goal_weight) or (
        not losing and new_weight >= user.goal_weight
    )
    if not reached:
        return

    try:
        from_email = _resolve_from_email()
    except Exception:
        return

    subject = f"🏆 Goal Reached, {user.name or user.username}!"
    message = (
        f"Hi {user.name or user.username},\n\n"
        f"You've hit your goal weight of {user.goal_weight} kg — amazing work!\n"
        "Time to set your next goal and keep pushing forward.\n\n"
        "— The FitPro Team"
    )
    try:
        send_mail(subject, message, from_email, [user.email], fail_silently=True)
    except Exception:
        pass


@extend_schema(responses={200: OpenApiResponse(description="Workout session counts")})
class AdminWorkoutStatsView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        from workout.models import Exercise
        from django.db.models import Count

        counts = (
            Exercise.objects
            .values("workout_id", "workout__name")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        return Response([
            {"workoutId": str(row["workout_id"]), "workoutName": row["workout__name"], "count": row["total"]}
            for row in counts
        ])


class AdminUserStatsView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        from workout.models import Exercise, ProgressEntry

        users = User.objects.filter(is_staff=False).order_by("-date_joined")

        exercise_agg = (
            Exercise.objects.values("user_id")
            .annotate(
                total_calories=Sum("calories_burned"),
                total_minutes=Sum("duration"),
                total_workouts=Count("id"),
                last_date=Max("date"),
            )
        )
        ex_map = {row["user_id"]: row for row in exercise_agg}

        active_dates_qs = (
            Exercise.objects.filter(user_id__in=ex_map.keys()).values_list("user_id", "date")
        )
        user_dates: dict[int, set] = {}
        for uid, active_date in active_dates_qs:
            user_dates.setdefault(uid, set()).add(active_date)

        latest_progress_ids = (
            ProgressEntry.objects.filter(user_id__in=[user.id for user in users])
            .values("user_id")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )
        latest_progress = {
            row["user_id"]: row
            for row in ProgressEntry.objects.filter(id__in=latest_progress_ids).values(
                "id",
                "user_id",
                "date",
                "weight",
                "calories_burned",
                "exercises_count",
                "notes",
            )
        }

        result = []
        for user in users:
            ex = ex_map.get(user.id, {})
            last_ex_date = ex.get("last_date")
            streak = _compute_streak(user_dates.get(user.id, set()))
            lp = latest_progress.get(user.id)
            result.append(
                {
                    "userId": str(user.id),
                    "email": user.email,
                    "name": user.name or user.username or None,
                    "joinedAt": user.date_joined.isoformat(),
                    "totalCaloriesBurned": ex.get("total_calories") or 0,
                    "totalWorkoutsCompleted": ex.get("total_workouts") or 0,
                    "totalMinutes": ex.get("total_minutes") or 0,
                    "currentStreak": streak,
                    "lastExerciseDate": last_ex_date.isoformat() if last_ex_date else None,
                    "latestProgressEntry": (
                        {
                            "date": str(lp["date"]),
                            "weight": lp["weight"],
                            "caloriesBurned": lp["calories_burned"],
                            "exercisesCount": lp["exercises_count"],
                            "notes": lp["notes"],
                        }
                        if lp
                        else None
                    ),
                }
            )

        return Response(result)
