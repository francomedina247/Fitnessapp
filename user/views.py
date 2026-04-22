import random
import string
from datetime import timedelta
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum, Count, Max
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers

from .serializers import RegisterSerializer, UserSerializer, ProfileSerializer

User = get_user_model()


class OtpRateThrottle(AnonRateThrottle):
    """5 OTP requests per hour per IP address."""
    scope = 'otp'


def send_otp(email, cache_prefix, subject):
    code = ''.join(random.choices(string.digits, k=6))
    cache.set(f'{cache_prefix}_{email}', code, timeout=600)
    try:
        send_mail(
            subject=subject,
            message=(
                f'Your verification code is: {code}\n\n'
                f'This code expires in 10 minutes.\n'
                f'If you did not request this, please ignore this email.'
            ),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@fitpro.app'),
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        raise Exception(f'Failed to send email: {str(e)}')
    return code


# ── Login ─────────────────────────────────────────────────────────────────────
class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            serializer = TokenObtainPairSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            if not user.is_verified:
                return Response(
                    {'detail': 'Email not verified. Please verify your email before signing in.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            response.data['user'] = UserSerializer(user).data
        return response


# ── Register — creates account then sends verification email ──────────────────
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        user = serializer.save()
        try:
            send_otp(user.email, 'verify', 'Verify your FitPro account')
            print(f'✅ OTP sent to {user.email}')
        except Exception as e:
            print(f'❌ OTP send failed: {e}')
            pass  # Account created — email failure is non-fatal



# ── Profile ───────────────────────────────────────────────────────────────────
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


# ── Send verification code ────────────────────────────────────────────────────
@extend_schema(request=inline_serializer('SendVerification', fields={'email': drf_serializers.EmailField()}), responses={200: OpenApiResponse(description='Code sent')})
class SendVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes   = [OtpRateThrottle]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'detail': 'An account with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            send_otp(email, 'verify', 'Verify your FitPro account')
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': 'Verification code sent.'}, status=status.HTTP_200_OK)


# ── Verify email — marks user as verified ────────────────────────────────────
@extend_schema(request=inline_serializer('VerifyEmail', fields={'email': drf_serializers.EmailField(), 'code': drf_serializers.CharField()}), responses={200: OpenApiResponse(description='Email verified')})
class VerifyEmailView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        code  = request.data.get('code', '').strip()

        if not email or not code:
            return Response({'detail': 'Email and code are required.'}, status=status.HTTP_400_BAD_REQUEST)

        cached = cache.get(f'verify_{email}')
        if not cached:
            return Response({'detail': 'Code has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
        if cached != code:
            return Response({'detail': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(f'verify_{email}')

        # Mark user as verified
        try:
            user = User.objects.get(email=email)
            user.is_verified = True
            user.save(update_fields=['is_verified'])
        except User.DoesNotExist:
            pass

        return Response({'detail': 'Email verified successfully.'}, status=status.HTTP_200_OK)


# ── Resend verification ───────────────────────────────────────────────────────
@extend_schema(request=inline_serializer('ResendVerification', fields={'email': drf_serializers.EmailField()}), responses={200: OpenApiResponse(description='Code resent')})
class ResendVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes   = [OtpRateThrottle]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Verification code sent.'}, status=status.HTTP_200_OK)
        if user.is_verified:
            return Response({'detail': 'Email already verified.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            send_otp(email, 'verify', 'Verify your FitPro account')
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'detail': 'Verification code sent.'}, status=status.HTTP_200_OK)


# ── Forgot password ───────────────────────────────────────────────────────────
@extend_schema(request=inline_serializer('ForgotPassword', fields={'email': drf_serializers.EmailField()}), responses={200: OpenApiResponse(description='Reset code sent if email exists')})
class ForgotPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes   = [OtpRateThrottle]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            try:
                send_otp(email, 'reset', 'Your FitPro Password Reset Code')
            except Exception as e:
                return Response({'detail': f'Failed to send reset email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': 'If that email exists, a reset code has been sent.'}, status=status.HTTP_200_OK)


# ── Reset password — verify OTP then set new password ────────────────────────
@extend_schema(request=inline_serializer('ResetPassword', fields={'email': drf_serializers.EmailField(), 'code': drf_serializers.CharField(), 'password': drf_serializers.CharField()}), responses={200: OpenApiResponse(description='Password reset successfully')})
class ResetPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email    = request.data.get('email', '').strip().lower()
        code     = request.data.get('code', '').strip()
        password = request.data.get('password', '')

        if not email or not code or not password:
            return Response({'detail': 'Email, code, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password)
        except ValidationError as e:
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        cached = cache.get(f'reset_{email}')
        if not cached:
            return Response({'detail': 'Code has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
        if cached != code:
            return Response({'detail': 'Invalid reset code.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'No account found with this email.'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(password)
        user.save(update_fields=['password'])
        cache.delete(f'reset_{email}')

        return Response({'detail': 'Password reset successfully.'}, status=status.HTTP_200_OK)


# ── Change password — logged-in user changes their own password ───────────────
@extend_schema(request=inline_serializer('ChangePassword', fields={'current_password': drf_serializers.CharField(), 'new_password': drf_serializers.CharField()}), responses={200: OpenApiResponse(description='Password changed')})
class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        current  = request.data.get('current_password', '')
        new_pass = request.data.get('new_password', '')

        if not current or not new_pass:
            return Response({'detail': 'current_password and new_password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not current.strip():
            return Response({'detail': 'Current password cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        if not new_pass.strip():
            return Response({'detail': 'New password cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(current):
            return Response({'detail': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_pass, user=request.user)
        except ValidationError as e:
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_pass)
        request.user.save(update_fields=['password'])
        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)


# ── Delete account — logged-in user deletes their own account ────────────────
@extend_schema(request=inline_serializer('DeleteAccount', fields={'password': drf_serializers.CharField()}), responses={204: OpenApiResponse(description='Account deleted')})
class DeleteAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        password = request.data.get('password', '')
        if not password or not password.strip():
            return Response({'detail': 'Password is required to confirm account deletion.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password, user=request.user)
        except ValidationError as e:
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(password):
            return Response({'detail': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.delete()
        return Response({'detail': 'Account deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


# ── Admin: list all users ─────────────────────────────────────────────────────
class AdminUserListView(generics.ListAPIView):
    serializer_class   = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return User.objects.filter(is_staff=False).order_by('-date_joined')


# ── Admin: delete a user ──────────────────────────────────────────────────────
class AdminUserDeleteView(generics.DestroyAPIView):
    serializer_class   = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return User.objects.filter(is_staff=False)


def _compute_streak(active_dates: set) -> int:
    """Count consecutive days ending today (or yesterday) that have activity."""
    streak = 0
    day = timezone.now().date()
    while day in active_dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


# ── Admin: per-user stats ─────────────────────────────────────────────────────
@extend_schema(responses={200: OpenApiResponse(description='List of user stats')})
class AdminUserStatsView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        from workout.models import Exercise, ProgressEntry

        users = User.objects.filter(is_staff=False).order_by('-date_joined')

        # Aggregate exercise stats per user in two queries
        exercise_agg = (
            Exercise.objects
            .values('user_id')
            .annotate(
                total_calories=Sum('calories_burned'),
                total_minutes=Sum('duration'),
                total_workouts=Count('id'),
                last_date=Max('date'),
            )
        )
        ex_map = {row['user_id']: row for row in exercise_agg}

        # Latest progress entry per user
        progress_agg = (
            ProgressEntry.objects
            .values('user_id')
            .annotate(last_date=Max('date'))
        )
        prog_last_date = {row['user_id']: row['last_date'] for row in progress_agg}

        # Active exercise dates per user (for streak) — only users with exercises
        active_dates_qs = (
            Exercise.objects
            .filter(user_id__in=ex_map.keys())
            .values_list('user_id', 'date')
        )
        user_dates: dict[int, set] = {}
        for uid, d in active_dates_qs:
            user_dates.setdefault(uid, set()).add(d)

        # Latest progress entry per user — MySQL-compatible (no distinct on field)
        latest_progress_ids = (
            ProgressEntry.objects
            .filter(user_id__in=[u.id for u in users])
            .values('user_id')
            .annotate(latest_id=Max('id'))
            .values_list('latest_id', flat=True)
        )
        latest_progress = {
            row['user_id']: row
            for row in ProgressEntry.objects
            .filter(id__in=latest_progress_ids)
            .values('id', 'user_id', 'date', 'weight', 'calories_burned', 'exercises_count', 'notes')
        }

        result = []
        for user in users:
            ex = ex_map.get(user.id, {})
            last_ex_date = ex.get('last_date')  # date object or None
            streak = _compute_streak(user_dates.get(user.id, set()))
            lp = latest_progress.get(user.id)
            result.append({
                'userId': str(user.id),
                'email': user.email,
                'name': user.name or user.username or None,
                'joinedAt': user.date_joined.isoformat(),
                'totalCaloriesBurned': ex.get('total_calories') or 0,
                'totalWorkoutsCompleted': ex.get('total_workouts') or 0,
                'totalMinutes': ex.get('total_minutes') or 0,
                'currentStreak': streak,
                'lastExerciseDate': last_ex_date.isoformat() if last_ex_date else None,
                'latestProgressEntry': {
                    'date': str(lp['date']),
                    'weight': lp['weight'],
                    'caloriesBurned': lp['calories_burned'],
                    'exercisesCount': lp['exercises_count'],
                    'notes': lp['notes'],
                } if lp else None,
            })

        return Response(result)
