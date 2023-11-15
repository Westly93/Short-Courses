from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import path, reverse_lazy, include

from .views import (
    dashboard,
    ContactUsView,
    NewPasswordChangeView,
    UserProfileView,
    UserRegisterView,
    password_change_done, NewContactView,
    ProofOfPaymentView, ProofOfPaymentListView,
    ProofOfPaymentDetailView, approve_pop, AuditTrailListView, reject_pop
)

app_name = "accounts"
urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
    path("proof-of-payment/", ProofOfPaymentView.as_view(), name="proof_of_payment"),
    path("pops/", ProofOfPaymentListView.as_view(), name="pops"),
    path("pops/<int:pop_id>/approve", approve_pop, name="approve_pop"),
    path("pops/<int:pop_id>/reject", reject_pop, name="reject_pop"),
    path("pops/<int:pop_id>/",
         ProofOfPaymentDetailView.as_view(), name="pop_detail"),
    path("audit_trail", AuditTrailListView.as_view(), name="audit_trail"),
    path(
        "login/", LoginView.as_view(template_name="accounts/login.html"), name="login"
    ),
    path("signup/", UserRegisterView.as_view(), name="register"),
    path("new_contact/", NewContactView.as_view(), name="new_contact"),

    path(
        "logout/",
        LogoutView.as_view(template_name="accounts/logout.html"),
        name="logout",
    ),
    path("profile/update/", UserProfileView.as_view(), name="profile-update"),
    # password reset
    path("password_change/", NewPasswordChangeView.as_view(), name="password_change"),
    path("password_change/done/", password_change_done,
         name="password_change_done"),
    path(
        "password_reset/",
        PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name='accounts/password_reset_email.html',
            success_url=reverse_lazy('accounts:password_reset_done')),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy('accounts:password_reset_complete')
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path('api/v1/', include('djoser.urls')),
    path('api/v1/', include('djoser.urls.jwt')),
    path('contact-us/', ContactUsView.as_view(), name='contact-us'),

]
