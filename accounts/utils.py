import uuid
from datetime import datetime


def generate_registration_number(last_name):
    current_year = str(datetime.now().year)[-2:]
    random_numbers = str(uuid.uuid4().int)[:5]
    registration_number = f"SC{current_year}{random_numbers}{last_name[0]}"

    return registration_number
