from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.core.mail import send_mail
from django.db.models import Q
from decimal import Decimal
from .forms import (
    CustomPasswordChangeForm,
    ProfileUpdateForm,
    UserRegisterForm,
    UserUpdateForm,
    ContactForm, ProofOfPaymentForm
)
from .models import Profile, UserAccount, Inquiry, ProofOfPayment, AuditTrail, ProofOfPaymentReject
from app.models import Order
from app.utils import send_html_email
from django.template.loader import render_to_string


class ContactUsView(View):
    def get(self, request, *args, **kwargs):
        inquiries = Inquiry.objects.all()
        context = {
            'inquiries': inquiries
        }
        return render(request, 'accounts/contact_us.html', context)

    def post(self, request, *args, **kwargs):
        user = request.user
        subject = request.POST['subject']
        body = request.POST['body']
        Inquiry.objects.create(sender=user, subject=subject, body=body)
        send_mail(subject, body, user.email, [settings.EMAIL_HOST_USER])
        return HttpResponse("The Inquiry is lodged successfully wait for the feedback")


class UserRegisterView(View):
    def get(self, request, *args, **kwargs):
        form = UserRegisterForm()
        return render(request, "accounts/register.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = UserRegisterForm(request.POST)
        # last_name = request.POST['last_name']
        if form.is_valid():
            user = form.save(commit=False)
            # user.registration_number = generate_registration_number(last_name)
            user.save()
            subject = 'Welcome to MSU Short Courses Platform'
            html_message = render_to_string(
                'accounts/welcome_email.html', {'user': user})
            send_html_email(subject, html_message, [user.email])
            messages.success(
                request,
                "Your Account has been created successifully, You can now login!",
            )
            return redirect("accounts:login")
        return render(request, "accounts/register.html", {"form": form})


class ProofOfPaymentView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = ProofOfPaymentForm()
        return render(request, 'accounts/proof_of_payment.html', {'form': form})

    def post(self, request, *args, **kwgars):
        form = ProofOfPaymentForm(request.POST, request.FILES)
        amount = request.POST['amount']
        print(type(amount))
        order = Order.objects.filter(
            student=request.user, status='pending').first()
        if order.total != Decimal(amount):
            return HttpResponse("The amount does not match the total price of the order")
        if form.is_valid():
            pop = form.save(commit=False)
            pop.user = request.user
            pop.order = order
            pop.save()
            messages.success(
                request, "Thank you for uploading the proof of payment we are now working on it ")
            return redirect('app:index')
        return render(request, 'accounts/proof_of_payment.html', {'form': form})


class ProofOfPaymentDetailView(LoginRequiredMixin, View):
    def get(self, request, pop_id, *args, **kwargs):
        pop = get_object_or_404(ProofOfPayment, pk=pop_id)
        return render(request, 'accounts/pop_detail.html', {"pop": pop})


@login_required
def reject_pop(request, pop_id):
    user = request.user
    pop = get_object_or_404(ProofOfPayment, pk=pop_id)
    if request.method == 'POST':
        reason = request.POST['reason']
        pop.status = 'Rejected'
        pop.save()
        ProofOfPaymentReject.objects.create(user=user, pop=pop, reason=reason)
        AuditTrail.objects.create(
            user=user, action=f"Rejected {pop.user.email}'s POP ")
        messages.success(request, 'You have successfully rejected the POP')
        return redirect('accounts:pop_detail', pop.id)
    return render(request, 'accounts/pop_detail.html', {"pop": pop})


@login_required
def approve_pop(request, pop_id):
    user = request.user
    pop = get_object_or_404(ProofOfPayment, pk=pop_id)
    if request.method == 'POST':
        if pop.status == 'Pending':
            pop.status = "Approved"
            AuditTrail.objects.create(
                user=user, action=f"Confirmed the payment for the {pop.user.email}'s POP!")
            messages.success(
                request, "You have successfully updated the POP status to Approved")

        elif pop.status == 'Approved':
            pop.status = 'Processed'
            AuditTrail.objects.create(
                user=user, action=f"Authorized payment for the {pop.user.email}'s POP! ")
            messages.success(
                request, "You have successfully updated the POP status to Processed")

        pop.save()
        return redirect('accounts:pop_detail', pop.id)

    return render(request, 'accounts/pop_detail.html', {"pop": pop})


class AuditTrailListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        adt_list = AuditTrail.objects.all()
        context = {
            "adt_list": adt_list
        }
        return render(request, 'accounts/audit_trail.html', context)


class ProofOfPaymentListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        pops = ProofOfPayment.objects.filter(
            Q(status='Approved') | Q(status='Pending'))
        return render(request, 'accounts/pops.html', {'pops': pops})


class UserProfileView(LoginRequiredMixin, View):
    # login_url = '/login/'
    def test_func(self):
        # Define the test function to check if the user is a guest
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        # Redirect the user if they fail the test
        login_url = reverse(
            "accounts:login"
        )  # Replace 'login' with the URL or name of the login page
        next_url = (
            self.request.get_full_path()
        )  # Get the current URL as the 'next' parameter
        redirect_url = (
            # Append 'next' parameter to the login URL
            f"{login_url}?next={next_url}"
        )
        return redirect(redirect_url)

    def get(self, request, *args, **kwargs):
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
        context = {"u_form": u_form, "p_form": p_form}
        return render(request, "accounts/profile.html", context)

    def post(self, request, *args, **kwargs):
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        context = {"u_form": u_form, "p_form": p_form}
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(
                request, "You profile has been updated successfully!")
            return redirect("accounts:dashboard")
        messages.warning(request, "Failed to update your profile!")
        return render(request, "accounts/profile.html", context)


@login_required
def dashboard(request):
    form = ContactForm()
    context = {
        'form': form
    }
    return render(request, "accounts/dashboard.html", context)


class NewContactView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = ContactForm()
        return render(request, 'accounts/partials/new_contact.html', {"form": form})

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            return render(request, 'accounts/partials/contacts.html')
        return HttpResponse("<span class='text-red-700 font-semibold'>Wrong format, Failed to create the contact</span>")


class NewPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy(
        "accounts:password_change_done"
    )  # URL to redirect after successful password change


def password_change_done(request):
    return render(
        request, "accounts/password_change_done.html", {
            "title": "password change done"}
    )
