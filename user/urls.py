from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    SendVerificationView,
    VerifyEmailView,
    ResendVerificationView,
    ForgotPasswordView,
    ResetPasswordView,
    ChangePasswordView,
    DeleteAccountView,
    AdminUserListView,
    AdminUserDeleteView,
    AdminUserStatsView,
)

urlpatterns = [
    path('register/',              RegisterView.as_view(),          name='register'),
    path('login/',                 LoginView.as_view(),              name='login'),
    path('token/refresh/',         TokenRefreshView.as_view(),       name='token_refresh'),
    path('profile/',               ProfileView.as_view(),            name='profile'),
    path('send-verification/',     SendVerificationView.as_view(),   name='send_verification'),
    path('verify-email/',          VerifyEmailView.as_view(),        name='verify_email'),
    path('resend-verification/',   ResendVerificationView.as_view(), name='resend_verification'),
    path('forgot-password/',       ForgotPasswordView.as_view(),     name='forgot_password'),
    path('reset-password/',        ResetPasswordView.as_view(),      name='reset_password'),
    path('change-password/',        ChangePasswordView.as_view(),    name='change_password'),
    path('delete-account/',         DeleteAccountView.as_view(),     name='delete_account'),
    path('admin/users/',           AdminUserListView.as_view(),      name='admin_user_list'),
    path('admin/users/stats/',     AdminUserStatsView.as_view(),     name='admin_user_stats'),
    path('admin/users/<int:pk>/delete/', AdminUserDeleteView.as_view(), name='admin_user_delete'),
]
