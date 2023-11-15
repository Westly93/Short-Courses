import os
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django_countries.fields import CountryField
from simple_history.models import HistoricalRecords
from django.db import models
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_resized import ResizedImageField
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timesince
from simple_history.models import HistoricalRecords


class UserAccountManager(BaseUserManager):
    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have email")
        if not password:
            raise ValueError("users must have password")
        if not first_name:
            raise ValueError("users must have first_name")
        if not last_name:
            raise ValueError("users must have last_name")

        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name,
                          last_name=last_name)
        user.set_password(password)
        extra_fields.setdefault("is_superuser", True)
        user.is_staff = True
        user.is_admin = True
        user.save()
        return user

    def create_user(self, email, first_name, last_name, password=None):
        if not email:
            raise ValueError("Users must have an email")
        if not password:
            raise ValueError("Users must have a password")
        if not first_name:
            raise ValueError("Users must at least have a first_name ")
        if not last_name:
            raise ValueError("Users must at least have a last_name ")

        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name,
                          last_name=last_name)
        user.set_password(password)
        user.save()
        return user


class UserAccount(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=255, null=True, blank=True, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    registration_number = models.CharField(
        max_length=10, unique=True, blank=True, null=True)
    history = HistoricalRecords()
    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_teacher(self):
        return True if self.email.endswith('@staff.msu.ac.zw') else False

    def get_shortname(self):
        return self.first_name

    def is_male(self):
        if self.profile.gender == "male":
            return True
        else:
            return False

    def __str__(self):
        return self.email


national_id_regex = r'^\d{8}[A-Za-z]\d{2}$'
national_id_validator = RegexValidator(
    national_id_regex,
    'Enter a valid national ID. The format should be 8 digits followed by a letter and then 2 digits.'
)


class AuditTrail(models.Model):
    user = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    when = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-id', )

    def __str__(self):
        return f"{self.user} - {self.action} at {self.when}"


class Inquiry(models.Model):
    sender = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    date_send = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.first_name} Inquiry'


class Contact(models.Model):
    user = models.ForeignKey(
        UserAccount, on_delete=models.CASCADE, related_name="contacts")
    contact_phone = PhoneNumberField(unique=True)

    def __str__(self):
        return self.contact_phone


class Profile(models.Model):
    class GenderChoices(models.TextChoices):
        MALE = 'Male'
        FEMALE = 'Female'
        OTHER = 'Other'

    class MaritalStatusChoices(models.TextChoices):
        SINGLE = 'Single'
        MARRIED = 'Married'
        DEVORCED = 'Devorced'

    bio = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    dob = models.DateField(blank=True, null=True, validators=[
                           MaxValueValidator(datetime.date.today() - datetime.timedelta(days=5840))])
    gender = models.CharField(
        max_length=10, choices=GenderChoices.choices, blank=True, null=True)
    marital_status = models.CharField(
        max_length=10, choices=MaritalStatusChoices.choices, blank=True, null=True)
    user = models.OneToOneField(
        UserAccount, on_delete=models.CASCADE, related_name="profile"
    )
    address = models.CharField(max_length=255, null=True, blank=True)
    nationality = CountryField(blank=True, null=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    national_id = models.CharField(
        max_length=11,
        null=True,
        blank=True,
        unique=True,
        validators=[national_id_validator]
    )
    thumbnail = ResizedImageField(
        size=[200, 200], quality=100, upload_to="authSystem", default="default.jpg"
    )

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    @property
    def age(self):
        today = datetime.date.today()
        age = today.year - self.dob.year
        if today.month < self.dob.month or (today.month == self.dob.month and today.day < self.dob.day):
            age -= 1
        return age

    def __str__(self):
        return f"{self.user.email}'s Profile"

    def get_profile_completion(self):
        total_weight = 0
        filled_weight = 0

        # Define the fields that contribute to profile completion with their respective weights
        profile_fields = [
            (self.bio, 2),
            (self.city, 2),
            (self.first_name, 2),
            (self.surname, 2),
            (self.gender, 1),
            (self.marital_status, 1),
            (self.address, 3),
            (self.nationality, 2),
            (self.city, 2),
            (self.national_id, 2),
            (self.thumbnail, 2),
            (self.bio, 2),

        ]

        # Calculate the total weight and filled weight
        for field, weight in profile_fields:
            total_weight += weight
            if field:
                filled_weight += weight

        if self.user.references.exists():
            total_weight += 5
            filled_weight += 5
        else:
            total_weight += 5

        if self.user.experience.exists():
            total_weight += 5
            filled_weight += 5
        else:
            total_weight += 5

        if self.user.academic_qualifications.exists():
            total_weight += 5
            filled_weight += 5
        else:
            total_weight += 5

        if self.user.contacts.exists():
            total_weight += 5
            filled_weight += 5
        else:
            total_weight += 5
        # Calculate the profile completion percentage
        if total_weight > 0:
            completion_percentage = (filled_weight / total_weight) * 100
        else:
            completion_percentage = 0

        return round(completion_percentage, 2)


@receiver(post_save, sender=UserAccount)
def create_profile(sender, created, instance, *args, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=UserAccount)
def save_profile(sender, instance, *args, **kwargs):
    instance.profile.save()


class ProofOfPayment(models.Model):
    from app.models import Order

    class StatusChoices(models.TextChoices):
        PROCESSED = 'Processed'
        APPROVED = 'Approved'
        PENDING = 'Pending'
        REJECTED = 'Rejected'
        ACTIONED = 'Actioned'

    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    date_of_payment = models.DateField()
    bank_from = models.CharField(max_length=255)
    bank_to = models.CharField(max_length=255)
    reference = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(max_length=255, null=True, blank=True)
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='proof_of_payments',
                            help_text="Accepted File Formats: We accept the following file formats: PDF, JPG, PNG.")
    status = models.CharField(
        max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.user.email} proof of payment'

    @property
    def file_extension(self):
        _, extension = os.path.splitext(self.file.name)
        return extension


class ProofOfPaymentReject(models.Model):
    user = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    pop = models.ForeignKey(ProofOfPayment, on_delete=models.CASCADE)
    reason = models.TextField()
