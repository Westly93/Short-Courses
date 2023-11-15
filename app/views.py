import os
import math
import time
import decimal
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import LessonForm, CategoryForm, CourseForm, TopicForm, EnrollmentForm
from .admin import OrderTableResource
from .tables import OrdersTable
from .models import Course, Topic, Lesson, Order, Enrollment, PollUrl, InterBankRate
from accounts.models import Profile, AuditTrail, ProofOfPayment
from .utils import get_credentials, generate_random_password, send_email, get_zwl_price, initialize_paynow, send_html_email
from classroom.views import get_user_credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from accounts.utils import generate_registration_number
from urllib.parse import unquote
from bokeh.models import ColumnDataSource, NumeralTickFormatter, HoverTool
from bokeh.embed import components
from bokeh.plotting import figure
from django.db.models import Max, Min, ExpressionWrapper, fields, Count, F, Sum
from django.db.models.functions import TruncDate, Now
from bokeh.models import ColumnDataSource, NumeralTickFormatter, HoverTool
from bokeh.embed import components
from bokeh.plotting import figure
from django.template.loader import render_to_string


class CourseListView(View):

    def get(self, request, *args, **kwargs):
        courses = Course.objects.all()

        context = {
            'courses': courses
        }
        return render(request, 'app/index.html', context)


""" class CourseListView(View):
    def get(self, request, *args, **kwargs):
        courses = Course.objects.all()
        context = {
            "courses": courses
        }
        return render(request, 'app/index.html', context)

    def post(self, request, *args, **kwargs):
        pass
 """


class ReportsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        total_revenue = sum([
            enrollment.course.price for enrollment in Enrollment.objects.all()
        ])
        total_students = Enrollment.objects.values(
            'student').distinct().count()
        enrolled_courses = Enrollment.objects.values(
            'course').distinct().count()
        number_of_instructors = Course.objects.values(
            'instructor').distinct().count()
        script, div = self.students_enrolled_per_course()
        script1, div1 = self.course_sales()
        script2, div2 = self.daily_sales()
        script3, div3 = self.sales_by_age()
        gender = Profile.GenderChoices.labels
        context = {
            "total_revenue": total_revenue,
            "total_students": total_students,
            "enrolled_courses": enrolled_courses,
            "number_of_instructors": number_of_instructors,
            "script": script,
            "div": div,
            "script1": script1,
            "div1": div1,
            "script2": script2,
            "div2": div2,
            "script3": script3,
            "div3": div3,
            'gender': gender
        }
        return render(request, 'app/reports.html', context)

    def students_enrolled_per_course(self):
        enrollments = Enrollment.objects.values(
            'course__title').annotate(enrollment_count=Count('course'))
        course_titles = [enrollment['course__title']
                         for enrollment in enrollments]
        counts = [enrollment['enrollment_count'] for enrollment in enrollments]
        # print(course_titles)
        source = ColumnDataSource(
            data=dict(course_titles=course_titles, counts=counts))
        fig = figure(x_range=course_titles, height=500,
                     title="Total Students Enrolled")
        fig.vbar(source=source, top="counts", x="course_titles", width=0.8)
        fig.title.align = "center"
        fig.title.text_font_size = "1.5em"
        fig.xaxis.major_label_orientation = math.pi / 4
        # fig.yaxis.formatter = NumeralTickFormatter(format="$0.0a")
        tooltips = [
            ("Course", "@course_titles"),
            ("Students", "@counts")
        ]
        fig.add_tools(HoverTool(tooltips=tooltips))

        script, div = components(fig)

        return script, div

    def course_sales(self):
        enrollments = Enrollment.objects.values(
            'course__title').annotate(sales=Sum('course__price'))
        course_titles = [enrollment['course__title']
                         for enrollment in enrollments]
        sales = [enrollment['sales'] for enrollment in enrollments]
        # print(course_titles)
        source = ColumnDataSource(
            data=dict(course_titles=course_titles, sales=sales))
        fig = figure(x_range=course_titles, height=500,
                     title="Total Sales (USD)")
        fig.vbar(source=source, top="sales", x="course_titles", width=0.8)
        fig.title.align = "center"
        fig.title.text_font_size = "1.5em"
        fig.xaxis.major_label_orientation = math.pi / 4
        # fig.yaxis.formatter = NumeralTickFormatter(format="$0.0a")
        tooltips = [
            ("Course", "@course_titles"),
            ("Sales", "@sales")
        ]
        fig.add_tools(HoverTool(tooltips=tooltips))

        script, div = components(fig)

        return script, div

    def daily_sales(self):
        enrollments = Enrollment.objects.annotate(
            date=TruncDate('enrolled_at')).values('date').annotate(sales=Sum('course__price'))
        dates = [str(enrollment['date'])
                 for enrollment in enrollments]
        sales = [enrollment['sales'] for enrollment in enrollments]
        # print(course_titles)
        source = ColumnDataSource(
            data=dict(dates=dates, sales=sales))
        fig = figure(x_range=dates, height=500,
                     title="Total Daily Sales(USD)")
        fig.vbar(source=source, top="sales", x="dates", width=0.8)
        fig.title.align = "center"
        fig.title.text_font_size = "1.5em"
        fig.xaxis.major_label_orientation = math.pi / 4
        fig.yaxis.formatter = NumeralTickFormatter(format="$0.0a")
        tooltips = [
            ("Date", "@dates"),
            ("Sales", "@sales")
        ]
        fig.add_tools(HoverTool(tooltips=tooltips))

        script, div = components(fig)

        return script, div

    def sales_by_age(self):
        enrollments = Enrollment.objects.annotate(
            user_age=ExpressionWrapper(
                F('student__profile__dob'),
                output_field=fields.DateField()
            )
        ).annotate(
            age=ExpressionWrapper(
                Now(),
                output_field=fields.DateField()
            ) - F('user_age')
        ).values('age').annotate(count=Count('course'))
        # age_range = [math.floor(enrollment['age'].days/365.25) if enrollment['age'] else None
        #             for enrollment in enrollments]
        age_range = (20, 71)
        count = [enrollment['count'] for enrollment in enrollments]
        # print(course_titles)
        source = ColumnDataSource(
            data=dict(age_range=age_range, count=count))
        fig = figure(x_range=age_range, height=500,
                     title="Total Number of Students Based on Age")
        fig.vbar(source=source, top="count", x="age_range", width=0.8)
        fig.title.align = "center"
        fig.title.text_font_size = "1.5em"
        fig.xaxis.major_label_orientation = math.pi / 4
        # fig.yaxis.formatter = NumeralTickFormatter(format="$0.0a")
        tooltips = [
            ("Age", "@age_range"),
            ("Students", "@count")
        ]
        fig.add_tools(HoverTool(tooltips=tooltips))

        script, div = components(fig)

        return script, div

    def monthly_sales(self):
        pass

    def post(self, request, *args, **kwargs):
        pass


def students_enrolled_by_gender(request):
    selected_gender = request.GET.get('gender')
    if selected_gender:
        enrollments = Enrollment.objects.filter(student__profile__gender=selected_gender).values(
            'course__title').annotate(enrollment_count=Count('course'))
    else:
        enrollments = Enrollment.objects.values(
            'course__title').annotate(enrollment_count=Count('course'))
    course_titles = [enrollment['course__title']
                     for enrollment in enrollments]
    counts = [enrollment['enrollment_count'] for enrollment in enrollments]
    # print(course_titles)
    source = ColumnDataSource(
        data=dict(course_titles=course_titles, counts=counts))
    fig = figure(x_range=course_titles, height=500,
                 title="Total Students Enrolled")
    fig.vbar(source=source, top="counts", x="course_titles", width=0.8)
    fig.title.align = "center"
    fig.title.text_font_size = "1.5em"
    fig.xaxis.major_label_orientation = math.pi / 4
    # fig.yaxis.formatter = NumeralTickFormatter(format="$0.0a")
    tooltips = [
        ("Course", "@course_titles"),
        ("Students", "@counts")
    ]
    fig.add_tools(HoverTool(tooltips=tooltips))

    script, div = components(fig)
    return render(request, 'app/partials/students_enrolled_by_gender.html', {"script": script, "div": div})


class NewCourseView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        creds = get_user_credentials(request)
        if not request.user.is_teacher:
            return HttpResponseForbidden()
        if creds:
            form = CourseForm()
            context = {"form": form}
            return render(request, "app/new_course.html", context)
        return HttpResponse("You are not logged in Please login ")

    def post(self, request, *args, **kwargs):
        token_path = settings.BASE_DIR / 'lecturer_token.json'
        form = CourseForm(request.POST)
        course_name = request.POST['title']
        course_description = request.POST['description']
        course = {
            'name': course_name,
            'descriptionHeading': course_description,
            'ownerId': request.user.email,
            'courseState': 'Active',
        }
        creds = get_credentials(
            ['https://www.googleapis.com/auth/classroom.courses'], token_path)

        try:
            service = build('classroom', 'v1', credentials=creds)

            if form.is_valid():
                new_course = form.save(commit=False)
                # Call the Classroom API
                res = service.courses().create(body=course).execute()
                new_course.instructor = request.user
                new_course.link = res['alternateLink']
                new_course.class_id = res['id']
                new_course.save()
                AuditTrail.objects.create(
                    user=request.user, action=f"Created Course '{new_course.title}'")
                return redirect('classroom:my-courses')
            return render(request, 'app/new_course.html', {"form": form})

        except HttpError as error:
            print(error)
            return HttpResponse(f"Failed to create the course {error}")
            # return render(request, 'app/new_course.html', {"form": form})


class NewTopicView(LoginRequiredMixin, View):
    def get(self, request, id, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        form = TopicForm()
        context = {
            "form": form,
            "course": course
        }
        return render(request, "app/new_topic.html", context)

    def post(self, request, id, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        form = TopicForm(request.POST, request.FILES)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.course = course
            topic.save()
            return redirect('app:course_topics', course.id)
        context = {
            "form": form
        }
        return render(request, "app/new_topic.html", context)


@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    token_path = settings.BASE_DIR / 'lecturer_token.json'
    if not course.instructor == request.user:
        HttpResponseForbidden()

    creds = get_credentials(
        ['https://www.googleapis.com/auth/classroom.courses'], token_path)

    try:
        service = build('classroom', 'v1', credentials=creds)
        service.courses().delete(id=course.class_id).execute()
        course.delete()
        AuditTrail.objects.create(
            user=request.user, action=f"Deleted Course '{course.title}'")
        courses = Course.objects.filter(instructor=request.user)
        return render(request, 'app/partials/classes.html', {"courses": courses})

    except HttpError as error:
        print(f'An error occurred: {error}')
        return HttpResponse("Failed to delete the course ")
    return HttpResponse("You have failed to delete this course")


@login_required
def initiate_payment(request):
    # import json
    user = request.user
    paynow = initialize_paynow()
    # Create a new payment
    order = Order.objects.filter(
        student=user, status='pending').first()
    payment = paynow.create_payment(f'#{order.id}', user.email)
    interbank_rate = InterBankRate.objects.last()
    payment.items = []
    payment.add(
        ', '.join([course.title for course in order.courses.all()]), order.total)
    response = paynow.send(payment)
    if response.success:
        # print("The response is success ")
        # Get the link to redirect the user to, then use it as you see fit
        link = response.redirect_url
        poll_url = response.poll_url
        # print(json.dumps(response.__dict__))

        PollUrl.objects.create(student=request.user, poll_url=poll_url)
        return redirect(link)

    return HttpResponse("Failed to send the payment")


def enroll_student(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user_email = f'{request.user.registration_number}@courses.msu.ac.zw'
    token_path = settings.BASE_DIR / 'lecturer_token.json'
    # course = get_object_or_404(Course, pk=course_id)

    creds = get_credentials(['https://www.googleapis.com/auth/classroom.courses',
                            'https://www.googleapis.com/auth/classroom.coursework.students', 'https://www.googleapis.com/auth/classroom.rosters'], token_path)

    try:
        service = build('classroom', 'v1', credentials=creds)

        course_details = service.courses().get(id=course.class_id).execute()
        # print(f'course details {course_details}')
        enrollment_code = course_details.get('enrollmentCode')
        # print(f'enrollment code {enrollment_code}')
        student = {"userId": user_email}
        # params = {"enrollmentCode": enrollment_code}

        student = service.courses().students().create(
            courseId=course.class_id,
            enrollmentCode=enrollment_code,
            body=student).execute()
        print(f"student is enrolled {student}")
        return redirect(course.link)
    except Exception as e:
        print(f'Error enrolling a student {e}')
        return HttpResponse("Ooops something went wrong, Contact our support")


@login_required
def payment_return(request):
    user = request.user
    url = PollUrl.objects.filter(
        student=request.user, status='created').last()
    if not url:
        return HttpResponseForbidden()
    paynow = initialize_paynow()
    status = paynow.check_transaction_status(url.poll_url)
    # order = Order.objects.filter(student=user, status='pending').first()
    time.sleep(10)
    if status.paid:
        user.registration_number = user.registration_number if user.registration_number else generate_registration_number(
            user.last_name)
        user.save()
        create_google_user(user)
        messages.success(
            request, "Thank You for enrolling, Please wait for 5 minutes while your payments are being processed!")
        return redirect('classroom:my-courses')
        # return render(request, 'app/payment_success.html', {'order': order})
    return HttpResponse("The payment is canceled please try again")


@login_required
def add_to_cart(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    order = Order.objects.filter(
        student=request.user, status='pending').first()
    if not order:
        order = Order.objects.create(student=request.user)
    order.courses.add(course)
    order.save()
    is_ordered = True if course in order.courses.all() else False
    return render(request, 'app/partials/cart.html', {'is_ordered': is_ordered, "course": course})


class OrdersView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        orders = Order.objects.all()
        if not user.is_admin:
            return HttpResponseForbidden()
        status = Order.IsPaidStatus.values

        context = {
            'orders': orders,
            'status': status
        }
        return render(request, 'app/orders.html', context)


class EditTopicView(LoginRequiredMixin, View):
    def get(self, request, id, pk, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        topic = get_object_or_404(Topic, pk=pk)
        if not topic in course.topics.all():
            return HttpResponse("You cant be here ")
        form = TopicForm(instance=topic)
        context = {
            "form": form
        }
        return render(request, "app/new_topic.html", context)

    def post(self, request, id, pk, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        topic = get_object_or_404(Topic, pk=pk)
        form = TopicForm(request.POST, request.FILES, instance=topic)
        if form.is_valid():
            form.save()
            return redirect('app:course_topics', course.id)
        context = {
            "form": form
        }
        return render(request, "app/new_topic.html", context)


class NewLessonView(LoginRequiredMixin, View):
    def get(self, request, id, pk, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        topic = get_object_or_404(Topic, pk=pk)
        form = LessonForm()
        context = {
            "form": form
        }
        return render(request, "app/new_lesson.html", context)

    def post(self, request, id, pk, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        topic = get_object_or_404(Topic, pk=pk)
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.topic = topic
            lesson.course = course
            lesson.save()
            return redirect('app:topic_lessons', course.id, topic.id)
        context = {
            "form": form
        }
        return render(request, "app/new_lesson.html", context)


class EditLessonView(LoginRequiredMixin, View):
    def get(self, request, id, pk, lesson_id, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        topic = get_object_or_404(Topic, pk=pk)
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        if not topic in course.topcs.all() and not lesson in topic.lessons.all():
            return HttpResponse("You can not be here")
        form = LessonForm(instance=lesson)
        context = {
            "form": form
        }
        return render(request, "app/new_lesson.html", context)

    def post(self, request, id, pk, lesson_id, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        topic = get_object_or_404(Topic, pk=pk)
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect('app:topic_lessons')
        context = {
            "form": form,
            "course": course,
            "lesson": lesson,
            "topic": topic
        }
        return render(request, "app/new_lesson.html", context)


class InstructorCourseListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        courses = Course.objects.filter(instructor=request.user)
        context = {
            'courses': courses,
        }
        return render(request, 'app/instructor_courses.html', context)


class CourseTopicListView(View):
    def get(self, request, id, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        context = {
            'course': course,
        }
        return render(request, 'app/course_topics.html', context)


class TopicLessonListView(LoginRequiredMixin, View):
    def get(self, request, id, pk,  *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        topic = get_object_or_404(Topic, pk=pk)
        if not topic in course.topics.all():
            return HttpResponse("No such topic for this course")
        context = {
            'course': course,
            'topic': topic
        }
        return render(request, 'app/topic_lessons.html', context)


class EditCourseView(LoginRequiredMixin, View):
    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Course, pk=course_id)
        # creds = get_user_credentials(request)
        form = CourseForm(instance=course)
        context = {"form": form}
        return render(request, "app/new_course.html", context)

    def post(self, request, course_id, *args, **kwargs):
        token_path = settings.BASE_DIR / 'lecturer_token.json'
        course = get_object_or_404(Course, pk=course_id)
        form = CourseForm(request.POST, request.FILES, instance=course)
        course_name = request.POST['title']
        course_description = request.POST['description']
        data = {
            'name': course_name,
            'descriptionHeading': course_description,
        }
        creds = get_credentials(
            ['https://www.googleapis.com/auth/classroom.courses'], token_path)

        try:
            service = build('classroom', 'v1', credentials=creds)

            if form.is_valid():
                updated_course = service.courses().update(
                    id=course.class_id, body=data).execute()
                form.save()
                AuditTrail.objects.create(
                    user=request.user, action=f"Updated Course '{course.title}'")
                return redirect('classroom:my-courses')
            return HttpResponse("Failed to Update the course")

        except HttpError as error:
            print(error)
            return HttpResponse(f'An error occurred: Failed to Update the course')

        return render(request, 'app/new_course.html', {"form": form})


class NewCategoryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = CategoryForm()
        context = {
            "form": form
        }
        return render(request, "app/new_category.html", context)

    def post(self, request, *args, **kwargs):
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            AuditTrail.objects.create(
                user=request.user, action=f"Created a category '{category.name}'")
            return redirect('app:index')
        context = {
            "form": form
        }
        return render(request, "app/new_category.html", context)


class NewTopicView(LoginRequiredMixin, View):
    def get(self, request, id, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        form = TopicForm()
        context = {
            "form": form,
            "course": course
        }
        return render(request, "app/new_topic.html", context)

    def post(self, request, id, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        form = TopicForm(request.POST, request.FILES)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.course = course
            topic.save()
            return redirect('app:course_topics', course.id)
        context = {
            "form": form
        }
        return render(request, "app/new_topic.html", context)


class OrderDetailView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        order = Order.objects.filter(student=user, status='pending').first()
        if order in [pop.order for pop in ProofOfPayment.objects.all()]:
            order = None
        interbank_rate = InterBankRate.objects.last()
        zwl_price = 0.00
        if order:
            zwl_price = get_zwl_price(interbank_rate.rate, order.total)
        context = {
            "order": order,
            'zwl_price': zwl_price
        }
        return render(request, "app/user_orders.html", context)


def delete_order(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    order = Order.objects.filter(student=user, status='pending').first()
    order.courses.remove(course)
    order.save()

    return render(request, 'app/partials/orders.html', {'order': order})


class CourseDetailView(LoginRequiredMixin, View):
    def get(self, request, id, *args, **kwargs):
        user = request.user
        url = PollUrl.objects.all().last()
        course = get_object_or_404(Course, pk=id)
        user_orders = Order.objects.filter(student=user)
        interbank_rate = InterBankRate.objects.last()
        zwl_price = get_zwl_price(interbank_rate.rate, course.price)
        is_ordered = False
        for order in user_orders:
            if course in order.courses.all():
                is_ordered = True
                break

        is_enrolled = True if Enrollment.objects.filter(
            course=course, student=user) else False
        context = {
            "course": course,
            'is_enrolled': is_enrolled,
            'is_ordered': is_ordered,
            'zwl_price': zwl_price
        }
        return render(request, 'app/course_detail.html', context)


class EnrollStudentsView(LoginRequiredMixin, View):
    def get(self, request, id, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        form = EnrollmentForm()
        context = {
            "course": course,
            "form": form,
        }
        return render(request, 'app/enroll_students.html', context)

    def post(self, request, id, *args, **kwargs):
        course = get_object_or_404(Course, pk=id)
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enroll = form.save(commit=False)
            enroll.course = course
            enroll.save()
            messages.success(request, "The students are enrolled successfully")
            return redirect('')
        context = {
            "course": course,
            "form": form,
        }
        return render(request, 'app/enroll_students.html', context)


def create_google_user(logedin_user):
    token_path = settings.BASE_DIR / 'admin_token.json'
    password = generate_random_password()
    creds = get_credentials(
        ['https://www.googleapis.com/auth/admin.directory.user'], token_path)

    # Create the user resource
    user_resource = {
        'primaryEmail': f"{logedin_user.registration_number}@courses.msu.ac.zw",
        'name': {
            'givenName': logedin_user.first_name,
            'familyName': logedin_user.last_name,
            'fullName': f'{logedin_user.first_name} {logedin_user.last_name}'
        },
        'password': password,
        'changePasswordAtNextLogin': True,
    }

    try:
        service = build('admin', 'directory_v1', credentials=creds)
        # Execute the user creation API request
        user = service.users().insert(body=user_resource).execute()

        # Print information about the created user
        print(
            f"User {user['primaryEmail']} created successfully with ID: {user['id']}")
        body = f"Thank you for enrolling with us, Your new Email {user['primaryEmail']} and your password is {password}"
        subject = "Payment Success: Thank You for Choosing MSU Short Courses!"
        html_message = render_to_string(
            'app/payment_success_email.html', {'password': password, 'email': f'{logedin_user.registration_number}@courses.msu.ac.zw'})
        send_html_email(subject, html_message, [logedin_user.email])
        return user

    except Exception as e:
        # Handle any errors that occur during the user creation
        user = get_user(
            f"{logedin_user.registration_number}@courses.msu.ac.zw")
        subject = "Payment Success: Thank You for Choosing MSU Short Courses!"
        html_message = render_to_string(
            'app/payment_success_email.html')
        send_html_email(subject, html_message, [logedin_user.email])
        # print(f"Error creating user: {e}")
        return user


def get_user(user_email):
    token_path = settings.BASE_DIR / 'admin_token.json'
    creds = get_credentials(
        ['https://www.googleapis.com/auth/admin.directory.user'], token_path)
    # Create a service object for interacting with the Directory API
    service = build('admin', 'directory_v1', credentials=creds)

    try:
        # Call the Directory API to get user details
        user = service.users().get(userKey=user_email).execute()
        return user
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def export_orders_table(request):
    if not request.user.is_admin:
        return HttpResponseForbidden()

    queryset = Order.objects.all()
    resource = OrderTableResource()
    dataset = resource.export(queryset)
    data_format = dataset.csv
    response = HttpResponse(data_format, content_type=f"text/{format}")
    response["Content-Disposition"] = "attachment; filename=orders.csv"
    return response
