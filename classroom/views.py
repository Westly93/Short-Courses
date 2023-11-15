from django.shortcuts import redirect, render
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from google_auth_oauthlib.flow import Flow
from django.views import View
import google.auth
import os.path
from google.auth import exceptions
from google.auth.transport.requests import Request
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.models import Course, Enrollment
from django.db.models import Count

# Your Google API credentials file
CLIENT_SECRETS_FILE = settings.BASE_DIR / 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/classroom.courses']


def get_user_credentials(request):
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    credentials = None

    # Check if the user has already granted access in a previous session
    if 'credentials' in request.session:
        credentials = Credentials.from_authorized_user_info(
            request.session['credentials'])

    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(request)
        else:
            # Set up the OAuth2 client flow for the live server
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES,
                redirect_uri=request.build_absolute_uri(
                    'accounts:oauth2callback')
            )

            # Generate the authorization URL and redirect the user
            authorization_url, _ = flow.authorization_url(prompt='consent')

            return redirect(authorization_url)

    return credentials


class MyCourseView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_teacher:
            courses = Course.objects.filter(instructor=request.user.id).annotate(
                enrolled=Count('enrollment'))
        else:
            courses = [enrollment.course for enrollment in Enrollment.objects.filter(
                student=request.user)]

        if request.htmx:
            courses = [enrollment.course for enrollment in Enrollment.objects.filter(
                student=request.user)]
            return render(request, 'app/partials/classes.html', {"courses": courses})
        return render(request, 'app/courses.html', {"courses": courses})


""" class StudentView(View):
    def get(self, request, *args, **kwargs):
        credentials= get_user_credentials()
        if not credentials:
            return HttpResponse("Can you please login ")

        try:
            service = build('classroom', 'v1', credentials=credentials)
            courses = service.courses().list().execute().get('courses', [])
            print(len(courses))
            context = {'courses': courses}
            return render(request, 'classroom/students.html', context)

        except HttpError as e:
            return HttpResponse( f'An error occurred: {e}')
 """


class EnrollStudentView(View):
    def get(self, request, course_id, *args, **kwargs):
        credentials = get_user_credentials()

        if not credentials:
            return render(request, 'error.html', {'error_message': 'Failed to obtain user credentials'})

        try:
            service = build('classroom', 'v1', credentials=credentials)

            # Enroll the student in the course
            enrollment_request = {
                'courseId': course_id,
                'enrollmentCode': '120',  # Replace with the actual enrollment code
            }

            enrollment = service.courses().students().create(**enrollment_request).execute()

            # Redirect to a success page or display a success message
            return render(request, 'success.html', {'enrollment': enrollment})

        except HttpError as e:
            # Handle errors, for example, if the enrollment code is invalid
            error_message = f"An error occurred: {e}"
            return HttpResponse(error_message)

        except HttpError as e:
            return HttpResponse(f'An error occurred: {e}')


class ClassroomCourseList(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        SCOPES = ['https://www.googleapis.com/auth/classroom.courses']
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file(
                'new_token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('new_token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('classroom', 'v1', credentials=creds)

            # Call the Classroom API
            results = service.courses().list(pageSize=10).execute()
            courses = results.get('courses', [])

            if not courses:
                print('No courses found.')
                return HttpResponse("You have no courses")
            else:
                # Prints the names of the first 10 courses.
                for course in courses:
                    print(course)
                # print(courses)
                context = {
                    'courses': courses
                }
                return render(request, 'classroom/courses.html', context)

        except HttpError as error:
            print('An error occurred: %s' % error)
            return HttpResponse("An error ocurred while fetching courses")
