from django import forms
from .models import Category, Course, Topic, Lesson, Enrollment
from accounts.models import UserAccount
from django.forms import TextInput


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name",)


class EnrollmentForm(forms.ModelForm):
    student = forms.ModelMultipleChoiceField(
        queryset=UserAccount.objects.all()
    )

    class Meta:
        model = Enrollment
        fields = ("status", "student")


class CourseForm(forms.ModelForm):
    price = forms.DecimalField(required=False)
    # what_you_will_learn = forms.CharField(widget=CKEditorWidget())
    description = forms.CharField(required=True, widget=forms.Textarea(
        attrs={"rows": 3, "placeholder": "Course Description"}))
    start_date = forms.DateField(required=True, widget=forms.DateInput({
        "type": "date"
    }))
    course_duration = forms.DurationField(
        help_text="Enter the duration in the format 'X days, X hours'."
    )

    class Meta:
        model = Course
        fields = ("category", "title", "description",
                  "price", 'course_duration', 'start_date')
        widgets = {
            'course_duration': TextInput(attrs={'class': 'durationInputWidget'})
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ("title", "summary")


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ("title", "content", "attachment")
