import time
import requests
from bs4 import BeautifulSoup
from accounts.models import ProofOfPayment
from app.models import InterBankRate, PollUrl, Order, Transaction, Enrollment
from .utils import initialize_paynow, enroll_student, send_html_email
from django.template.loader import render_to_string
from app.views import create_google_user
from accounts.utils import generate_registration_number


def get_interbank_rate():
    response = requests.get('https://www.rbz.co.zw/', verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    table_rows = soup.find(id="baTab1").find(
        'table').find('tbody').find_all('tr')

    target_row = None
    for row in table_rows:

        if any("USD/ZW" in cell.text for cell in row.find_all('td')):
            target_row = row
            break
        if 'USD/ZW$' in row.text:
            target_row = row
            break
    interbank_rate = target_row.find_all('td')[3].text
    print(f'Current Interbank Rate {interbank_rate}')
    InterBankRate.objects.create(rate=float(interbank_rate))


def check_payment_status():
    urls = PollUrl.objects.filter(status='created')
    paynow = initialize_paynow()
    enrollment_success = True
    for url in urls:
        status = paynow.check_transaction_status(url.poll_url)
        time.sleep(20)
        if status.paid:
            order = Order.objects.filter(
                student=url.student, status='pending').first()
            for course in order.courses.all():
                student = enroll_student(
                    f'{url.student.registration_number}@courses.msu.ac.zw', course)

                if student is None:
                    enrollment_success = False
                    break
                Enrollment.objects.create(course=course, student=url.student)
                subject = f"Congratulations on Enrolling in {course.title} at MSU Short Courses Platform!"
                html_message = render_to_string(
                    'app/enroll_success_email.html', {'course': course, 'order': order})
                send_html_email(subject, html_message, [order.student.email])
            if enrollment_success:
                url.status = 'paid'
                order.status = 'paid'
                order.paynow_reference = status.paynow_reference
                order.save()
                url.save()
                print(f"Order for {order.student.email } is paid successfully")
            else:
                print(f'Failed to enroll the student')
        else:
            url.status = 'disputed'
            url.save()


def enroll_student_from_pop():
    pops = ProofOfPayment.objects.filter(status='Processed')
    for pop in pops:
        enrollment_success = True
        if not pop.user.registration_number:
            pop.user.registration_number = generate_registration_number(
                pop.user.last_name)
            pop.user.save()
        create_google_user(pop.user)
        for course in pop.order.courses.all():
            student = enroll_student(
                f'{pop.order.student.registration_number}@courses.msu.ac.zw', course)

            if student is None:
                enrollment_success = False
                break
            Enrollment.objects.create(course=course, student=pop.order.student)
            subject = f"Congratulations on Enrolling in {course.title} at MSU Short Courses Platform!"
            html_message = render_to_string(
                'app/enroll_success_email.html', {'course': course, 'order': pop.order})
            send_html_email(subject, html_message, [pop.order.student.email])
        if enrollment_success:
            pop.order.status = "paid"
            pop.status = 'Actioned'
            pop.save()
            pop.order.save()
            print(f"Order for {pop.order.student.email } is paid successfully")
        else:
            print(f'Failed to enroll the student')


def post_payments_to_dhanz():
    # print("The post payments is run")
    transactions = [
        transaction.reference for transaction in Transaction.objects.all()]
    orders = [order for order in Order.objects.filter(
        status='Paid') if order.paynow_reference not in transactions and order.paynow_reference]
    # print(orders)

    for order in orders:
        courses = ', '.join([course.title for course in order.courses.all()])
        Transaction.objects.create(
            reference=order.paynow_reference,
            amount=order.total,
            registration_number=order.student.registration_number,
            first_name=order.student.first_name,
            last_name=order.student.last_name,
            description=courses
        )
        print(f"{order} has been posted to dhanz table")
