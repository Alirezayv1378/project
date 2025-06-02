import os

import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth.models import User  # noqa:E402


def update_password(username: str, password: str):
    admin = User.objects.get(username=username)
    if not admin.check_password(password):
        admin.set_password(password)
        admin.save()


def init_admin_user():
    super_admin_username = os.getenv("SUPER_ADMIN_USERNAME")
    super_admin_email = os.getenv("SUPER_ADMIN_EMAIL")
    super_admin_password = os.getenv("SUPER_ADMIN_PASSWORD")

    if not User.objects.filter(username=super_admin_username).exists():
        User.objects.create_superuser(super_admin_username, super_admin_email, super_admin_password)
    else:
        update_password(super_admin_username, super_admin_password)


if __name__ == "__main__":
    init_admin_user()
