from django.urls import path
from .views import ClassroomCourseList, EnrollStudentView, MyCourseView
app_name = 'classroom'
urlpatterns = [
    # path('authenticate/', authenticate_with_google, name="authenticate_with_google"),
    # path('create_course/', CreateCourse.as_view(), name="create_course"),
    path('courses/', ClassroomCourseList.as_view(), name="courses"),
    # path('courses/<int:course_id>/enroll', EnrollStudentView.as_view(), name="enroll"),
    path('my-courses/', MyCourseView.as_view(), name="my-courses"),
]
