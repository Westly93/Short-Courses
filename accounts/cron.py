# from django.db.models.functions import month, day
from .models import UserAccount
from app.utils import send_email
from datetime import date
from django.template.loader import render_to_string
from app.utils import send_html_email


def send_birthday_wish():
    current_date = date.today()
    users = UserAccount.objects.filter(
        profile__dob__month=current_date.month, profile__dob__day=current_date.day)
    for user in users:
        subject = f"Happy Birthday, {user.first_name} {user.last_name}! Your Special Day Calls for a Celebration with MSU Short Courses Platform"
        html_message = render_to_string(
            'accounts/birthday_wish_email.html')
        send_html_email(subject, html_message, [user.email])

        print(f'birthday wish send to {user.email}')
