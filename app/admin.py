from django.contrib import admin
from import_export.fields import Field
from import_export import resources
from simple_history.admin import SimpleHistoryAdmin
from .models import Category, Course, Order, Topic, Lesson, Enrollment, PollUrl, Transaction
# Register your models here.


class OrderTableResource(resources.ModelResource):
    student__first_name = Field(
        attribute='student__first_name', column_name='First Name')
    student__last_name = Field(
        attribute='student__last_name', column_name='Last Name')
    student__email = Field(
        attribute='student__email', column_name='Student Email')
    order_date = Field()
    courses = Field()

    class Meta:
        model = Order
        fields = ('id', 'student__first_name', 'student__last_name', "student__email",
                  "courses", "order_date")
        export_order = ('id', 'student__first_name', 'student__last_name', "student__email",
                        "courses", "order_date")

    def dehydrate_courses(self, obj):
        courses = [x.title for x in obj.courses.all()]
        return ", ".join(courses)

    def dehydrate_order_date(self, obj):
        return obj.order_date.strftime("%d-%m-%Y")


admin.site.register(Category, SimpleHistoryAdmin)
admin.site.register(Course, SimpleHistoryAdmin)
admin.site.register(Order, SimpleHistoryAdmin)
admin.site.register(Topic)
admin.site.register(Lesson)
admin.site.register(Enrollment)
admin.site.register(PollUrl)
admin.site.register(Transaction)
