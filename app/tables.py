from .models import Order
from table import Table
from table.columns import Column


class OrdersTable(Table):
    id = Column(field='id', header='ID')
    first_name = Column(header='First Name')
    last_name = Column(field='student__last_name', header='Last Name')
    email = Column(field='student__email', header='Email')
    courses = Column(header='Courses')

    def render_first_name(self, value):
        return value.first_name

    def render_courses(self, value):
        return ', '.join([course.title for course in value])

    class Meta:
        model = Order
