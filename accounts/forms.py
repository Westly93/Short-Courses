from django import forms
from django_countries.widgets import CountrySelectWidget
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from .models import Profile, UserAccount, Contact, ProofOfPayment
from captcha.fields import ReCaptchaField


class ContactForm(forms.ModelForm):
    contact_phone = PhoneNumberField(
        widget=PhoneNumberPrefixWidget(
            initial="ZW",
            attrs={
                'class': 'text-sm rounded-md w-full mb-5 border border-gray-500 py-2'},
        ),

    )

    class Meta:
        model = Contact
        fields = ("contact_phone",)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput,
    )
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    captcha = ReCaptchaField()

    class Meta:
        model = UserAccount
        fields = ["first_name", "last_name", "email",
                  "password1", "password2", "captcha"]


class ProofOfPaymentForm(forms.ModelForm):
    date_of_payment = forms.DateField(widget=forms.DateInput({
        "type": "date"
    }))
    file = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(
            attrs={'accept': 'application/pdf, image/*'}),
        help_text="<p class='text-red-700 font-bold py-2 italic'>We accept the following file formats: PDF, JPG, PNG. File size: (2 MB).</p>"
    )

    class Meta:
        model = ProofOfPayment
        fields = ["bank_from", "bank_to", "amount",
                  "reference", "payment_method", "date_of_payment", 'file']


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = UserAccount
        fields = ["email", "first_name", "last_name"]


class ProfileUpdateForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea(
        attrs={"rows": 3, "placeholder": "Description about yourself", "required": False}))
    dob = forms.DateField(widget=forms.DateInput({
        "type": "date"
    }))
    national_id = forms.CharField(widget=forms.TextInput(
        attrs={"placeholder": "05121587Y05"}
    ))
    address = forms.CharField(widget=forms.TextInput(
        attrs={"placeholder": "3155 Wood Broke North "}
    ))
    city = forms.CharField(widget=forms.TextInput(
        attrs={"placeholder": "Bindura"}
    ))

    class Meta:
        model = Profile
        fields = ["dob", "national_id", "gender",
                  "marital_status", "bio", "address", "city", "nationality", "thumbnail"]
        widgets = {"nationality": CountrySelectWidget()}


class CustomPasswordChangeForm(PasswordChangeForm):
    pass
