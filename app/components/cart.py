from typing import List, Optional
from django_unicorn.components import UnicornView, QuerySetType
from django.contrib.auth.models import User
from app.models import Order


class CartView(UnicornView):
    user_courses: QuerySetType[Order] = None
    user_pk: int
    total: float = 0

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.user_pk = kwargs.get("user")
        self.user_courses = Order.objects.filter(student=self.user_pk)
        self.get_total()

    def add_course(self, course_id):
        course, created = Order.objects.get_or_create(
            student_id=self.user_pk, course_id=course_id)
        # print("course added")
        if not created:
            course.delete()
        self.user_courses = Order.objects.filter(student=self.user_pk)
        self.get_total()

    def delete_course(self, course_id):
        course = Order.objects.get(pk=course_id)
        course.delete()
        self.user_courses = self.user_courses.exclude(pk=course_id)
        self.get_total()

    def get_total(self):
        self.total = sum(
            order.course.price for order in self.user_courses
        )
