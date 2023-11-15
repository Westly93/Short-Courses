import os
import random
import decimal
from paynow import Paynow
import string
from django.conf import settings
from django.core.mail import send_mail
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags


def get_credentials(scopes, token_path):

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.BASE_DIR / 'creds.json', scopes)
            creds = flow.run_local_server(port=80)
            # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds


def generate_random_password(length=8):
    # Define characters to include in the password
    characters = string.ascii_letters + string.digits + string.punctuation

    # Generate a random password using the defined characters
    password = ''.join(random.choice(characters) for _ in range(length))

    return password


def send_email(subject, message, recipient_list):
    """
    Send an email using Django's email module.

    """
    from_mail = settings.EMAIL_HOST_USER
    try:
        send_mail(subject, message, from_mail,
                  recipient_list, fail_silently=False)
        return True
    except Exception as e:
        print(str(e))
        return False


def send_html_email(subject, html_message, receipients):
    plain_message = strip_tags(html_message)
    message = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=None,
        to=receipients
    )

    message.attach_alternative(html_message, 'text/html')
    message.send()


def get_zwl_price(interbank_rate, usd_price):
    zwl_price = decimal.Decimal(str(interbank_rate)) * usd_price
    return "{:,.2f}".format(zwl_price)


def graph():
    max_year = GDP.objects.aggregate(max_yr=Max('year'))["max_yr"]
    min_year = GDP.objects.aggregate(min_year=Min("year"))["min_year"]
    years = range(min_year, max_year + 1)
    year = request.GET.get("year", max_year)
    count = int(request.GET.get("count", 10))
    gdps = GDP.objects.filter(year=year).order_by("gdp").reverse()[:count]

    country_names = [d.country for d in gdps]
    country_gdps = [d.gdp for d in gdps]

    cds = ColumnDataSource(
        data=dict(country_names=country_names, country_gdps=country_gdps))
    fig = figure(x_range=country_names, height=500,
                 title=f"Top {count} GDPS ({year})")

    fig.vbar(source=cds, top="country_gdps", x="country_names", width=0.8)
    fig.title.align = "center"
    fig.title.text_font_size = "1.5em"
    fig.xaxis.major_label_orientation = math.pi / 4
    fig.yaxis.formatter = NumeralTickFormatter(format="$0.0a")
    tooltips = [
        ("Country", "@country_names"),
        ("GDP", "@country_gdps{, }")
    ]
    fig.add_tools(HoverTool(tooltips=tooltips))

    script, div = components(fig)


def initialize_paynow():
    # Initializing the paynow
    paynow = Paynow(
        settings.PAYNOW_INTERGRATION_ID,
        settings.PAYNOW_INTERGRATION_KEY,
        "https://learn.msu.ac.zw/paynow/return/",
        "https://learn.msu.ac.zw/paynow/return/"
    )
    return paynow


def enroll_student(user_email, course):
    token_path = settings.BASE_DIR / 'lecturer_token.json'
    # course = get_object_or_404(Course, pk=course_id)
    scopes = [
        'https://www.googleapis.com/auth/classroom.courses',
        'https://www.googleapis.com/auth/classroom.coursework.students',
        'https://www.googleapis.com/auth/classroom.rosters'
    ]
    creds = get_credentials(scopes, token_path)

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
        return student
    except Exception as e:
        print(f'Error enrolling a student {e}')
        return None
