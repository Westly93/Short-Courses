import datetime
from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import UserAccount
from simple_history.models import HistoricalRecords
from django_resized import ResizedImageField
from ckeditor.fields import RichTextField


""" class Course(models.Model):
    name= models.CharField(max_length= 1000)
    owner_id = models.ForeignKey(
        UserAccount, on_delete=models.CASCADE, related_name='courses')
    date_created = models.DateTimeField(auto_now_add=True) """


class Course(models.Model):
    class StatusChoices(models.TextChoices):
        PUBLISH = 'Publish'
        DRAFT = 'Draft'
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    instructor = models.ForeignKey(
        UserAccount, on_delete=models.CASCADE, related_name="courses")
    title = models.CharField(max_length=1000)
    description = models.TextField(blank=True, null=True)
    link = models.CharField(max_length=255, null=True, blank=True)
    what_you_will_learn = RichTextField(blank=True, null=True)
    featured_image = ResizedImageField(
        size=[200, 200], quality=100, upload_to="courses", blank=True, null=True
    )
    course_duration = models.DurationField()
    start_date = models.DateField(blank=True, null=True)
    class_id = models.CharField(max_length=255, null=True, blank=True)
    featured_video = models.FileField(
        upload_to="courses", blank=True, null=True)
    price = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    status = models.CharField(
        max_length=10, choices=StatusChoices.choices, default=StatusChoices.DRAFT)

    created = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ('-id', )

    @property
    def discount_amount(self):
        return (self.discount / 100) * float(self.price)

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(max_length=1000, unique=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Order(models.Model):
    class IsPaidStatus(models.TextChoices):
        PAID = 'paid'
        CANCELED = 'cancelled'
        PENDING = 'pending'
    student = models.ForeignKey(
        UserAccount, on_delete=models.CASCADE, related_name="orders")
    paynow_reference = models.CharField(max_length=20, blank=True, null=True)
    courses = models.ManyToManyField(Course, related_name='courses')
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        default=IsPaidStatus.PENDING, max_length=10, choices=IsPaidStatus.choices)
    order_date = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    @property
    def total(self):
        return sum([course.price for course in self.courses.all()])

    def __str__(self):
        return f'Order for {self.student.first_name}'


class Enrollment(models.Model):
    class StatusChoices(models.TextChoices):
        DROPPED = "Dropped"
        COMPLETED = "Completed"
        ENROLLED = "Enrolled"
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(
        UserAccount, on_delete=models.CASCADE, related_name='enrollments', blank=True, null=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10, choices=StatusChoices.choices, default=StatusChoices.ENROLLED)


class Topic(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=2000)
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.title} topic for {self.course.title}'


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=2000)
    content = models.TextField(null=True, blank=True)
    attachment = models.FileField(upload_to=f"courses/", null=True, blank=True)

    def __str__(self):
        return f'{self.title} lesson for the topic {self.topic.title}'


class PollUrl(models.Model):
    class StatusChoces(models.TextChoices):
        CREATED = 'created'
        PAID = "paid"
        DISPUTED = 'disputed'
        REFUNDED = 'refunded'
        SENT = 'sent'
    student = models.ForeignKey(
        UserAccount, on_delete=models.CASCADE, related_name="poll_url")
    poll_url = models.CharField(max_length=255)
    status = models.CharField(
        max_length=10, choices=StatusChoces.choices, default=StatusChoces.CREATED)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.first_name} poll url'


class Transaction(models.Model):
    reference = models.CharField(max_length=255, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=20, null=True)
    registration_number = models.CharField(max_length=10, null=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}'s Transaction"


class InterBankRate(models.Model):
    rate = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


""" class Quiz(models.Model):
    pass 
class Question(models.Model):
    pass
class Answer(models.Model):
    pass """
